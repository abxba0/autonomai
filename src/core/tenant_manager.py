"""
Multi-Tenant Isolation - Phase 7 Implementation

Provides tenant-aware data models and isolated instruction spaces.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class TenantConfig:
    """Configuration for a single tenant"""

    tenant_id: str
    tenant_name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True

    # Resource limits
    max_rules: int = 1000
    max_golden_interactions: int = 500
    max_failures: int = 100

    # Feature flags
    enable_semantic_deduplication: bool = True
    enable_judge_model: bool = True
    enable_regression_testing: bool = True
    enable_confidence_throttling: bool = True
    enable_multimodal: bool = False
    enable_knowledge_graph: bool = False

    # Isolation settings
    share_base_rules: bool = False  # Share system-level base rules
    share_golden_dataset: bool = False  # Share golden dataset across tenants

    # Model configuration (can override defaults)
    main_model: Optional[str] = None
    critic_model: Optional[str] = None

    # Storage paths (relative to tenant directory)
    instructions_file: str = "instructions.md"
    golden_dataset_file: str = "golden_dataset.json"
    rule_graph_file: str = "rule_graph.json"
    pending_review_file: str = "pending_review.md"

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "created_at": self.created_at,
            "is_active": self.is_active,
            "max_rules": self.max_rules,
            "max_golden_interactions": self.max_golden_interactions,
            "max_failures": self.max_failures,
            "enable_semantic_deduplication": self.enable_semantic_deduplication,
            "enable_judge_model": self.enable_judge_model,
            "enable_regression_testing": self.enable_regression_testing,
            "enable_confidence_throttling": self.enable_confidence_throttling,
            "enable_multimodal": self.enable_multimodal,
            "enable_knowledge_graph": self.enable_knowledge_graph,
            "share_base_rules": self.share_base_rules,
            "share_golden_dataset": self.share_golden_dataset,
            "main_model": self.main_model,
            "critic_model": self.critic_model,
            "instructions_file": self.instructions_file,
            "golden_dataset_file": self.golden_dataset_file,
            "rule_graph_file": self.rule_graph_file,
            "pending_review_file": self.pending_review_file,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantConfig":
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class TenantContext:
    """Runtime context for tenant operations"""

    tenant_id: str
    config: TenantConfig
    base_path: Path

    # Cached data
    _instructions_cache: Optional[str] = None
    _rules_cache: Optional[List[str]] = None
    _last_updated: Optional[datetime] = None

    def get_instructions_path(self) -> Path:
        """Get the path to tenant's instructions file"""
        return self.base_path / self.tenant_id / self.config.instructions_file

    def get_golden_dataset_path(self) -> Path:
        """Get the path to tenant's golden dataset"""
        return self.base_path / self.tenant_id / self.config.golden_dataset_file

    def get_rule_graph_path(self) -> Path:
        """Get the path to tenant's rule graph"""
        return self.base_path / self.tenant_id / self.config.rule_graph_file

    def get_pending_review_path(self) -> Path:
        """Get the path to tenant's pending review file"""
        return self.base_path / self.tenant_id / self.config.pending_review_file

    def ensure_directory(self):
        """Ensure tenant directory exists"""
        tenant_dir = self.base_path / self.tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir


class TenantManager:
    """Manages multi-tenant isolation and contexts"""

    def __init__(self, base_path: Optional[Path] = None, config=None):
        """
        Initialize the tenant manager

        Args:
            base_path: Base path for all tenant data
            config: SystemConfig instance
        """
        self.base_path = base_path or Path("tenants")
        self.config = config
        self.tenants: Dict[str, TenantConfig] = {}
        self.contexts: Dict[str, TenantContext] = {}

        # Configuration file
        self.config_file = self.base_path / "tenants.json"

        # Load existing tenants
        if self.config_file.exists():
            self.load()
        else:
            # Create default tenant
            self.create_tenant("default", "Default Tenant")

    def create_tenant(self, tenant_id: str, tenant_name: str, **kwargs) -> TenantConfig:
        """
        Create a new tenant

        Args:
            tenant_id: Unique tenant identifier
            tenant_name: Human-readable tenant name
            **kwargs: Additional tenant configuration

        Returns:
            TenantConfig for the created tenant
        """
        if tenant_id in self.tenants:
            raise ValueError(f"Tenant {tenant_id} already exists")

        tenant_config = TenantConfig(
            tenant_id=tenant_id, tenant_name=tenant_name, **kwargs
        )

        self.tenants[tenant_id] = tenant_config

        # Create tenant context
        context = TenantContext(
            tenant_id=tenant_id, config=tenant_config, base_path=self.base_path
        )
        context.ensure_directory()
        self.contexts[tenant_id] = context

        self.save()
        return tenant_config

    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration"""
        return self.tenants.get(tenant_id)

    def get_context(self, tenant_id: str) -> Optional[TenantContext]:
        """Get tenant context"""
        if tenant_id not in self.contexts and tenant_id in self.tenants:
            # Lazy create context
            self.contexts[tenant_id] = TenantContext(
                tenant_id=tenant_id,
                config=self.tenants[tenant_id],
                base_path=self.base_path,
            )
            self.contexts[tenant_id].ensure_directory()

        return self.contexts.get(tenant_id)

    def list_tenants(self, active_only: bool = True) -> List[TenantConfig]:
        """List all tenants"""
        tenants = list(self.tenants.values())
        if active_only:
            tenants = [t for t in tenants if t.is_active]
        return tenants

    def update_tenant(self, tenant_id: str, **updates) -> TenantConfig:
        """
        Update tenant configuration

        Args:
            tenant_id: Tenant to update
            **updates: Configuration updates

        Returns:
            Updated TenantConfig
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Update allowed fields
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        self.save()
        return tenant

    def deactivate_tenant(self, tenant_id: str):
        """Deactivate a tenant (soft delete)"""
        if tenant_id in self.tenants:
            self.tenants[tenant_id].is_active = False
            self.save()

    def activate_tenant(self, tenant_id: str):
        """Reactivate a tenant"""
        if tenant_id in self.tenants:
            self.tenants[tenant_id].is_active = True
            self.save()

    def delete_tenant(self, tenant_id: str, delete_data: bool = False):
        """
        Delete a tenant

        Args:
            tenant_id: Tenant to delete
            delete_data: If True, also delete all tenant data files
        """
        if tenant_id not in self.tenants:
            return

        # Remove from memory
        del self.tenants[tenant_id]
        if tenant_id in self.contexts:
            del self.contexts[tenant_id]

        # Optionally delete data
        if delete_data:
            tenant_dir = self.base_path / tenant_id
            if tenant_dir.exists():
                import shutil

                shutil.rmtree(tenant_dir)

        self.save()

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get statistics for a tenant"""
        context = self.get_context(tenant_id)
        if not context:
            return {}

        stats = {
            "tenant_id": tenant_id,
            "is_active": self.tenants[tenant_id].is_active,
            "created_at": self.tenants[tenant_id].created_at,
            "files_exist": {},
        }

        # Check which files exist
        stats["files_exist"]["instructions"] = context.get_instructions_path().exists()
        stats["files_exist"][
            "golden_dataset"
        ] = context.get_golden_dataset_path().exists()
        stats["files_exist"]["rule_graph"] = context.get_rule_graph_path().exists()
        stats["files_exist"][
            "pending_review"
        ] = context.get_pending_review_path().exists()

        # Get file sizes if they exist
        for file_type, exists in stats["files_exist"].items():
            if exists:
                if file_type == "instructions":
                    path = context.get_instructions_path()
                elif file_type == "golden_dataset":
                    path = context.get_golden_dataset_path()
                elif file_type == "rule_graph":
                    path = context.get_rule_graph_path()
                elif file_type == "pending_review":
                    path = context.get_pending_review_path()

                stats[f"{file_type}_size"] = path.stat().st_size if path.exists() else 0

        return stats

    def save(self):
        """Save tenant configurations"""
        self.base_path.mkdir(parents=True, exist_ok=True)

        data = {
            "tenants": {tid: tc.to_dict() for tid, tc in self.tenants.items()},
            "saved_at": datetime.now().isoformat(),
        }

        with open(self.config_file, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load tenant configurations"""
        if not self.config_file.exists():
            return

        with open(self.config_file, "r") as f:
            data = json.load(f)

        self.tenants = {
            tid: TenantConfig.from_dict(tc_data)
            for tid, tc_data in data.get("tenants", {}).items()
        }


class TenantAwareDataFilter:
    """Helper for filtering data by tenant"""

    @staticmethod
    def filter_rules(rules: List[Any], tenant_id: str) -> List[Any]:
        """Filter rules by tenant"""
        return [r for r in rules if getattr(r, "tenant_id", "default") == tenant_id]

    @staticmethod
    def filter_failures(failures: List[Any], tenant_id: str) -> List[Any]:
        """Filter failures by tenant"""
        return [f for f in failures if getattr(f, "tenant_id", "default") == tenant_id]

    @staticmethod
    def filter_interactions(interactions: List[Any], tenant_id: str) -> List[Any]:
        """Filter golden interactions by tenant"""
        return [
            i for i in interactions if getattr(i, "tenant_id", "default") == tenant_id
        ]
