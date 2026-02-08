"""
Integration tests for GDPR database compliance.

Tests the full database integration for:
- Subject Access Requests (Article 15)
- Right to Erasure (Article 17)
- Right to Rectification (Article 16)
- Consent management persistence
- Audit trail integrity
- Data retention and cleanup
"""

import os
import pytest
import uuid
import tempfile
from datetime import datetime, timedelta

# Skip if sqlalchemy not installed
pytest.importorskip("sqlalchemy")

from src.models.config import SystemConfig
from src.storage.database import DatabaseManager
from src.security.audit import AuditLogger
from src.security.gdpr import (
    GDPRCompliance,
    ConsentPurpose,
    ConsentRecord,
    DataExportFormat,
    DataAccessRequest,
    DataDeletionRequest,
    GDPR_REQUEST_RETENTION_DAYS,
)


@pytest.fixture
def db_manager():
    """Create a DatabaseManager with in-memory SQLite for testing."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    config = SystemConfig()
    manager = DatabaseManager(config)
    yield manager


@pytest.fixture
def audit_logger(tmp_path):
    """Create an AuditLogger with a temporary database for testing."""
    db_file = str(tmp_path / "test_audit.db")
    logger = AuditLogger(database_file=db_file, enable_console=False)
    return logger


@pytest.fixture
def gdpr(db_manager, audit_logger):
    """Create a GDPRCompliance instance with database and audit logger."""
    return GDPRCompliance(database_manager=db_manager, audit_logger=audit_logger)


@pytest.fixture
def user_id():
    """Generate a unique user ID for each test."""
    return f"test_user_{uuid.uuid4().hex[:8]}"


class TestConsentDatabaseIntegration:
    """Test consent management with database persistence."""

    def test_grant_consent_persists_to_db(self, gdpr, user_id):
        """Granting consent should persist the record to the database."""
        consent = gdpr.grant_consent(
            user_id=user_id,
            purpose=ConsentPurpose.SERVICE_PROVISION,
            version="2.0",
            method="api",
        )

        assert consent.granted is True
        assert consent.purpose == ConsentPurpose.SERVICE_PROVISION

        # Verify it's in the database
        records = gdpr.db.get_consent_records(user_id)
        assert len(records) == 1
        assert records[0]["purpose"] == "service_provision"
        assert records[0]["granted"] is True
        assert records[0]["version"] == "2.0"

    def test_withdraw_consent_persists_to_db(self, gdpr, user_id):
        """Withdrawing consent should persist a new record to the database."""
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.ANALYTICS)
        gdpr.withdraw_consent(user_id=user_id, purpose=ConsentPurpose.ANALYTICS)

        records = gdpr.db.get_consent_records(user_id)
        assert len(records) == 2
        # The second record should be the withdrawal
        assert records[1]["granted"] is False

    def test_check_consent_reads_from_db(self, gdpr, user_id):
        """check_consent should query the database for the latest state."""
        assert gdpr.check_consent(user_id, ConsentPurpose.MARKETING) is False

        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.MARKETING)
        assert gdpr.check_consent(user_id, ConsentPurpose.MARKETING) is True

        gdpr.withdraw_consent(user_id=user_id, purpose=ConsentPurpose.MARKETING)
        assert gdpr.check_consent(user_id, ConsentPurpose.MARKETING) is False

    def test_consent_history_from_db(self, gdpr, user_id):
        """get_consent_history should return all records from the database."""
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.SERVICE_PROVISION)
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.ANALYTICS)
        gdpr.withdraw_consent(user_id=user_id, purpose=ConsentPurpose.ANALYTICS)

        history = gdpr.get_consent_history(user_id)
        assert len(history) == 3
        assert all(isinstance(r, dict) for r in history)
        assert history[0]["purpose"] == "service_provision"

    def test_multiple_users_isolated(self, gdpr):
        """Consent records should be isolated between users."""
        user_a = f"user_a_{uuid.uuid4().hex[:6]}"
        user_b = f"user_b_{uuid.uuid4().hex[:6]}"

        gdpr.grant_consent(user_id=user_a, purpose=ConsentPurpose.ANALYTICS)
        gdpr.grant_consent(user_id=user_b, purpose=ConsentPurpose.MARKETING)

        assert gdpr.check_consent(user_a, ConsentPurpose.ANALYTICS) is True
        assert gdpr.check_consent(user_a, ConsentPurpose.MARKETING) is False
        assert gdpr.check_consent(user_b, ConsentPurpose.MARKETING) is True
        assert gdpr.check_consent(user_b, ConsentPurpose.ANALYTICS) is False


class TestSubjectAccessRequest:
    """Test Subject Access Requests (Article 15) with database."""

    def test_data_access_request_persists(self, gdpr, user_id):
        """Data access requests should be persisted to the database."""
        request = gdpr.request_data_access(
            user_id=user_id, format=DataExportFormat.JSON
        )

        assert request.status == "pending"
        assert request.user_id == user_id
        assert "access_" in request.request_id

    def test_export_includes_all_personal_data(self, gdpr, db_manager, user_id):
        """Data export should include account data, usage data, consent, and audit logs."""
        # Save some personal data first
        db_manager.save_user_personal_data(
            user_id=user_id,
            username="testuser",
            email="test@example.com",
            role="viewer",
        )

        # Grant consent
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.SERVICE_PROVISION)

        # Export data
        exported_json = gdpr.export_user_data(user_id, DataExportFormat.JSON)

        assert user_id in exported_json
        assert "account_data" in exported_json
        assert "testuser" in exported_json
        assert "test@example.com" in exported_json
        assert "consent_records" in exported_json
        assert "audit_logs" in exported_json

    def test_export_csv_format(self, gdpr, db_manager, user_id):
        """Data export in CSV format should contain account data."""
        db_manager.save_user_personal_data(
            user_id=user_id,
            username="csvuser",
            email="csv@example.com",
        )
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.SERVICE_PROVISION)

        exported_csv = gdpr.export_user_data(user_id, DataExportFormat.CSV)

        assert "Account Data" in exported_csv
        assert isinstance(exported_csv, str)

    def test_export_with_no_data_returns_empty_structure(self, gdpr):
        """Exporting data for a user with no stored data should return empty fields."""
        nonexistent_user = f"ghost_{uuid.uuid4().hex[:8]}"
        exported = gdpr.export_user_data(nonexistent_user, DataExportFormat.JSON)

        assert nonexistent_user in exported
        assert "account_data" in exported


class TestRightToErasure:
    """Test Right to Erasure (Article 17) with database."""

    def test_deletion_request_persists(self, gdpr, user_id):
        """Deletion requests should be persisted to the database."""
        request = gdpr.request_data_deletion(
            user_id=user_id, reason="No longer need service"
        )

        assert request.status == "grace_period"
        assert request.reason == "No longer need service"

        # Verify in database
        db_req = gdpr.db.get_data_deletion_request(request.request_id)
        assert db_req is not None
        assert db_req["status"] == "grace_period"
        assert db_req["user_id"] == user_id

    def test_deletion_grace_period_enforced(self, gdpr, user_id):
        """Deletion should not execute before the grace period ends."""
        request = gdpr.request_data_deletion(user_id=user_id)

        # Try to execute immediately - should fail (grace period not elapsed)
        result = gdpr.execute_data_deletion(request.request_id)
        assert result is False

    def test_cancel_deletion_during_grace_period(self, gdpr, user_id):
        """Deletion requests should be cancellable during grace period."""
        request = gdpr.request_data_deletion(user_id=user_id)

        success = gdpr.cancel_deletion_request(request.request_id)
        assert success is True
        assert gdpr.deletion_requests[request.request_id].status == "cancelled"

    def test_deletion_actually_removes_data(self, gdpr, db_manager, user_id):
        """After deletion, personal data should be actually removed from the database."""
        # Create user data
        db_manager.save_user_personal_data(
            user_id=user_id,
            username="todelete",
            email="delete@example.com",
        )
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.SERVICE_PROVISION)

        # Verify data exists
        assert db_manager.get_user_personal_data(user_id) is not None
        assert len(db_manager.get_consent_records(user_id)) > 0

        # Execute deletion directly (bypassing grace period for testing)
        success = gdpr._delete_user_data(user_id)
        assert success is True

        # Verify personal data is gone
        assert db_manager.get_user_personal_data(user_id) is None

        # Consent records should be removed
        assert len(db_manager.get_consent_records(user_id)) == 0

    def test_deletion_anonymizes_audit_logs(self, gdpr, audit_logger, user_id):
        """After deletion, audit logs should be anonymized, not deleted."""
        from src.security.audit import AuditEvent, AuditEventType, AuditSeverity

        # Create some audit events for the user
        event = AuditEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            event_type=AuditEventType.QUERY_EXECUTED,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username="testuser",
            details={"query": "test query"},
        )
        audit_logger.log_event(event)

        # Verify event exists with user_id
        events = audit_logger.get_events(user_id=user_id)
        assert len(events) >= 1

        # Execute deletion
        success = gdpr._delete_user_data(user_id)
        assert success is True

        # Verify audit logs are anonymized (original user_id no longer findable)
        events_after = audit_logger.get_events(user_id=user_id)
        assert len(events_after) == 0

        # Verify anonymized logs still exist
        anonymized_id = f"deleted_{user_id[:8]}"
        anonymized_events = audit_logger.get_events(user_id=anonymized_id)
        assert len(anonymized_events) >= 1


class TestRightToRectification:
    """Test Right to Rectification (Article 16) with database."""

    def test_rectify_email_updates_db(self, gdpr, db_manager, user_id):
        """Rectifying email should update the database record."""
        db_manager.save_user_personal_data(
            user_id=user_id,
            username="rectifyuser",
            email="old@example.com",
        )

        result = gdpr.rectify_user_data(
            user_id=user_id, field="email", new_value="new@example.com"
        )
        assert result["success"] is True

        # Verify database was updated
        user_data = db_manager.get_user_personal_data(user_id)
        assert user_data["email"] == "new@example.com"

    def test_rectify_username_updates_db(self, gdpr, db_manager, user_id):
        """Rectifying username should update the database record."""
        db_manager.save_user_personal_data(
            user_id=user_id,
            username="oldname",
            email="test@example.com",
        )

        result = gdpr.rectify_user_data(
            user_id=user_id, field="username", new_value="newname"
        )
        assert result["success"] is True

        user_data = db_manager.get_user_personal_data(user_id)
        assert user_data["username"] == "newname"

    def test_rectify_disallowed_field_rejected(self, gdpr, user_id):
        """Attempting to rectify a disallowed field should be rejected."""
        result = gdpr.rectify_user_data(
            user_id=user_id, field="password", new_value="secret"
        )
        assert result["success"] is False
        assert "error" in result


class TestAuditTrailIntegrity:
    """Test audit trail completeness and integrity."""

    def test_consent_actions_audited(self, gdpr, audit_logger, user_id):
        """Consent grant and withdrawal should be logged in audit trail."""
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.ANALYTICS)
        gdpr.withdraw_consent(user_id=user_id, purpose=ConsentPurpose.ANALYTICS)

        logs = audit_logger.get_user_logs(user_id)
        # The GDPR event type is stored in the 'action' field of the audit event
        actions = [log.get("action", "") for log in logs]
        assert "consent_granted" in actions
        assert "consent_withdrawn" in actions

    def test_data_access_request_audited(self, gdpr, audit_logger, user_id):
        """Data access requests should be logged in audit trail."""
        gdpr.request_data_access(user_id=user_id)

        logs = audit_logger.get_user_logs(user_id)
        actions = [log.get("action", "") for log in logs]
        assert "data_access_requested" in actions

    def test_deletion_request_audited(self, gdpr, audit_logger, user_id):
        """Data deletion requests should be logged in audit trail."""
        gdpr.request_data_deletion(user_id=user_id, reason="Testing")

        logs = audit_logger.get_user_logs(user_id)
        actions = [log.get("action", "") for log in logs]
        assert "data_deletion_requested" in actions

    def test_audit_logs_included_in_data_export(self, gdpr, audit_logger, user_id):
        """Audit logs should be included in subject access request exports."""
        gdpr.grant_consent(user_id=user_id, purpose=ConsentPurpose.SERVICE_PROVISION)

        exported = gdpr.export_user_data(user_id, DataExportFormat.JSON)
        assert "audit_logs" in exported


class TestDataRetentionAndCleanup:
    """Test data retention policies and automated cleanup."""

    def test_cleanup_expired_gdpr_data(self, db_manager):
        """Cleanup should remove completed requests older than retention period."""
        user_id = f"cleanup_user_{uuid.uuid4().hex[:6]}"

        # Create an old completed access request
        old_request_id = f"access_old_{uuid.uuid4().hex[:6]}"
        db_manager.save_data_access_request(
            request_id=old_request_id, user_id=user_id, format="json"
        )
        db_manager.update_data_access_request(old_request_id, "completed")

        # Manually backdate the completed_at timestamp
        from src.storage.database import DBDataAccessRequest
        with db_manager.get_session() as session:
            record = session.query(DBDataAccessRequest).filter_by(
                request_id=old_request_id
            ).first()
            record.completed_at = datetime.utcnow() - timedelta(days=200)
            session.commit()

        # Run cleanup with 90-day retention
        results = db_manager.cleanup_expired_gdpr_data(retention_days=90)
        assert results["completed_access_requests"] >= 1

    def test_run_data_retention_cleanup_via_gdpr(self, gdpr, db_manager):
        """run_data_retention_cleanup should process pending deletions and clean old data."""
        result = gdpr.run_data_retention_cleanup(retention_days=90)

        assert "timestamp" in result
        assert "deletions_executed" in result
        assert "requests_cleaned" in result

    def test_pending_deletions_past_grace_period_processed(self, gdpr, db_manager):
        """Pending deletion requests past grace period should be auto-processed."""
        user_id = f"retention_user_{uuid.uuid4().hex[:6]}"
        db_manager.save_user_personal_data(
            user_id=user_id, username="retentionuser", email="retain@test.com"
        )

        # Create a deletion request
        request = gdpr.request_data_deletion(user_id=user_id)

        # Manually backdate scheduled_for to simulate grace period expiration
        from src.storage.database import DBDataDeletionRequest
        with db_manager.get_session() as session:
            record = session.query(DBDataDeletionRequest).filter_by(
                request_id=request.request_id
            ).first()
            record.scheduled_for = datetime.utcnow() - timedelta(days=1)
            session.commit()

        # Also update the in-memory request
        gdpr.deletion_requests[request.request_id].scheduled_for = (
            datetime.utcnow() - timedelta(days=1)
        )

        # Run cleanup
        result = gdpr.run_data_retention_cleanup()
        assert result["deletions_executed"] >= 1


class TestDatabaseModelOperations:
    """Test the underlying database model operations directly."""

    def test_save_and_get_user_personal_data(self, db_manager):
        """Test saving and retrieving user personal data."""
        user_id = f"db_user_{uuid.uuid4().hex[:6]}"
        db_manager.save_user_personal_data(
            user_id=user_id,
            username="dbuser",
            email="db@example.com",
            role="admin",
        )

        data = db_manager.get_user_personal_data(user_id)
        assert data is not None
        assert data["username"] == "dbuser"
        assert data["email"] == "db@example.com"
        assert data["role"] == "admin"
        assert data["is_active"] is True

    def test_deactivate_user(self, db_manager):
        """Test deactivating a user."""
        user_id = f"deact_user_{uuid.uuid4().hex[:6]}"
        db_manager.save_user_personal_data(user_id=user_id, username="active")

        db_manager.deactivate_user(user_id)

        data = db_manager.get_user_personal_data(user_id)
        assert data["is_active"] is False

    def test_delete_user_personal_data(self, db_manager):
        """Test hard-deleting user personal data."""
        user_id = f"del_user_{uuid.uuid4().hex[:6]}"
        db_manager.save_user_personal_data(
            user_id=user_id, username="tobedeleted", email="del@example.com"
        )
        db_manager.save_consent_record(
            user_id=user_id, purpose="analytics", granted=True
        )

        # Delete
        result = db_manager.delete_user_personal_data(user_id)
        assert result is True

        # Verify data is gone
        assert db_manager.get_user_personal_data(user_id) is None
        assert len(db_manager.get_consent_records(user_id)) == 0

    def test_update_user_personal_field(self, db_manager):
        """Test updating a specific personal data field."""
        user_id = f"upd_user_{uuid.uuid4().hex[:6]}"
        db_manager.save_user_personal_data(
            user_id=user_id, username="orig", email="orig@test.com"
        )

        result = db_manager.update_user_personal_field(user_id, "email", "new@test.com")
        assert result is True

        data = db_manager.get_user_personal_data(user_id)
        assert data["email"] == "new@test.com"

    def test_update_disallowed_field_rejected(self, db_manager):
        """Updating a disallowed field should return False."""
        user_id = f"bad_upd_{uuid.uuid4().hex[:6]}"
        db_manager.save_user_personal_data(user_id=user_id, username="test")

        result = db_manager.update_user_personal_field(user_id, "role", "superadmin")
        assert result is False

    def test_consent_record_crud(self, db_manager):
        """Test full CRUD cycle for consent records."""
        user_id = f"consent_crud_{uuid.uuid4().hex[:6]}"

        # Create
        db_manager.save_consent_record(
            user_id=user_id, purpose="analytics", granted=True, version="1.0"
        )
        db_manager.save_consent_record(
            user_id=user_id, purpose="marketing", granted=False
        )

        # Read
        records = db_manager.get_consent_records(user_id)
        assert len(records) == 2

        # Check latest
        latest = db_manager.get_latest_consent(user_id, "analytics")
        assert latest["granted"] is True

        # Delete
        db_manager.delete_consent_records(user_id)
        assert len(db_manager.get_consent_records(user_id)) == 0

    def test_data_access_request_lifecycle(self, db_manager):
        """Test data access request save and update."""
        user_id = f"access_lc_{uuid.uuid4().hex[:6]}"
        request_id = f"access_{uuid.uuid4().hex[:8]}"

        db_manager.save_data_access_request(
            request_id=request_id, user_id=user_id, format="json"
        )
        db_manager.update_data_access_request(request_id, "completed")

    def test_data_deletion_request_lifecycle(self, db_manager):
        """Test data deletion request save, get, and update."""
        user_id = f"del_lc_{uuid.uuid4().hex[:6]}"
        request_id = f"delete_{uuid.uuid4().hex[:8]}"

        db_manager.save_data_deletion_request(
            request_id=request_id,
            user_id=user_id,
            scheduled_for=datetime.utcnow() + timedelta(days=30),
            reason="Test reason",
        )

        req = db_manager.get_data_deletion_request(request_id)
        assert req is not None
        assert req["status"] == "grace_period"
        assert req["reason"] == "Test reason"

        db_manager.update_data_deletion_request(request_id, "completed")
        req = db_manager.get_data_deletion_request(request_id)
        assert req["status"] == "completed"

    def test_get_user_usage_data(self, db_manager):
        """Test retrieving usage data for GDPR export."""
        # Usage data is keyed by tenant_id; for GDPR it maps to user_id
        usage = db_manager.get_user_usage_data("nonexistent_user")
        assert isinstance(usage, list)
        assert len(usage) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
