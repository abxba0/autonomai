"""
Tests for multi-tenant support
"""

import pytest
from datetime import datetime, timedelta
import uuid

# Skip if dependencies not available
pytest.importorskip("sqlalchemy")

from src.models.tenant import (
    Tenant,
    TenantStatus,
    TenantPlan,
    TenantPlanLimits,
    TenantConfig,
    UsageRecord,
)
from src.models.config import SystemConfig
from src.storage import DatabaseManager, TenantManager, UsageTracker


class TestTenantModels:
    """Test tenant data models"""
    
    def test_tenant_creation(self):
        """Test creating a tenant"""
        tenant = Tenant(
            tenant_id="test-tenant-1",
            name="Test Tenant",
            email="test@example.com",
            plan=TenantPlan.FREE,
        )
        
        assert tenant.tenant_id == "test-tenant-1"
        assert tenant.name == "Test Tenant"
        assert tenant.email == "test@example.com"
        assert tenant.plan == TenantPlan.FREE
        assert tenant.status == TenantStatus.ACTIVE
        assert tenant.is_active()
        assert tenant.can_make_request()
    
    def test_plan_limits(self):
        """Test plan limits"""
        free_limits = TenantPlanLimits.get_plan_limits(TenantPlan.FREE)
        assert free_limits.requests_per_day == 1000
        assert free_limits.max_users == 1
        
        enterprise_limits = TenantPlanLimits.get_plan_limits(TenantPlan.ENTERPRISE)
        assert enterprise_limits.requests_per_day == 100000
        assert enterprise_limits.max_users == 50
    
    def test_tenant_status_checks(self):
        """Test tenant status methods"""
        tenant = Tenant(
            tenant_id="test-tenant-2",
            name="Test Tenant",
            email="test@example.com",
            status=TenantStatus.SUSPENDED,
        )
        
        assert tenant.is_suspended()
        assert not tenant.can_make_request()
    
    def test_tenant_config(self):
        """Test tenant configuration"""
        config = TenantConfig(
            tenant_id="test-tenant-1",
            anthropic_api_key="test-key",
            enable_auto_optimization=True,
        )
        
        assert config.tenant_id == "test-tenant-1"
        assert config.anthropic_api_key == "test-key"
        assert config.enable_auto_optimization is True
        
        # Test serialization
        config_dict = config.to_dict()
        assert config_dict["tenant_id"] == "test-tenant-1"
        
        # Test deserialization
        config2 = TenantConfig.from_dict(config_dict)
        assert config2.tenant_id == config.tenant_id


class TestDatabaseIntegration:
    """Test database operations for tenants"""
    
    @pytest.fixture
    def db_manager(self):
        """Create database manager with in-memory SQLite"""
        config = SystemConfig()
        # Use in-memory database for testing
        import os
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        
        db_manager = DatabaseManager(config)
        yield db_manager
    
    def test_create_and_get_tenant(self, db_manager):
        """Test creating and retrieving a tenant"""
        tenant = Tenant(
            tenant_id=f"test-{uuid.uuid4().hex[:8]}",
            name="Test Company",
            email="test@company.com",
            plan=TenantPlan.STARTER,
        )
        
        # Create tenant
        assert db_manager.create_tenant(tenant) is True
        
        # Retrieve tenant
        retrieved = db_manager.get_tenant(tenant.tenant_id)
        assert retrieved is not None
        assert retrieved.tenant_id == tenant.tenant_id
        assert retrieved.name == tenant.name
        assert retrieved.plan == TenantPlan.STARTER
    
    def test_update_tenant(self, db_manager):
        """Test updating tenant information"""
        tenant = Tenant(
            tenant_id=f"test-{uuid.uuid4().hex[:8]}",
            name="Original Name",
            email="test@example.com",
        )
        
        db_manager.create_tenant(tenant)
        
        # Update tenant
        tenant.name = "Updated Name"
        tenant.company = "Updated Company"
        assert db_manager.update_tenant(tenant) is True
        
        # Verify update
        retrieved = db_manager.get_tenant(tenant.tenant_id)
        assert retrieved.name == "Updated Name"
        assert retrieved.company == "Updated Company"
    
    def test_list_tenants(self, db_manager):
        """Test listing tenants"""
        # Create multiple tenants
        for i in range(3):
            tenant = Tenant(
                tenant_id=f"test-{uuid.uuid4().hex[:8]}",
                name=f"Tenant {i}",
                email=f"tenant{i}@example.com",
            )
            db_manager.create_tenant(tenant)
        
        # List all tenants
        tenants = db_manager.list_tenants()
        assert len(tenants) >= 3
    
    def test_suspend_and_activate_tenant(self, db_manager):
        """Test suspending and activating a tenant"""
        tenant = Tenant(
            tenant_id=f"test-{uuid.uuid4().hex[:8]}",
            name="Test Tenant",
            email="test@example.com",
        )
        
        db_manager.create_tenant(tenant)
        
        # Suspend tenant
        assert db_manager.suspend_tenant(tenant.tenant_id) is True
        
        # Verify suspension
        retrieved = db_manager.get_tenant(tenant.tenant_id)
        assert retrieved.status == TenantStatus.SUSPENDED
        
        # Activate tenant
        assert db_manager.activate_tenant(tenant.tenant_id) is True
        
        # Verify activation
        retrieved = db_manager.get_tenant(tenant.tenant_id)
        assert retrieved.status == TenantStatus.ACTIVE
    
    def test_tenant_config_operations(self, db_manager):
        """Test tenant configuration operations"""
        tenant = Tenant(
            tenant_id=f"test-{uuid.uuid4().hex[:8]}",
            name="Test Tenant",
            email="test@example.com",
        )
        db_manager.create_tenant(tenant)
        
        # Create config
        config = TenantConfig(
            tenant_id=tenant.tenant_id,
            anthropic_api_key="test-key-123",
            enable_auto_optimization=False,
        )
        
        assert db_manager.save_tenant_config(config) is True
        
        # Retrieve config
        retrieved_config = db_manager.get_tenant_config(tenant.tenant_id)
        assert retrieved_config is not None
        assert retrieved_config.anthropic_api_key == "test-key-123"
        assert retrieved_config.enable_auto_optimization is False
    
    def test_usage_tracking(self, db_manager):
        """Test usage recording and retrieval"""
        tenant = Tenant(
            tenant_id=f"test-{uuid.uuid4().hex[:8]}",
            name="Test Tenant",
            email="test@example.com",
        )
        db_manager.create_tenant(tenant)
        
        # Record usage
        usage = UsageRecord(
            usage_id=f"usage-{uuid.uuid4().hex[:12]}",
            tenant_id=tenant.tenant_id,
            tokens_used=1000,
            input_tokens=500,
            output_tokens=500,
            successful_requests=1,
        )
        
        assert db_manager.record_usage(usage) is True
        
        # Get usage summary
        summary = db_manager.get_usage_summary(tenant.tenant_id)
        assert summary["total_tokens"] == 1000
        assert summary["successful_requests"] == 1


