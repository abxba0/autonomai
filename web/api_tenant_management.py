"""
Tenant Management API for Multi-Tenant Support
Provides admin endpoints for managing tenants, onboarding, usage tracking, etc.
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.tenant import (
    Tenant,
    TenantStatus,
    TenantPlan,
    TenantPlanLimits,
    TenantConfig,
    UsageRecord,
)
from src.storage import DatabaseManager, TenantManager, UsageTracker
from src.models.config import SystemConfig
from src.security import (
    User,
    Role,
    Permission,
    verify_token,
    TokenData,
    SecurityValidator,
    log_security_event,
    AuditEventType,
    AuditSeverity,
)

# Initialize database and managers
system_config = SystemConfig()
db_manager = DatabaseManager(system_config)
tenant_manager = TenantManager(db_manager)
usage_tracker = UsageTracker(db_manager)

# FastAPI app
app = FastAPI(
    title="Tenant Management API",
    description="Multi-tenant administration and management API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Pydantic Models for API
class TenantCreate(BaseModel):
    """Request model for creating a tenant"""
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    plan: TenantPlan = TenantPlan.FREE
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_email: Optional[str] = None
    trial_days: int = Field(14, ge=0, le=90)


class TenantUpdate(BaseModel):
    """Request model for updating a tenant"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_email: Optional[str] = None
    notes: Optional[str] = None


class TenantOnboard(BaseModel):
    """Request model for tenant onboarding"""
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    plan: TenantPlan = TenantPlan.FREE
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_email: Optional[str] = None
    
    # API Keys (optional during onboarding)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None


class TenantConfigUpdate(BaseModel):
    """Request model for updating tenant configuration"""
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    default_main_model: Optional[str] = None
    default_critic_model: Optional[str] = None
    enable_auto_optimization: Optional[bool] = None
    enable_correction_detection: Optional[bool] = None
    enable_multimodal: Optional[bool] = None
    enable_workflow_orchestrator: Optional[bool] = None


class PlanUpgrade(BaseModel):
    """Request model for upgrading tenant plan"""
    new_plan: TenantPlan


class UsageQuery(BaseModel):
    """Request model for querying usage"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Authentication dependency
async def require_admin(credentials: HTTPBearer = Depends(security)) -> TokenData:
    """Require admin role for access"""
    token = credentials.credentials
    token_data = verify_token(token)
    
    if not token_data.role or token_data.role != Role.ADMIN:
        log_security_event(
            AuditEventType.PERMISSION_DENIED,
            AuditSeverity.WARNING,
            user_id=token_data.user_id,
            username=token_data.username,
            details={"required_role": "admin", "user_role": token_data.role},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return token_data


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tenant_management"}


# Tenant CRUD Operations
@app.post("/tenants", response_model=Dict[str, Any])
async def create_tenant(
    tenant_data: TenantCreate,
    admin: TokenData = Depends(require_admin),
):
    """Create a new tenant"""
    try:
        tenant = tenant_manager.create_tenant(
            name=tenant_data.name,
            email=tenant_data.email,
            plan=tenant_data.plan,
            company=tenant_data.company,
            phone=tenant_data.phone,
            billing_email=tenant_data.billing_email,
            trial_days=tenant_data.trial_days,
        )
        
        log_security_event(
            AuditEventType.USER_CREATED,
            AuditSeverity.INFO,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": tenant.tenant_id, "tenant_name": tenant.name},
        )
        
        return {
            "success": True,
            "tenant": tenant.to_dict(),
            "message": f"Tenant '{tenant.name}' created successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}",
        )


@app.post("/tenants/onboard", response_model=Dict[str, Any])
async def onboard_tenant(
    onboard_data: TenantOnboard,
    admin: TokenData = Depends(require_admin),
):
    """Complete tenant onboarding workflow"""
    api_keys = {}
    if onboard_data.anthropic_api_key:
        api_keys["anthropic_api_key"] = onboard_data.anthropic_api_key
    if onboard_data.openai_api_key:
        api_keys["openai_api_key"] = onboard_data.openai_api_key
    if onboard_data.google_api_key:
        api_keys["google_api_key"] = onboard_data.google_api_key
    if onboard_data.deepseek_api_key:
        api_keys["deepseek_api_key"] = onboard_data.deepseek_api_key
    if onboard_data.openrouter_api_key:
        api_keys["openrouter_api_key"] = onboard_data.openrouter_api_key
    
    result = tenant_manager.onboard_tenant(
        name=onboard_data.name,
        email=onboard_data.email,
        plan=onboard_data.plan,
        api_keys=api_keys if api_keys else None,
        company=onboard_data.company,
        phone=onboard_data.phone,
        billing_email=onboard_data.billing_email,
    )
    
    if result["success"]:
        log_security_event(
            AuditEventType.USER_CREATED,
            AuditSeverity.INFO,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": result["tenant_id"], "action": "onboard"},
        )
    
    return result


@app.get("/tenants/{tenant_id}", response_model=Dict[str, Any])
async def get_tenant(
    tenant_id: str,
    admin: TokenData = Depends(require_admin),
):
    """Get tenant information"""
    info = tenant_manager.get_tenant_info(tenant_id)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found",
        )
    
    return info


@app.get("/tenants", response_model=List[Dict[str, Any]])
async def list_tenants(
    status_filter: Optional[str] = Query(None, alias="status"),
    plan_filter: Optional[str] = Query(None, alias="plan"),
    admin: TokenData = Depends(require_admin),
):
    """List all tenants"""
    status_enum = TenantStatus(status_filter) if status_filter else None
    plan_enum = TenantPlan(plan_filter) if plan_filter else None
    
    tenants = tenant_manager.list_all_tenants(status=status_enum, plan=plan_enum)
    return tenants


@app.put("/tenants/{tenant_id}", response_model=Dict[str, Any])
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdate,
    admin: TokenData = Depends(require_admin),
):
    """Update tenant information"""
    tenant = db_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found",
        )
    
    # Update fields
    if update_data.name:
        tenant.name = update_data.name
    if update_data.email:
        tenant.email = update_data.email
    if update_data.company is not None:
        tenant.company = update_data.company
    if update_data.phone is not None:
        tenant.phone = update_data.phone
    if update_data.billing_email is not None:
        tenant.billing_email = update_data.billing_email
    if update_data.notes is not None:
        tenant.notes = update_data.notes
    
    tenant.updated_at = datetime.utcnow()
    
    if db_manager.update_tenant(tenant):
        log_security_event(
            AuditEventType.USER_UPDATED,
            AuditSeverity.INFO,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": tenant_id},
        )
        
        return {
            "success": True,
            "tenant": tenant.to_dict(),
            "message": "Tenant updated successfully",
        }
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to update tenant",
    )


@app.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: Optional[str] = None,
    admin: TokenData = Depends(require_admin),
):
    """Suspend a tenant"""
    if tenant_manager.suspend_tenant(tenant_id, reason):
        log_security_event(
            AuditEventType.USER_UPDATED,
            AuditSeverity.WARNING,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": tenant_id, "action": "suspend", "reason": reason},
        )
        
        return {
            "success": True,
            "message": f"Tenant '{tenant_id}' suspended",
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tenant '{tenant_id}' not found",
    )


@app.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    admin: TokenData = Depends(require_admin),
):
    """Activate a suspended tenant"""
    if tenant_manager.activate_tenant(tenant_id):
        log_security_event(
            AuditEventType.USER_UPDATED,
            AuditSeverity.INFO,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": tenant_id, "action": "activate"},
        )
        
        return {
            "success": True,
            "message": f"Tenant '{tenant_id}' activated",
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tenant '{tenant_id}' not found",
    )


@app.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    hard_delete: bool = False,
    admin: TokenData = Depends(require_admin),
):
    """Delete a tenant (soft delete by default)"""
    if tenant_manager.delete_tenant(tenant_id, hard_delete):
        log_security_event(
            AuditEventType.USER_DELETED,
            AuditSeverity.WARNING,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": tenant_id, "hard_delete": hard_delete},
        )
        
        return {
            "success": True,
            "message": f"Tenant '{tenant_id}' {'permanently deleted' if hard_delete else 'soft deleted'}",
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tenant '{tenant_id}' not found",
    )


# Tenant Configuration
@app.get("/tenants/{tenant_id}/config")
async def get_tenant_config(
    tenant_id: str,
    admin: TokenData = Depends(require_admin),
):
    """Get tenant configuration (API keys masked)"""
    config = db_manager.get_tenant_config(tenant_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for tenant '{tenant_id}' not found",
        )
    
    # Mask API keys in response
    config_dict = config.to_dict()
    for key in ["anthropic_api_key", "openai_api_key", "google_api_key", "deepseek_api_key", "openrouter_api_key"]:
        if config_dict.get(key):
            config_dict[key] = "***" + config_dict[key][-4:] if len(config_dict[key]) > 4 else "****"
    
    return config_dict


@app.put("/tenants/{tenant_id}/config")
async def update_tenant_config(
    tenant_id: str,
    config_update: TenantConfigUpdate,
    admin: TokenData = Depends(require_admin),
):
    """Update tenant configuration"""
    config = db_manager.get_tenant_config(tenant_id)
    if not config:
        # Create new config
        config = TenantConfig(tenant_id=tenant_id)
    
    # Update fields
    for field, value in config_update.dict(exclude_unset=True).items():
        if hasattr(config, field) and value is not None:
            setattr(config, field, value)
    
    config.updated_at = datetime.utcnow()
    
    if db_manager.save_tenant_config(config):
        log_security_event(
            AuditEventType.CONFIGURATION_CHANGED,
            AuditSeverity.INFO,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": tenant_id},
        )
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
        }
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to update configuration",
    )


# Plan Management
@app.post("/tenants/{tenant_id}/upgrade")
async def upgrade_tenant_plan(
    tenant_id: str,
    upgrade: PlanUpgrade,
    admin: TokenData = Depends(require_admin),
):
    """Upgrade tenant to a new plan"""
    if tenant_manager.upgrade_plan(tenant_id, upgrade.new_plan):
        log_security_event(
            AuditEventType.USER_UPDATED,
            AuditSeverity.INFO,
            user_id=admin.user_id,
            username=admin.username,
            details={"tenant_id": tenant_id, "new_plan": upgrade.new_plan.value},
        )
        
        return {
            "success": True,
            "message": f"Tenant upgraded to {upgrade.new_plan.value} plan",
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Tenant '{tenant_id}' not found",
    )


# Usage Tracking
@app.get("/tenants/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: TokenData = Depends(require_admin),
):
    """Get tenant usage report"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    report = usage_tracker.get_usage_report(tenant_id, start, end)
    return report


@app.get("/tenants/{tenant_id}/usage/summary")
async def get_usage_summary(
    tenant_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: TokenData = Depends(require_admin),
):
    """Get aggregated usage summary"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    summary = db_manager.get_usage_summary(tenant_id, start, end)
    return summary


@app.get("/tenants/{tenant_id}/usage/billing")
async def export_usage_for_billing(
    tenant_id: str,
    start_date: str,
    end_date: str,
    admin: TokenData = Depends(require_admin),
):
    """Export usage in billing-ready format"""
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    billing_data = usage_tracker.export_usage_for_billing(tenant_id, start, end)
    return billing_data


@app.get("/tenants/{tenant_id}/limits")
async def check_tenant_limits(
    tenant_id: str,
    admin: TokenData = Depends(require_admin),
):
    """Check if tenant is within their limits"""
    limits_check = tenant_manager.check_tenant_limits(tenant_id)
    return limits_check


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
