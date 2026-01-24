"""
Settings and configuration management for the moderation platform
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings"""

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8080)
    api_workers: int = Field(default=4)

    # DeepSeek Configuration
    deepseek_api_key: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_model: str = Field(default="deepseek-chat")

    # Redis Configuration
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    enable_distributed_state: bool = Field(default=True)

    # Database Configuration
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite:///moderation_platform.db"
        )
    )

    # Caching Configuration
    enable_caching: bool = Field(default=True)
    cache_ttl: int = Field(default=3600)  # 1 hour
    cache_strategy: str = Field(default="ttl")  # ttl, lru, lfu

    # Batch Processing
    batch_size: int = Field(default=100)
    enable_batch_processing: bool = Field(default=True)
    celery_broker_url: str = Field(
        default_factory=lambda: os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    )

    # Moderation Configuration
    auto_approve_confidence: float = Field(default=0.9)
    auto_reject_confidence: float = Field(default=0.3)
    require_review_threshold: float = Field(default=0.6)

    # Security
    jwt_secret_key: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
    )
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # Logging
    log_level: str = Field(default="INFO")
    enable_audit_logging: bool = Field(default=True)

    # GDPR
    enable_gdpr_compliance: bool = Field(default=True)
    data_retention_days: int = Field(default=90)

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    config_dir: Path = Field(default_factory=lambda: Path(__file__).parent)
    instruction_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "instructions")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class TenantConfig(BaseModel):
    """Configuration for a specific tenant"""

    tenant_id: str
    name: str
    moderation_level: str = "moderate"  # lenient, moderate, strict
    auto_approve_threshold: float = 0.9
    auto_reject_threshold: float = 0.3
    require_review_threshold: float = 0.6
    custom_rules: Dict[str, Any] = Field(default_factory=dict)
    enabled_validators: list = Field(
        default_factory=lambda: ["profanity", "hate_speech", "spam", "toxicity"]
    )

    # Feature flags
    allow_competitive_language: bool = False
    block_external_links: bool = False
    require_email_verification: bool = True
    enable_auto_learning: bool = True

    # Rate limiting
    max_requests_per_minute: int = 100
    max_requests_per_day: int = 10000


def load_tenant_configs(config_file: Optional[Path] = None) -> Dict[str, TenantConfig]:
    """Load tenant configurations from YAML file"""

    if config_file is None:
        config_file = Path(__file__).parent / "tenant_configs.yaml"

    if not config_file.exists():
        # Return default configs
        return {
            "default": TenantConfig(
                tenant_id="default",
                name="Default Tenant",
                moderation_level="moderate"
            )
        }

    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)

    configs = {}
    for tenant_id, config_data in data.items():
        config_data['tenant_id'] = tenant_id
        configs[tenant_id] = TenantConfig(**config_data)

    return configs


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