class TestTenantManager:
    """Test tenant manager operations"""
    
    @pytest.fixture
    def tenant_manager(self):
        """Create tenant manager with in-memory database"""
        config = SystemConfig()
        import os
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        
        db_manager = DatabaseManager(config)
        tenant_manager = TenantManager(db_manager)
        yield tenant_manager
    
    def test_create_tenant(self, tenant_manager):
        """Test creating tenant via manager"""
        tenant = tenant_manager.create_tenant(
            name="New Company",
            email="new@company.com",
            plan=TenantPlan.PROFESSIONAL,
        )
        
        assert tenant is not None
        assert tenant.name == "New Company"
        assert tenant.plan == TenantPlan.PROFESSIONAL
        assert tenant.plan_limits.requests_per_day == 20000
    
    def test_onboard_tenant(self, tenant_manager):
        """Test tenant onboarding workflow"""
        result = tenant_manager.onboard_tenant(
            name="Onboard Test",
            email="onboard@test.com",
            plan=TenantPlan.STARTER,
            company="Test Corp",
        )
        
        assert result["success"] is True
        assert "tenant_id" in result
        assert result["tenant"]["name"] == "Onboard Test"
    
    def test_upgrade_plan(self, tenant_manager):
        """Test upgrading tenant plan"""
        tenant = tenant_manager.create_tenant(
            name="Upgrade Test",
            email="upgrade@test.com",
            plan=TenantPlan.FREE,
        )
        
        # Upgrade to professional
        assert tenant_manager.upgrade_plan(tenant.tenant_id, TenantPlan.PROFESSIONAL) is True
        
        # Verify upgrade
        updated_tenant = tenant_manager.db.get_tenant(tenant.tenant_id)
        assert updated_tenant.plan == TenantPlan.PROFESSIONAL
    
    def test_check_tenant_limits(self, tenant_manager):
        """Test checking tenant limits"""
        tenant = tenant_manager.create_tenant(
            name="Limits Test",
            email="limits@test.com",
            plan=TenantPlan.FREE,
        )
        
        limits_check = tenant_manager.check_tenant_limits(tenant.tenant_id)
        assert limits_check["can_proceed"] is True
        assert "limits" in limits_check


class TestUsageTracker:
    """Test usage tracking"""
    
    @pytest.fixture
    def usage_tracker(self):
        """Create usage tracker with in-memory database"""
        config = SystemConfig()
        import os
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        
        db_manager = DatabaseManager(config)
        usage_tracker = UsageTracker(db_manager)
        
        # Create a test tenant
        tenant = Tenant(
            tenant_id="usage-test-tenant",
            name="Usage Test",
            email="usage@test.com",
        )
        db_manager.create_tenant(tenant)
        
        yield usage_tracker
    
    def test_record_request(self, usage_tracker):
        """Test recording a request"""
        assert usage_tracker.record_request(
            tenant_id="usage-test-tenant",
            tokens_used=1000,
            input_tokens=400,
            output_tokens=600,
            success=True,
            model_used="claude-3-sonnet",
        ) is True
    
    def test_get_usage_report(self, usage_tracker):
        """Test getting usage report"""
        # Record some usage
        for i in range(3):
            usage_tracker.record_request(
                tenant_id="usage-test-tenant",
                tokens_used=500,
                success=True,
            )
        
        # Get report
        report = usage_tracker.get_usage_report("usage-test-tenant")
        assert report["summary"]["total_requests"] >= 3
        assert report["summary"]["total_tokens"] >= 1500
    
    def test_export_for_billing(self, usage_tracker):
        """Test exporting usage for billing"""
        # Record usage
        usage_tracker.record_request(
            tenant_id="usage-test-tenant",
            tokens_used=10000,
            input_tokens=5000,
            output_tokens=5000,
            success=True,
            model_used="claude-3-sonnet",
        )
        
        # Export for billing
        start = datetime.utcnow() - timedelta(days=1)
        end = datetime.utcnow()
        
        billing_data = usage_tracker.export_usage_for_billing(
            "usage-test-tenant",
            start,
            end,
        )
        
        assert "cost" in billing_data
        assert "usage" in billing_data
        assert billing_data["usage"]["total_tokens"] >= 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
