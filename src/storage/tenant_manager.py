"""
Tenant management for multi-tenant support
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import secrets
from pathlib import Path

from ..models.tenant import (
    Tenant,
    TenantStatus,
    TenantPlan,
    TenantPlanLimits,
    TenantConfig,
    UsageRecord,
)
from .database import DatabaseManager


class TenantManager:
    """Manages tenant operations and lifecycle"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_tenant(
        self,
        name: str,
        email: str,
        plan: TenantPlan = TenantPlan.FREE,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        billing_email: Optional[str] = None,
        trial_days: int = 14,
    ) -> Tenant:
        """Create a new tenant"""
        tenant_id = self._generate_tenant_id()
        
        # Determine status based on plan
        status = TenantStatus.TRIAL if plan != TenantPlan.FREE else TenantStatus.ACTIVE
        
        # Set trial end date if applicable
        trial_ends_at = None
        if status == TenantStatus.TRIAL:
            trial_ends_at = datetime.utcnow() + timedelta(days=trial_days)
        
        # Get plan limits
        plan_limits = TenantPlanLimits.get_plan_limits(plan)
        
        # Create tenant
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            email=email,
            status=status,
            plan=plan,
            plan_limits=plan_limits,
            company=company,
            phone=phone,
            billing_email=billing_email or email,
            trial_ends_at=trial_ends_at,
        )
        
        # Save to database
        if self.db.create_tenant(tenant):
            # Initialize default configuration
            self._initialize_tenant_config(tenant_id)
            return tenant
        
        raise Exception(f"Failed to create tenant: {tenant_id}")

    def onboard_tenant(
        self,
        name: str,
        email: str,
        plan: TenantPlan = TenantPlan.FREE,
        api_keys: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Complete tenant onboarding workflow
        
        Returns:
            Dictionary with tenant info and onboarding status
        """
        try:
            # Create tenant
            tenant = self.create_tenant(
                name=name,
                email=email,
                plan=plan,
                **kwargs
            )
            
            # Configure API keys if provided
            if api_keys:
                config = self.db.get_tenant_config(tenant.tenant_id)
                if config:
                    for key, value in api_keys.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                    self.db.save_tenant_config(config)
            
            return {
                "success": True,
                "tenant_id": tenant.tenant_id,
                "tenant": tenant.to_dict(),
                "message": f"Tenant '{name}' onboarded successfully",
                "trial_ends_at": tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to onboard tenant: {str(e)}",
            }

    def suspend_tenant(self, tenant_id: str, reason: Optional[str] = None) -> bool:
        """Suspend a tenant"""
        tenant = self.db.get_tenant(tenant_id)
        if not tenant:
            return False
        
        if self.db.suspend_tenant(tenant_id):
            # Update notes with suspension reason
            if reason:
                tenant.notes = f"Suspended: {reason}\n{tenant.notes or ''}"
                self.db.update_tenant(tenant)
            return True
        return False

    def activate_tenant(self, tenant_id: str) -> bool:
        """Activate a suspended tenant"""
        return self.db.activate_tenant(tenant_id)

    def delete_tenant(self, tenant_id: str, hard_delete: bool = False) -> bool:
        """Delete a tenant (soft delete by default)"""
        return self.db.delete_tenant(tenant_id, soft_delete=not hard_delete)

    def upgrade_plan(self, tenant_id: str, new_plan: TenantPlan) -> bool:
        """Upgrade tenant to a new plan"""
        tenant = self.db.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # Update plan and limits
        tenant.plan = new_plan
        tenant.plan_limits = TenantPlanLimits.get_plan_limits(new_plan)
        tenant.updated_at = datetime.utcnow()
        
        # Update status if moving from trial
        if tenant.status == TenantStatus.TRIAL:
            tenant.status = TenantStatus.ACTIVE
            tenant.trial_ends_at = None
        
        return self.db.update_tenant(tenant)

    def check_tenant_limits(self, tenant_id: str) -> Dict[str, Any]:
        """
        Check if tenant is within their plan limits
        
        Returns:
            Dictionary with limit check results
        """
        tenant = self.db.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        
        if not tenant.can_make_request():
            return {
                "can_proceed": False,
                "reason": f"Tenant status: {tenant.status.value}",
            }
        
        # Get current usage
        period_start = tenant.current_period_start
        period_end = tenant.current_period_end or datetime.utcnow()
        usage_summary = self.db.get_usage_summary(tenant_id, period_start, period_end)
        
        # Check limits
        limits = tenant.plan_limits
        warnings = []
        exceeded = []
        
        # Check request limits
        if usage_summary["total_requests"] >= limits.requests_per_month:
            exceeded.append("monthly_requests")
        elif usage_summary["total_requests"] >= limits.requests_per_month * 0.9:
            warnings.append("monthly_requests")
        
        # Check token limits
        if usage_summary["total_tokens"] >= limits.tokens_per_month:
            exceeded.append("monthly_tokens")
        elif usage_summary["total_tokens"] >= limits.tokens_per_month * 0.9:
            warnings.append("monthly_tokens")
        
        return {
            "can_proceed": len(exceeded) == 0,
            "tenant_id": tenant_id,
            "plan": tenant.plan.value,
            "usage": usage_summary,
            "limits": {
                "requests_per_month": limits.requests_per_month,
                "tokens_per_month": limits.tokens_per_month,
            },
            "warnings": warnings,
            "exceeded": exceeded,
        }

    def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get complete tenant information"""
        tenant = self.db.get_tenant(tenant_id)
        if not tenant:
            return None
        
        config = self.db.get_tenant_config(tenant_id)
        usage_summary = self.db.get_usage_summary(
            tenant_id,
            tenant.current_period_start,
            tenant.current_period_end or datetime.utcnow(),
        )
        
        return {
            "tenant": tenant.to_dict(),
            "config": config.to_dict() if config else None,
            "usage": usage_summary,
        }

    def list_all_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
    ) -> List[Dict[str, Any]]:
        """List all tenants with optional filters"""
        tenants = self.db.list_tenants(status=status)
        
        if plan:
            tenants = [t for t in tenants if t.plan == plan]
        
        return [t.to_dict() for t in tenants]

    def _generate_tenant_id(self) -> str:
        """Generate a unique tenant ID"""
        return f"tenant_{uuid.uuid4().hex[:12]}"

    def _initialize_tenant_config(self, tenant_id: str) -> bool:
        """Initialize default configuration for a tenant"""
        config = TenantConfig(tenant_id=tenant_id)
        return self.db.save_tenant_config(config)

    def create_tenant_directory_structure(self, tenant_id: str, base_path: Path) -> bool:
        """
        Create isolated directory structure for tenant data
        
        Creates:
        - instructions/
        - logs/
        - metrics/
        - temp/
        """
        try:
            tenant_path = base_path / tenant_id
            
            # Create directories
            (tenant_path / "instructions").mkdir(parents=True, exist_ok=True)
            (tenant_path / "instructions" / ".versions").mkdir(exist_ok=True)
            (tenant_path / "logs").mkdir(exist_ok=True)
            (tenant_path / "metrics").mkdir(exist_ok=True)
            (tenant_path / "temp").mkdir(exist_ok=True)
            
            # Create default instruction file
            instructions_file = tenant_path / "instructions" / "instructions.md"
            if not instructions_file.exists():
                instructions_file.write_text(
                    "# AI Assistant Instructions\n\n"
                    "You are a helpful AI assistant.\n\n"
                    "## Core Principles\n"
                    "- Be helpful, harmless, and honest\n"
                    "- Provide accurate and relevant information\n"
                    "- Adapt to user preferences and feedback\n"
                )
            
            return True
        except Exception as e:
            print(f"Error creating tenant directory structure: {e}")
            return False


