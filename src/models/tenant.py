"""
Multi-tenant data models and configuration
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum
import json


class TenantStatus(str, Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    PENDING = "pending"
    DELETED = "deleted"


class TenantPlan(str, Enum):
    """Tenant subscription plans"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


# Constants
COMPLIANCE_RETENTION_DAYS = 365 * 7  # 7 years for compliance (approximately 2555 days)


@dataclass
class TenantPlanLimits:
    """Plan-based limits for tenants"""
    
    # Request limits
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    requests_per_day: int = 1000
    requests_per_month: int = 10000
    
    # Token limits
    tokens_per_request: int = 4000
    tokens_per_day: int = 100000
    tokens_per_month: int = 1000000
    
    # Storage limits
    max_instruction_versions: int = 50
    max_failure_logs: int = 100
    max_storage_mb: int = 100
    
    # Feature limits
    max_users: int = 1
    max_api_keys: int = 1
    enable_advanced_optimization: bool = False
    enable_multimodal: bool = False
    enable_workflow_orchestrator: bool = False
    enable_plugin_system: bool = False
    
    # Data retention
    failure_log_retention_days: int = 30
    audit_log_retention_days: int = 90
    
    @classmethod
    def get_plan_limits(cls, plan: TenantPlan) -> "TenantPlanLimits":
        """Get default limits for a plan"""
        limits_map = {
            TenantPlan.FREE: cls(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                requests_per_month=10000,
                tokens_per_request=2000,
                tokens_per_day=50000,
                tokens_per_month=500000,
                max_instruction_versions=10,
                max_failure_logs=50,
                max_storage_mb=50,
                max_users=1,
                max_api_keys=1,
                enable_advanced_optimization=False,
                enable_multimodal=False,
                enable_workflow_orchestrator=False,
                enable_plugin_system=False,
                failure_log_retention_days=7,
                audit_log_retention_days=30,
            ),
            TenantPlan.STARTER: cls(
                requests_per_minute=30,
                requests_per_hour=500,
                requests_per_day=5000,
                requests_per_month=100000,
                tokens_per_request=4000,
                tokens_per_day=200000,
                tokens_per_month=3000000,
                max_instruction_versions=50,
                max_failure_logs=100,
                max_storage_mb=100,
                max_users=3,
                max_api_keys=3,
                enable_advanced_optimization=True,
                enable_multimodal=False,
                enable_workflow_orchestrator=True,
                enable_plugin_system=False,
                failure_log_retention_days=30,
                audit_log_retention_days=90,
            ),
            TenantPlan.PROFESSIONAL: cls(
                requests_per_minute=100,
                requests_per_hour=2000,
                requests_per_day=20000,
                requests_per_month=500000,
                tokens_per_request=8000,
                tokens_per_day=1000000,
                tokens_per_month=15000000,
                max_instruction_versions=200,
                max_failure_logs=500,
                max_storage_mb=500,
                max_users=10,
                max_api_keys=10,
                enable_advanced_optimization=True,
                enable_multimodal=True,
                enable_workflow_orchestrator=True,
                enable_plugin_system=True,
                failure_log_retention_days=90,
                audit_log_retention_days=365,
            ),
            TenantPlan.ENTERPRISE: cls(
                requests_per_minute=500,
                requests_per_hour=10000,
                requests_per_day=100000,
                requests_per_month=2000000,
                tokens_per_request=16000,
                tokens_per_day=5000000,
                tokens_per_month=100000000,
                max_instruction_versions=1000,
                max_failure_logs=2000,
                max_storage_mb=5000,
                max_users=50,
                max_api_keys=50,
                enable_advanced_optimization=True,
                enable_multimodal=True,
                enable_workflow_orchestrator=True,
                enable_plugin_system=True,
                failure_log_retention_days=365,
                audit_log_retention_days=COMPLIANCE_RETENTION_DAYS,
            ),
        }
        return limits_map.get(plan, cls())


