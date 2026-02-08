"""
Models for the self-optimizing system
"""

from .config import (
    SystemConfig,
    FailureEntry,
    FailureLog,
    OptimizationAttempt,
)
from .critic_response import CriticResponse
from .version import VersionMetadata, InstructionVersion
from .workflow import (
    WorkflowPlan,
    WorkflowStep,
    WorkflowFailure,
    StepStatus,
    FailureSource,
)
from .tenant import (
    Tenant,
    TenantStatus,
    TenantPlan,
    TenantPlanLimits,
    TenantConfig,
    UsageRecord,
)
from .exceptions import ConfigurationError

__all__ = [
    "SystemConfig",
    "FailureEntry",
    "FailureLog",
    "OptimizationAttempt",
    "CriticResponse",
    "VersionMetadata",
    "InstructionVersion",
    "WorkflowPlan",
    "WorkflowStep",
    "WorkflowFailure",
    "StepStatus",
    "FailureSource",
    "Tenant",
    "TenantStatus",
    "TenantPlan",
    "TenantPlanLimits",
    "TenantConfig",
    "UsageRecord",
    "ConfigurationError",
]