class UsageTracker:
    """Tracks and records tenant usage"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def record_request(
        self,
        tenant_id: str,
        tokens_used: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True,
        execution_time_ms: float = 0.0,
        model_used: Optional[str] = None,
        provider_used: Optional[str] = None,
        endpoint: Optional[str] = None,
        operation_type: Optional[str] = None,
    ) -> bool:
        """Record a single request's usage"""
        usage_id = f"usage_{uuid.uuid4().hex[:16]}"
        
        # Estimate cost based on tokens and model
        estimated_cost = self._estimate_cost(
            tokens_used, input_tokens, output_tokens, model_used, provider_used
        )
        
        usage = UsageRecord(
            usage_id=usage_id,
            tenant_id=tenant_id,
            request_count=1,
            successful_requests=1 if success else 0,
            failed_requests=0 if success else 1,
            tokens_used=tokens_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_cents=estimated_cost,
            execution_time_ms=execution_time_ms,
            model_used=model_used,
            provider_used=provider_used,
            endpoint=endpoint,
            operation_type=operation_type,
        )
        
        return self.db.record_usage(usage)

    def get_usage_report(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get detailed usage report for a tenant"""
        summary = self.db.get_usage_summary(tenant_id, start_date, end_date)
        recent_usage = self.db.get_tenant_usage(tenant_id, start_date, end_date, limit=100)
        
        return {
            "summary": summary,
            "recent_records": [u.to_dict() for u in recent_usage[:10]],
            "total_records": len(recent_usage),
        }

    def export_usage_for_billing(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Export usage data in billing-ready format"""
        summary = self.db.get_usage_summary(tenant_id, start_date, end_date)
        
        return {
            "tenant_id": tenant_id,
            "billing_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "usage": {
                "total_requests": summary["total_requests"],
                "successful_requests": summary["successful_requests"],
                "failed_requests": summary["failed_requests"],
                "total_tokens": summary["total_tokens"],
                "input_tokens": summary["total_input_tokens"],
                "output_tokens": summary["total_output_tokens"],
            },
            "cost": {
                "total_cents": summary["total_cost_cents"],
                "total_dollars": summary["total_cost_cents"] / 100,
                "currency": "USD",
            },
            "performance": {
                "avg_execution_time_ms": summary["avg_execution_time_ms"],
            },
        }

    def _estimate_cost(
        self,
        tokens_used: int,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str],
        provider: Optional[str],
    ) -> float:
        """
        Estimate cost in cents based on token usage and model
        
        Note: These are rough estimates. Update with actual pricing.
        """
        # Default cost per 1K tokens (in cents)
        cost_per_1k_input = 0.3
        cost_per_1k_output = 1.5
        
        # Adjust based on model (simplified)
        if model:
            if "gpt-4" in model.lower():
                cost_per_1k_input = 3.0
                cost_per_1k_output = 6.0
            elif "claude-3-opus" in model.lower():
                cost_per_1k_input = 1.5
                cost_per_1k_output = 7.5
            elif "claude-3-sonnet" in model.lower():
                cost_per_1k_input = 0.3
                cost_per_1k_output = 1.5
            elif "claude-3-haiku" in model.lower():
                cost_per_1k_input = 0.025
                cost_per_1k_output = 0.125
        
        input_cost = (input_tokens / 1000) * cost_per_1k_input
        output_cost = (output_tokens / 1000) * cost_per_1k_output
        
        return input_cost + output_cost