@dataclass
class TenantConfig:
    """Tenant-specific configuration"""
    
    tenant_id: str
    
    # API Keys and Secrets (encrypted in production)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    
    # Model preferences
    default_main_model: str = "claude-3-5-sonnet-20241022"
    default_critic_model: str = "claude-3-haiku-20240307"
    default_main_provider: Optional[str] = None
    default_critic_provider: Optional[str] = None
    
    # Feature flags
    enable_auto_optimization: bool = True
    enable_correction_detection: bool = True
    enable_judge_model: bool = False
    enable_regression_testing: bool = False
    enable_multimodal: bool = False
    enable_workflow_orchestrator: bool = True
    enable_plugin_system: bool = False
    
    # Custom validators (serialized)
    custom_validators: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    config_version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "anthropic_api_key": self.anthropic_api_key,
            "openai_api_key": self.openai_api_key,
            "google_api_key": self.google_api_key,
            "deepseek_api_key": self.deepseek_api_key,
            "openrouter_api_key": self.openrouter_api_key,
            "default_main_model": self.default_main_model,
            "default_critic_model": self.default_critic_model,
            "default_main_provider": self.default_main_provider,
            "default_critic_provider": self.default_critic_provider,
            "enable_auto_optimization": self.enable_auto_optimization,
            "enable_correction_detection": self.enable_correction_detection,
            "enable_judge_model": self.enable_judge_model,
            "enable_regression_testing": self.enable_regression_testing,
            "enable_multimodal": self.enable_multimodal,
            "enable_workflow_orchestrator": self.enable_workflow_orchestrator,
            "enable_plugin_system": self.enable_plugin_system,
            "custom_validators": self.custom_validators,
            "config_version": self.config_version,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantConfig":
        """Create from dictionary"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            tenant_id=data["tenant_id"],
            anthropic_api_key=data.get("anthropic_api_key"),
            openai_api_key=data.get("openai_api_key"),
            google_api_key=data.get("google_api_key"),
            deepseek_api_key=data.get("deepseek_api_key"),
            openrouter_api_key=data.get("openrouter_api_key"),
            default_main_model=data.get("default_main_model", "claude-3-5-sonnet-20241022"),
            default_critic_model=data.get("default_critic_model", "claude-3-haiku-20240307"),
            default_main_provider=data.get("default_main_provider"),
            default_critic_provider=data.get("default_critic_provider"),
            enable_auto_optimization=data.get("enable_auto_optimization", True),
            enable_correction_detection=data.get("enable_correction_detection", True),
            enable_judge_model=data.get("enable_judge_model", False),
            enable_regression_testing=data.get("enable_regression_testing", False),
            enable_multimodal=data.get("enable_multimodal", False),
            enable_workflow_orchestrator=data.get("enable_workflow_orchestrator", True),
            enable_plugin_system=data.get("enable_plugin_system", False),
            custom_validators=data.get("custom_validators", []),
            config_version=data.get("config_version", "1.0"),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
        )


@dataclass
class Tenant:
    """Tenant model"""
    
    tenant_id: str
    name: str
    email: str
    status: TenantStatus = TenantStatus.ACTIVE
    plan: TenantPlan = TenantPlan.FREE
    plan_limits: TenantPlanLimits = field(default_factory=TenantPlanLimits)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    trial_ends_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    # Contact and billing
    company: Optional[str] = None
    phone: Optional[str] = None
    billing_email: Optional[str] = None
    
    # Usage tracking
    current_period_start: datetime = field(default_factory=datetime.utcnow)
    current_period_end: Optional[datetime] = None
    
    # Notes
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Initialize plan limits if not provided"""
        if not self.plan_limits or self.plan_limits == TenantPlanLimits():
            self.plan_limits = TenantPlanLimits.get_plan_limits(self.plan)
    
    def is_active(self) -> bool:
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE
    
    def is_trial(self) -> bool:
        """Check if tenant is in trial"""
        return self.status == TenantStatus.TRIAL
    
    def is_suspended(self) -> bool:
        """Check if tenant is suspended"""
        return self.status == TenantStatus.SUSPENDED
    
    def can_make_request(self) -> bool:
        """Check if tenant can make requests"""
        return self.status in [TenantStatus.ACTIVE, TenantStatus.TRIAL]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "email": self.email,
            "status": self.status.value,
            "plan": self.plan.value,
            "plan_limits": {
                "requests_per_minute": self.plan_limits.requests_per_minute,
                "requests_per_hour": self.plan_limits.requests_per_hour,
                "requests_per_day": self.plan_limits.requests_per_day,
                "requests_per_month": self.plan_limits.requests_per_month,
                "tokens_per_request": self.plan_limits.tokens_per_request,
                "tokens_per_day": self.plan_limits.tokens_per_day,
                "tokens_per_month": self.plan_limits.tokens_per_month,
                "max_instruction_versions": self.plan_limits.max_instruction_versions,
                "max_failure_logs": self.plan_limits.max_failure_logs,
                "max_storage_mb": self.plan_limits.max_storage_mb,
                "max_users": self.plan_limits.max_users,
                "max_api_keys": self.plan_limits.max_api_keys,
                "enable_advanced_optimization": self.plan_limits.enable_advanced_optimization,
                "enable_multimodal": self.plan_limits.enable_multimodal,
                "enable_workflow_orchestrator": self.plan_limits.enable_workflow_orchestrator,
                "enable_plugin_system": self.plan_limits.enable_plugin_system,
                "failure_log_retention_days": self.plan_limits.failure_log_retention_days,
                "audit_log_retention_days": self.plan_limits.audit_log_retention_days,
            },
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "suspended_at": self.suspended_at.isoformat() if self.suspended_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "company": self.company,
            "phone": self.phone,
            "billing_email": self.billing_email,
            "current_period_start": self.current_period_start.isoformat() if isinstance(self.current_period_start, datetime) else self.current_period_start,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "notes": self.notes,
        }


@dataclass
class UsageRecord:
    """Usage tracking record"""
    
    usage_id: str
    tenant_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Request metrics
    request_count: int = 1
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Token metrics
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    
    # Cost metrics (in cents)
    estimated_cost_cents: float = 0.0
    
    # Resource usage
    execution_time_ms: float = 0.0
    
    # Categorization
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    endpoint: Optional[str] = None
    operation_type: Optional[str] = None
    
    # Period tracking
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "usage_id": self.usage_id,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "request_count": self.request_count,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "tokens_used": self.tokens_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_cents": self.estimated_cost_cents,
            "execution_time_ms": self.execution_time_ms,
            "model_used": self.model_used,
            "provider_used": self.provider_used,
            "endpoint": self.endpoint,
            "operation_type": self.operation_type,
            "period_start": self.period_start.isoformat() if isinstance(self.period_start, datetime) else self.period_start,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }
