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
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

from ..models.config import SystemConfig
from ..models.failure import FailureEntry
from ..models.version import VersionMetadata, InstructionVersion

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


class DBInstructionVersion(Base):
    """Database model for InstructionVersion"""

    __tablename__ = "instruction_versions"

    version_id = Column(String, primary_key=True)
    base_instructions = Column(Text)
    dynamic_appendix = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


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
                connect_args={"check_same_thread": False}
                if "sqlite" in database_url
                else {},
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
            )
            session.add(db_failure)
            session.commit()

    def get_failure(self, failure_id: str) -> Optional[FailureEntry]:
        """Get failure entry by ID"""
        with self.get_session() as session:
            db_failure = session.query(DBFailureEntry).filter_by(id=failure_id).first()
            if db_failure:
                return self._db_failure_to_model(db_failure)
        return None

    def get_recent_failures(self, limit: int = 10) -> List[FailureEntry]:
        """Get recent failure entries"""
        with self.get_session() as session:
            db_failures = (
                session.query(DBFailureEntry)
                .order_by(DBFailureEntry.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [self._db_failure_to_model(f) for f in db_failures]

    def count_failures_by_signature(
        self, signature: str, window_hours: int = 24
    ) -> int:
        """Count failures with same signature in time window"""
        with self.get_session() as session:
            from datetime import datetime, timedelta

            cutoff = datetime.utcnow() - timedelta(hours=window_hours)
            return (
                session.query(DBFailureEntry)
                .filter(DBFailureEntry.failure_signature == signature)
                .filter(DBFailureEntry.timestamp >= cutoff)
                .count()
            )

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
        )

    def cleanup_old_data(self, max_age_days: int = 90):
        """Clean up old data"""
        with self.get_session() as session:
            from datetime import datetime, timedelta

            cutoff = datetime.utcnow() - timedelta(days=max_age_days)

            # Delete old failures (keep metadata for analytics)
            session.query(DBFailureEntry).filter(
                DBFailureEntry.timestamp < cutoff
            ).delete(synchronize_session=False)

            # Keep all versions for now (they're important for rollback)
            # Could implement archival strategy here

            session.commit()
