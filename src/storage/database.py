"""
Database backend for production use
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    JSON,
    Index,
    Float,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

from ..models.config import SystemConfig, FailureEntry
from ..models.version import VersionMetadata, InstructionVersion
from ..models.tenant import (
    Tenant,
    TenantStatus,
    TenantPlan,
    TenantPlanLimits,
    TenantConfig,
    UsageRecord,
)

# Load environment variables
load_dotenv()

# SQLAlchemy base
Base = declarative_base()


class DBFailureEntry(Base):
    """Database model for FailureEntry"""

    __tablename__ = "failure_entries"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    trigger_type = Column(String)
    severity = Column(String)
    failure_description = Column(Text)
    user_feedback = Column(Text, nullable=True)
    last_model_output = Column(Text, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    user_query = Column(Text, nullable=True)
    conversation_context = Column(Text, nullable=True)
    optimization_attempted = Column(Boolean, default=False)
    optimization_successful = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    affected_appendix_rules = Column(JSON, default=list)
    failure_signature = Column(String)
    tenant_id = Column(String, default="default", nullable=False, index=True)


class DBVersionMetadata(Base):
    """Database model for VersionMetadata"""

    __tablename__ = "version_metadata"

    version_id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    trigger_type = Column(String)
    failure_signature = Column(String, nullable=True)
    critic_justification = Column(Text)
    diff_summary = Column(Text)
    rules_added = Column(Integer, default=0)
    rules_modified = Column(Integer, default=0)
    rules_deprecated = Column(Integer, default=0)
    parent_version = Column(String, nullable=True)
    user_approved = Column(Boolean, default=False)
    approval_notes = Column(Text, nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), default="default", nullable=False, index=True)


class DBInstructionVersion(Base):
    """Database model for InstructionVersion"""

    __tablename__ = "instruction_versions"

    version_id = Column(String, primary_key=True)
    base_instructions = Column(Text)
    dynamic_appendix = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), default="default", nullable=False, index=True)


class DBTenant(Base):
    """Database model for Tenant"""

    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="active")
    plan = Column(String, nullable=False, default="free")
    plan_limits = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trial_ends_at = Column(DateTime, nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Contact and billing
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)
    
    # Usage tracking
    current_period_start = Column(DateTime, default=datetime.utcnow)
    current_period_end = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)


class DBTenantConfig(Base):
    """Database model for TenantConfig"""

    __tablename__ = "tenant_configs"

    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), primary_key=True)
    
    # API Keys (encrypted in production)
    anthropic_api_key = Column(String, nullable=True)
    openai_api_key = Column(String, nullable=True)
    google_api_key = Column(String, nullable=True)
    deepseek_api_key = Column(String, nullable=True)
    openrouter_api_key = Column(String, nullable=True)
    
    # Model preferences
    default_main_model = Column(String, default="claude-3-5-sonnet-20241022")
    default_critic_model = Column(String, default="claude-3-haiku-20240307")
    default_main_provider = Column(String, nullable=True)
    default_critic_provider = Column(String, nullable=True)
    
    # Feature flags
    enable_auto_optimization = Column(Boolean, default=True)
    enable_correction_detection = Column(Boolean, default=True)
    enable_judge_model = Column(Boolean, default=False)
    enable_regression_testing = Column(Boolean, default=False)
    enable_multimodal = Column(Boolean, default=False)
    enable_workflow_orchestrator = Column(Boolean, default=True)
    enable_plugin_system = Column(Boolean, default=False)
    
    # Custom validators (serialized)
    custom_validators = Column(JSON, default=list)
    
    # Metadata
    config_version = Column(String, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DBUsageRecord(Base):
    """Database model for UsageRecord"""

    __tablename__ = "usage_records"

    usage_id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Request metrics
    request_count = Column(Integer, default=1)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Token metrics
    tokens_used = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    
    # Cost metrics (in cents)
    estimated_cost_cents = Column(Float, default=0.0)
    
    # Resource usage
    execution_time_ms = Column(Float, default=0.0)
    
    # Categorization
    model_used = Column(String, nullable=True)
    provider_used = Column(String, nullable=True)
    endpoint = Column(String, nullable=True, index=True)
    operation_type = Column(String, nullable=True)
    
    # Period tracking
    period_start = Column(DateTime, default=datetime.utcnow)
    period_end = Column(DateTime, nullable=True)

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_tenant_timestamp", "tenant_id", "timestamp"),
        Index("idx_tenant_period", "tenant_id", "period_start"),
    )


class DatabaseManager:
    """Manages database operations for the self-optimizing system"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database connection"""
        try:
            # Get database URL from environment or use SQLite
            database_url = os.getenv("DATABASE_URL", "sqlite:///./self_optimizing.db")

            # Create engine
            self.engine = create_engine(
                database_url,
                connect_args=(
                    {"check_same_thread": False} if "sqlite" in database_url else {}
                ),
            )

            # Create tables
            Base.metadata.create_all(bind=self.engine)

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            print(f"✓ Database initialized: {database_url}")

        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    # Failure Entry Operations

    def add_failure(self, failure: FailureEntry):
        """Add failure entry to database"""
        with self.get_session() as session:
            db_failure = DBFailureEntry(
                id=failure.id,
                timestamp=datetime.fromisoformat(failure.timestamp),
                trigger_type=failure.trigger_type,
                severity=failure.severity,
                failure_description=failure.failure_description,
                user_feedback=failure.user_feedback,
                last_model_output=failure.last_model_output,
                validation_errors=failure.validation_errors,
                user_query=failure.user_query,
                conversation_context=failure.conversation_context,
                optimization_attempted=failure.optimization_attempted,
                optimization_successful=failure.optimization_successful,
                resolution_notes=failure.resolution_notes,
                affected_appendix_rules=failure.affected_appendix_rules,
                failure_signature=failure.failure_signature,
                tenant_id=getattr(failure, 'tenant_id', 'default'),
            )
            session.add(db_failure)
            session.commit()

    def get_failure(self, failure_id: str, tenant_id: Optional[str] = None) -> Optional[FailureEntry]:
        """Get failure entry by ID, optionally filtered by tenant"""
        with self.get_session() as session:
            query = session.query(DBFailureEntry).filter_by(id=failure_id)
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            db_failure = query.first()
            if db_failure:
                return self._db_failure_to_model(db_failure)
        return None

    def get_recent_failures(self, limit: int = 10, tenant_id: Optional[str] = None) -> List[FailureEntry]:
        """Get recent failure entries, optionally filtered by tenant"""
        with self.get_session() as session:
            query = session.query(DBFailureEntry)
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            db_failures = (
                query
                .order_by(DBFailureEntry.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [self._db_failure_to_model(f) for f in db_failures]

    def count_failures_by_signature(
        self, signature: str, window_hours: int = 24, tenant_id: Optional[str] = None
    ) -> int:
        """Count failures with same signature in time window, optionally filtered by tenant"""
        with self.get_session() as session:
            from datetime import datetime, timedelta

            cutoff = datetime.utcnow() - timedelta(hours=window_hours)
            query = (
                session.query(DBFailureEntry)
                .filter(DBFailureEntry.failure_signature == signature)
                .filter(DBFailureEntry.timestamp >= cutoff)
            )
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            return query.count()

    def get_failures_by_tenant(self, tenant_id: str, limit: Optional[int] = None) -> List[FailureEntry]:
        """Get all failures for a specific tenant"""
        with self.get_session() as session:
            query = session.query(DBFailureEntry).filter_by(tenant_id=tenant_id)
            query = query.order_by(DBFailureEntry.timestamp.desc())
            if limit:
                query = query.limit(limit)
            db_failures = query.all()
            return [self._db_failure_to_model(f) for f in db_failures]

    # Version Operations

    def add_version(self, version: InstructionVersion):
        """Add instruction version to database"""
        with self.get_session() as session:
            # Add metadata
            db_metadata = DBVersionMetadata(
                version_id=version.metadata.version_id,
                timestamp=datetime.fromisoformat(version.metadata.timestamp),
                trigger_type=version.metadata.trigger_type,
                failure_signature=version.metadata.failure_signature,
                critic_justification=version.metadata.critic_justification,
                diff_summary=version.metadata.diff_summary,
                rules_added=version.metadata.rules_added,
                rules_modified=version.metadata.rules_modified,
                rules_deprecated=version.metadata.rules_deprecated,
                parent_version=version.metadata.parent_version,
                user_approved=version.metadata.user_approved,
                approval_notes=version.metadata.approval_notes,
            )
            session.add(db_metadata)

            # Add version content
            db_version = DBInstructionVersion(
                version_id=version.metadata.version_id,
                base_instructions=version.base_instructions,
                dynamic_appendix=version.dynamic_appendix,
            )
            session.add(db_version)

            session.commit()

    def get_version(self, version_id: str) -> Optional[InstructionVersion]:
        """Get instruction version by ID"""
        with self.get_session() as session:
            # Get metadata
            db_metadata = (
                session.query(DBVersionMetadata)
                .filter_by(version_id=version_id)
                .first()
            )

            # Get version content
            db_version = (
                session.query(DBInstructionVersion)
                .filter_by(version_id=version_id)
                .first()
            )

            if db_metadata and db_version:
                metadata = VersionMetadata(
                    trigger_type=db_metadata.trigger_type,
                    critic_justification=db_metadata.critic_justification,
                    diff_summary=db_metadata.diff_summary,
                    version_id=db_metadata.version_id,
                    timestamp=db_metadata.timestamp.isoformat(),
                    failure_signature=db_metadata.failure_signature,
                    rules_added=db_metadata.rules_added,
                    rules_modified=db_metadata.rules_modified,
                    rules_deprecated=db_metadata.rules_deprecated,
                    parent_version=db_metadata.parent_version,
                    user_approved=db_metadata.user_approved,
                    approval_notes=db_metadata.approval_notes,
                )

                return InstructionVersion(
                    metadata=metadata,
                    base_instructions=db_version.base_instructions,
                    dynamic_appendix=db_version.dynamic_appendix,
                )

        return None

    def get_latest_version(self) -> Optional[InstructionVersion]:
        """Get latest instruction version"""
        with self.get_session() as session:
            # Get latest metadata
            db_metadata = (
                session.query(DBVersionMetadata)
                .order_by(DBVersionMetadata.timestamp.desc())
                .first()
            )

            if db_metadata:
                return self.get_version(db_metadata.version_id)

        return None

    def get_version_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get version history"""
        with self.get_session() as session:
            db_metadata_list = (
                session.query(DBVersionMetadata)
                .order_by(DBVersionMetadata.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "version_id": m.version_id,
                    "timestamp": m.timestamp.isoformat(),
                    "trigger_type": m.trigger_type,
                    "diff_summary": m.diff_summary,
                    "rules_added": m.rules_added,
                    "rules_modified": m.rules_modified,
                    "rules_deprecated": m.rules_deprecated,
                }
                for m in db_metadata_list
            ]

    # Utility Methods

    def _db_failure_to_model(self, db_failure: DBFailureEntry) -> FailureEntry:
        """Convert database failure to model"""
        return FailureEntry(
            trigger_type=db_failure.trigger_type,
            failure_description=db_failure.failure_description,
            id=db_failure.id,
            timestamp=db_failure.timestamp.isoformat(),
            severity=db_failure.severity,
            user_feedback=db_failure.user_feedback,
            last_model_output=db_failure.last_model_output,
            validation_errors=db_failure.validation_errors,
            user_query=db_failure.user_query,
            conversation_context=db_failure.conversation_context,
            optimization_attempted=db_failure.optimization_attempted,
            optimization_successful=db_failure.optimization_successful,
            resolution_notes=db_failure.resolution_notes,
            affected_appendix_rules=db_failure.affected_appendix_rules,
            failure_signature=db_failure.failure_signature,
            tenant_id=getattr(db_failure, 'tenant_id', 'default'),
        )

    def cleanup_old_data(self, max_age_days: int = 90, tenant_id: Optional[str] = None):
        """Clean up old data, optionally scoped to a tenant"""
        with self.get_session() as session:
            from datetime import datetime, timedelta

            cutoff = datetime.utcnow() - timedelta(days=max_age_days)

            # Delete old failures (keep metadata for analytics)
            query = session.query(DBFailureEntry).filter(
                DBFailureEntry.timestamp < cutoff
            )
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            query.delete(synchronize_session=False)

            # Keep all versions for now (they're important for rollback)
            # Could implement archival strategy here

            session.commit()

    # Tenant Management Operations

    def create_tenant(self, tenant: Tenant) -> bool:
        """Create a new tenant"""
        try:
            with self.get_session() as session:
                db_tenant = DBTenant(
                    tenant_id=tenant.tenant_id,
                    name=tenant.name,
                    email=tenant.email,
                    status=tenant.status.value,
                    plan=tenant.plan.value,
                    plan_limits=tenant.to_dict()["plan_limits"],
                    created_at=tenant.created_at,
                    updated_at=tenant.updated_at,
                    trial_ends_at=tenant.trial_ends_at,
                    suspended_at=tenant.suspended_at,
                    deleted_at=tenant.deleted_at,
                    company=tenant.company,
                    phone=tenant.phone,
                    billing_email=tenant.billing_email,
                    current_period_start=tenant.current_period_start,
                    current_period_end=tenant.current_period_end,
                    notes=tenant.notes,
                )
                session.add(db_tenant)
                session.commit()
                return True
        except Exception as e:
            print(f"Error creating tenant: {e}")
            return False

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        with self.get_session() as session:
            db_tenant = session.query(DBTenant).filter_by(tenant_id=tenant_id).first()
            if db_tenant:
                return self._db_tenant_to_model(db_tenant)
        return None

    def update_tenant(self, tenant: Tenant) -> bool:
        """Update tenant information"""
        try:
            with self.get_session() as session:
                db_tenant = session.query(DBTenant).filter_by(tenant_id=tenant.tenant_id).first()
                if db_tenant:
                    db_tenant.name = tenant.name
                    db_tenant.email = tenant.email
                    db_tenant.status = tenant.status.value
                    db_tenant.plan = tenant.plan.value
                    db_tenant.plan_limits = tenant.to_dict()["plan_limits"]
                    db_tenant.updated_at = datetime.utcnow()
                    db_tenant.trial_ends_at = tenant.trial_ends_at
                    db_tenant.suspended_at = tenant.suspended_at
                    db_tenant.deleted_at = tenant.deleted_at
                    db_tenant.company = tenant.company
                    db_tenant.phone = tenant.phone
                    db_tenant.billing_email = tenant.billing_email
                    db_tenant.current_period_start = tenant.current_period_start
                    db_tenant.current_period_end = tenant.current_period_end
                    db_tenant.notes = tenant.notes
                    session.commit()
                    return True
        except Exception as e:
            print(f"Error updating tenant: {e}")
        return False

    def list_tenants(self, status: Optional[TenantStatus] = None, limit: int = 100) -> List[Tenant]:
        """List all tenants, optionally filtered by status"""
        with self.get_session() as session:
            query = session.query(DBTenant)
            if status:
                query = query.filter_by(status=status.value)
            db_tenants = query.order_by(DBTenant.created_at.desc()).limit(limit).all()
            return [self._db_tenant_to_model(t) for t in db_tenants]

    def suspend_tenant(self, tenant_id: str) -> bool:
        """Suspend a tenant"""
        try:
            with self.get_session() as session:
                db_tenant = session.query(DBTenant).filter_by(tenant_id=tenant_id).first()
                if db_tenant:
                    db_tenant.status = TenantStatus.SUSPENDED.value
                    db_tenant.suspended_at = datetime.utcnow()
                    db_tenant.updated_at = datetime.utcnow()
                    session.commit()
                    return True
        except Exception as e:
            print(f"Error suspending tenant: {e}")
        return False

    def activate_tenant(self, tenant_id: str) -> bool:
        """Activate a suspended tenant"""
        try:
            with self.get_session() as session:
                db_tenant = session.query(DBTenant).filter_by(tenant_id=tenant_id).first()
                if db_tenant:
                    db_tenant.status = TenantStatus.ACTIVE.value
                    db_tenant.suspended_at = None
                    db_tenant.updated_at = datetime.utcnow()
                    session.commit()
                    return True
        except Exception as e:
            print(f"Error activating tenant: {e}")
        return False

    def delete_tenant(self, tenant_id: str, soft_delete: bool = True) -> bool:
        """Delete or soft-delete a tenant"""
        try:
            with self.get_session() as session:
                db_tenant = session.query(DBTenant).filter_by(tenant_id=tenant_id).first()
                if db_tenant:
                    if soft_delete:
                        db_tenant.status = TenantStatus.DELETED.value
                        db_tenant.deleted_at = datetime.utcnow()
                        db_tenant.updated_at = datetime.utcnow()
                    else:
                        session.delete(db_tenant)
                    session.commit()
                    return True
        except Exception as e:
            print(f"Error deleting tenant: {e}")
        return False

    # Tenant Configuration Operations

    def save_tenant_config(self, config: TenantConfig) -> bool:
        """Save or update tenant configuration"""
        try:
            with self.get_session() as session:
                db_config = session.query(DBTenantConfig).filter_by(tenant_id=config.tenant_id).first()
                
                if db_config:
                    # Update existing
                    db_config.anthropic_api_key = config.anthropic_api_key
                    db_config.openai_api_key = config.openai_api_key
                    db_config.google_api_key = config.google_api_key
                    db_config.deepseek_api_key = config.deepseek_api_key
                    db_config.openrouter_api_key = config.openrouter_api_key
                    db_config.default_main_model = config.default_main_model
                    db_config.default_critic_model = config.default_critic_model
                    db_config.default_main_provider = config.default_main_provider
                    db_config.default_critic_provider = config.default_critic_provider
                    db_config.enable_auto_optimization = config.enable_auto_optimization
                    db_config.enable_correction_detection = config.enable_correction_detection
                    db_config.enable_judge_model = config.enable_judge_model
                    db_config.enable_regression_testing = config.enable_regression_testing
                    db_config.enable_multimodal = config.enable_multimodal
                    db_config.enable_workflow_orchestrator = config.enable_workflow_orchestrator
                    db_config.enable_plugin_system = config.enable_plugin_system
                    db_config.custom_validators = config.custom_validators
                    db_config.config_version = config.config_version
                    db_config.updated_at = datetime.utcnow()
                else:
                    # Create new
                    db_config = DBTenantConfig(
                        tenant_id=config.tenant_id,
                        anthropic_api_key=config.anthropic_api_key,
                        openai_api_key=config.openai_api_key,
                        google_api_key=config.google_api_key,
                        deepseek_api_key=config.deepseek_api_key,
                        openrouter_api_key=config.openrouter_api_key,
                        default_main_model=config.default_main_model,
                        default_critic_model=config.default_critic_model,
                        default_main_provider=config.default_main_provider,
                        default_critic_provider=config.default_critic_provider,
                        enable_auto_optimization=config.enable_auto_optimization,
                        enable_correction_detection=config.enable_correction_detection,
                        enable_judge_model=config.enable_judge_model,
                        enable_regression_testing=config.enable_regression_testing,
                        enable_multimodal=config.enable_multimodal,
                        enable_workflow_orchestrator=config.enable_workflow_orchestrator,
                        enable_plugin_system=config.enable_plugin_system,
                        custom_validators=config.custom_validators,
                        config_version=config.config_version,
                    )
                    session.add(db_config)
                
                session.commit()
                return True
        except Exception as e:
            print(f"Error saving tenant config: {e}")
        return False

    def get_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration"""
        with self.get_session() as session:
            db_config = session.query(DBTenantConfig).filter_by(tenant_id=tenant_id).first()
            if db_config:
                return self._db_config_to_model(db_config)
        return None

    # Usage Tracking Operations

    def record_usage(self, usage: UsageRecord) -> bool:
        """Record usage data"""
        try:
            with self.get_session() as session:
                db_usage = DBUsageRecord(
                    usage_id=usage.usage_id,
                    tenant_id=usage.tenant_id,
                    timestamp=usage.timestamp,
                    request_count=usage.request_count,
                    successful_requests=usage.successful_requests,
                    failed_requests=usage.failed_requests,
                    tokens_used=usage.tokens_used,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    estimated_cost_cents=usage.estimated_cost_cents,
                    execution_time_ms=usage.execution_time_ms,
                    model_used=usage.model_used,
                    provider_used=usage.provider_used,
                    endpoint=usage.endpoint,
                    operation_type=usage.operation_type,
                    period_start=usage.period_start,
                    period_end=usage.period_end,
                )
                session.add(db_usage)
                session.commit()
                return True
        except Exception as e:
            print(f"Error recording usage: {e}")
        return False

    def get_tenant_usage(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[UsageRecord]:
        """Get usage records for a tenant"""
        with self.get_session() as session:
            query = session.query(DBUsageRecord).filter_by(tenant_id=tenant_id)
            
            if start_date:
                query = query.filter(DBUsageRecord.timestamp >= start_date)
            if end_date:
                query = query.filter(DBUsageRecord.timestamp <= end_date)
            
            db_usage = query.order_by(DBUsageRecord.timestamp.desc()).limit(limit).all()
            return [self._db_usage_to_model(u) for u in db_usage]

    def get_usage_summary(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get aggregated usage summary for a tenant"""
        with self.get_session() as session:
            from sqlalchemy import func
            
            query = session.query(
                func.sum(DBUsageRecord.request_count).label("total_requests"),
                func.sum(DBUsageRecord.successful_requests).label("successful_requests"),
                func.sum(DBUsageRecord.failed_requests).label("failed_requests"),
                func.sum(DBUsageRecord.tokens_used).label("total_tokens"),
                func.sum(DBUsageRecord.input_tokens).label("total_input_tokens"),
                func.sum(DBUsageRecord.output_tokens).label("total_output_tokens"),
                func.sum(DBUsageRecord.estimated_cost_cents).label("total_cost_cents"),
                func.avg(DBUsageRecord.execution_time_ms).label("avg_execution_time_ms"),
            ).filter_by(tenant_id=tenant_id)
            
            if start_date:
                query = query.filter(DBUsageRecord.timestamp >= start_date)
            if end_date:
                query = query.filter(DBUsageRecord.timestamp <= end_date)
            
            result = query.first()
            
            return {
                "tenant_id": tenant_id,
                "total_requests": result.total_requests or 0,
                "successful_requests": result.successful_requests or 0,
                "failed_requests": result.failed_requests or 0,
                "total_tokens": result.total_tokens or 0,
                "total_input_tokens": result.total_input_tokens or 0,
                "total_output_tokens": result.total_output_tokens or 0,
                "total_cost_cents": float(result.total_cost_cents or 0),
                "avg_execution_time_ms": float(result.avg_execution_time_ms or 0),
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }

    # Utility Methods for Tenant Models

    def _db_tenant_to_model(self, db_tenant: DBTenant) -> Tenant:
        """Convert database tenant to model"""
        plan_limits_dict = db_tenant.plan_limits
        plan_limits = TenantPlanLimits(**plan_limits_dict) if plan_limits_dict else TenantPlanLimits()
        
        return Tenant(
            tenant_id=db_tenant.tenant_id,
            name=db_tenant.name,
            email=db_tenant.email,
            status=TenantStatus(db_tenant.status),
            plan=TenantPlan(db_tenant.plan),
            plan_limits=plan_limits,
            created_at=db_tenant.created_at,
            updated_at=db_tenant.updated_at,
            trial_ends_at=db_tenant.trial_ends_at,
            suspended_at=db_tenant.suspended_at,
            deleted_at=db_tenant.deleted_at,
            company=db_tenant.company,
            phone=db_tenant.phone,
            billing_email=db_tenant.billing_email,
            current_period_start=db_tenant.current_period_start,
            current_period_end=db_tenant.current_period_end,
            notes=db_tenant.notes,
        )

    def _db_config_to_model(self, db_config: DBTenantConfig) -> TenantConfig:
        """Convert database config to model"""
        return TenantConfig(
            tenant_id=db_config.tenant_id,
            anthropic_api_key=db_config.anthropic_api_key,
            openai_api_key=db_config.openai_api_key,
            google_api_key=db_config.google_api_key,
            deepseek_api_key=db_config.deepseek_api_key,
            openrouter_api_key=db_config.openrouter_api_key,
            default_main_model=db_config.default_main_model,
            default_critic_model=db_config.default_critic_model,
            default_main_provider=db_config.default_main_provider,
            default_critic_provider=db_config.default_critic_provider,
            enable_auto_optimization=db_config.enable_auto_optimization,
            enable_correction_detection=db_config.enable_correction_detection,
            enable_judge_model=db_config.enable_judge_model,
            enable_regression_testing=db_config.enable_regression_testing,
            enable_multimodal=db_config.enable_multimodal,
            enable_workflow_orchestrator=db_config.enable_workflow_orchestrator,
            enable_plugin_system=db_config.enable_plugin_system,
            custom_validators=db_config.custom_validators or [],
            config_version=db_config.config_version,
            created_at=db_config.created_at,
            updated_at=db_config.updated_at,
        )

    def _db_usage_to_model(self, db_usage: DBUsageRecord) -> UsageRecord:
        """Convert database usage to model"""
        return UsageRecord(
            usage_id=db_usage.usage_id,
            tenant_id=db_usage.tenant_id,
            timestamp=db_usage.timestamp,
            request_count=db_usage.request_count,
            successful_requests=db_usage.successful_requests,
            failed_requests=db_usage.failed_requests,
            tokens_used=db_usage.tokens_used,
            input_tokens=db_usage.input_tokens,
            output_tokens=db_usage.output_tokens,
            estimated_cost_cents=db_usage.estimated_cost_cents,
            execution_time_ms=db_usage.execution_time_ms,
            model_used=db_usage.model_used,
            provider_used=db_usage.provider_used,
            endpoint=db_usage.endpoint,
            operation_type=db_usage.operation_type,
            period_start=db_usage.period_start,
            period_end=db_usage.period_end,
        )
