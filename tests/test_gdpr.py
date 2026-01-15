"""
Tests for UK GDPR compliance functionality
"""

import pytest
from datetime import datetime, timedelta

from src.security.gdpr import (
    GDPRCompliance,
    ConsentPurpose,
    ConsentRecord,
    DataExportFormat,
)


class TestGDPRCompliance:
    """Test suite for GDPR compliance features"""

    def test_grant_consent(self):
        """Test granting consent for a purpose"""
        gdpr = GDPRCompliance()
        
        consent = gdpr.grant_consent(
            user_id="user123",
            purpose=ConsentPurpose.SERVICE_PROVISION,
            version="1.0",
            method="web"
        )
        
        assert consent.user_id == "user123"
        assert consent.purpose == ConsentPurpose.SERVICE_PROVISION
        assert consent.granted is True
        assert consent.version == "1.0"
        assert isinstance(consent.timestamp, datetime)

    def test_withdraw_consent(self):
        """Test withdrawing consent"""
        gdpr = GDPRCompliance()
        
        # Grant consent first
        gdpr.grant_consent(
            user_id="user123",
            purpose=ConsentPurpose.ANALYTICS
        )
        
        # Withdraw consent
        withdrawal = gdpr.withdraw_consent(
            user_id="user123",
            purpose=ConsentPurpose.ANALYTICS
        )
        
        assert withdrawal.granted is False
        assert withdrawal.purpose == ConsentPurpose.ANALYTICS

    def test_check_consent(self):
        """Test checking consent status"""
        gdpr = GDPRCompliance()
        
        # Initially no consent
        assert gdpr.check_consent("user123", ConsentPurpose.MARKETING) is False
        
        # Grant consent
        gdpr.grant_consent("user123", ConsentPurpose.MARKETING)
        assert gdpr.check_consent("user123", ConsentPurpose.MARKETING) is True
        
        # Withdraw consent
        gdpr.withdraw_consent("user123", ConsentPurpose.MARKETING)
        assert gdpr.check_consent("user123", ConsentPurpose.MARKETING) is False

    def test_consent_history(self):
        """Test consent history tracking"""
        gdpr = GDPRCompliance()
        
        # Grant multiple consents
        gdpr.grant_consent("user123", ConsentPurpose.SERVICE_PROVISION)
        gdpr.grant_consent("user123", ConsentPurpose.ANALYTICS)
        gdpr.withdraw_consent("user123", ConsentPurpose.ANALYTICS)
        
        history = gdpr.get_consent_history("user123")
        
        assert len(history) == 3
        assert all(isinstance(record, dict) for record in history)

    def test_data_access_request(self):
        """Test creating data access request"""
        gdpr = GDPRCompliance()
        
        request = gdpr.request_data_access(
            user_id="user123",
            format=DataExportFormat.JSON
        )
        
        assert request.user_id == "user123"
        assert request.status == "pending"
        assert request.format == DataExportFormat.JSON
        assert "access_" in request.request_id

    def test_export_user_data_json(self):
        """Test exporting user data in JSON format"""
        gdpr = GDPRCompliance()
        
        # Add some consent records
        gdpr.grant_consent("user123", ConsentPurpose.SERVICE_PROVISION)
        
        exported = gdpr.export_user_data("user123", DataExportFormat.JSON)
        
        assert isinstance(exported, str)
        assert "user_id" in exported
        assert "user123" in exported
        assert "account_data" in exported

    def test_export_user_data_csv(self):
        """Test exporting user data in CSV format"""
        gdpr = GDPRCompliance()
        
        gdpr.grant_consent("user123", ConsentPurpose.SERVICE_PROVISION)
        
        exported = gdpr.export_user_data("user123", DataExportFormat.CSV)
        
        assert isinstance(exported, str)
        assert "Account Data" in exported

    def test_data_deletion_request(self):
        """Test creating data deletion request"""
        gdpr = GDPRCompliance()
        
        request = gdpr.request_data_deletion(
            user_id="user123",
            reason="No longer need service"
        )
        
        assert request.user_id == "user123"
        assert request.status == "grace_period"
        assert request.reason == "No longer need service"
        assert isinstance(request.scheduled_for, datetime)
        assert request.scheduled_for > datetime.utcnow()

    def test_cancel_deletion_request(self):
        """Test cancelling deletion request during grace period"""
        gdpr = GDPRCompliance()
        
        # Create deletion request
        request = gdpr.request_data_deletion("user123")
        
        # Cancel it
        success = gdpr.cancel_deletion_request(request.request_id)
        
        assert success is True
        assert request.status == "cancelled"

    def test_cannot_execute_deletion_before_grace_period(self):
        """Test that deletion cannot be executed before grace period"""
        gdpr = GDPRCompliance()
        
        request = gdpr.request_data_deletion("user123")
        
        # Try to execute immediately
        success = gdpr.execute_data_deletion(request.request_id)
        
        assert success is False

    def test_rectify_user_data_valid_field(self):
        """Test rectifying user data for allowed fields"""
        gdpr = GDPRCompliance()
        
        result = gdpr.rectify_user_data(
            user_id="user123",
            field="email",
            new_value="newemail@example.com"
        )
        
        assert result["success"] is True
        assert result["field"] == "email"
        assert "updated_at" in result

    def test_rectify_user_data_invalid_field(self):
        """Test rectifying user data for disallowed fields"""
        gdpr = GDPRCompliance()
        
        result = gdpr.rectify_user_data(
            user_id="user123",
            field="password",
            new_value="newpassword"
        )
        
        assert result["success"] is False
        assert "error" in result

    def test_get_processing_activities(self):
        """Test getting processing activities"""
        gdpr = GDPRCompliance()
        
        activities = gdpr.get_processing_activities("user123")
        
        assert isinstance(activities, list)
        assert len(activities) > 0
        assert all("activity" in a for a in activities)
        assert all("purpose" in a for a in activities)
        assert all("legal_basis" in a for a in activities)

    def test_consent_record_serialization(self):
        """Test consent record to_dict conversion"""
        consent = ConsentRecord(
            user_id="user123",
            purpose=ConsentPurpose.SERVICE_PROVISION,
            granted=True,
            version="1.0"
        )
        
        data = consent.to_dict()
        
        assert data["user_id"] == "user123"
        assert data["purpose"] == "service_provision"
        assert data["granted"] is True
        assert isinstance(data["timestamp"], str)


if __name__ == "__main__":
    # Run tests if pytest is available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed. Running basic tests...")
        test = TestGDPRCompliance()
        
        # Run basic tests
        test.test_grant_consent()
        print("✓ test_grant_consent passed")
        
        test.test_withdraw_consent()
        print("✓ test_withdraw_consent passed")
        
        test.test_check_consent()
        print("✓ test_check_consent passed")
        
        test.test_consent_history()
        print("✓ test_consent_history passed")
        
        test.test_data_access_request()
        print("✓ test_data_access_request passed")
        
        test.test_export_user_data_json()
        print("✓ test_export_user_data_json passed")
        
        test.test_data_deletion_request()
        print("✓ test_data_deletion_request passed")
        
        test.test_cancel_deletion_request()
        print("✓ test_cancel_deletion_request passed")
        
        test.test_rectify_user_data_valid_field()
        print("✓ test_rectify_user_data_valid_field passed")
        
        test.test_get_processing_activities()
        print("✓ test_get_processing_activities passed")
        
        print("\n✓ All basic tests passed!")
