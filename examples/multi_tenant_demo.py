"""
Example: Multi-Tenant System Usage

Demonstrates how to use the multi-tenant features including:
- Creating and managing tenants
- Configuring tenant-specific settings
- Tracking usage
- Checking limits
- Generating billing reports
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

# Set up in-memory database for demo
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from src.models.config import SystemConfig
from src.models.tenant import Tenant, TenantPlan, TenantConfig
from src.storage import DatabaseManager, TenantManager, UsageTracker


def main():
    print("=" * 60)
    print("Multi-Tenant System Demo")
    print("=" * 60)
    
    # Initialize system
    print("\n1. Initializing multi-tenant system...")
    config = SystemConfig()
    db_manager = DatabaseManager(config)
    tenant_manager = TenantManager(db_manager)
    usage_tracker = UsageTracker(db_manager)
    print("✓ System initialized")
    
    # Create tenants
    print("\n2. Creating tenants...")
    
    # Tenant 1: Free tier
    tenant1 = tenant_manager.create_tenant(
        name="Startup Inc",
        email="admin@startup.com",
        plan=TenantPlan.FREE,
        company="Startup Inc",
    )
    print(f"✓ Created tenant: {tenant1.name} (ID: {tenant1.tenant_id})")
    print(f"  Plan: {tenant1.plan.value}")
    print(f"  Limits: {tenant1.plan_limits.requests_per_day} requests/day")
    
    # Tenant 2: Professional tier
    result = tenant_manager.onboard_tenant(
        name="Acme Corporation",
        email="admin@acme.com",
        plan=TenantPlan.PROFESSIONAL,
        company="Acme Corp",
        api_keys={
            "anthropic_api_key": "sk-ant-demo-key",
            "openai_api_key": "sk-demo-key",
        }
    )
    tenant2_id = result["tenant_id"]
    print(f"✓ Onboarded tenant: Acme Corporation (ID: {tenant2_id})")
    print(f"  Plan: professional")
    print(f"  API keys configured: ✓")
    
    # Configure tenant
    print("\n3. Configuring tenant settings...")
    config = db_manager.get_tenant_config(tenant2_id)
    config.enable_multimodal = True
    config.enable_workflow_orchestrator = True
    config.default_main_model = "gpt-4-turbo-preview"
    db_manager.save_tenant_config(config)
    print(f"✓ Updated configuration for {tenant2_id}")
    print(f"  Multimodal: {config.enable_multimodal}")
    print(f"  Workflows: {config.enable_workflow_orchestrator}")
    print(f"  Main model: {config.default_main_model}")
    
    # Record usage
    print("\n4. Recording usage...")
    
    # Simulate some requests for tenant 1
    for i in range(5):
        usage_tracker.record_request(
            tenant_id=tenant1.tenant_id,
            tokens_used=500 + i * 100,
            input_tokens=200 + i * 40,
            output_tokens=300 + i * 60,
            success=True,
            execution_time_ms=150.5 + i * 10,
            model_used="claude-3-haiku",
            provider_used="anthropic",
            endpoint="/api/query",
        )
    print(f"✓ Recorded 5 requests for {tenant1.name}")
    
    # Simulate requests for tenant 2
    for i in range(10):
        usage_tracker.record_request(
            tenant_id=tenant2_id,
            tokens_used=2000 + i * 200,
            input_tokens=800 + i * 80,
            output_tokens=1200 + i * 120,
            success=i < 9,  # One failed request
            execution_time_ms=250.0 + i * 15,
            model_used="gpt-4-turbo-preview",
            provider_used="openai",
            endpoint="/api/generate",
        )
    print(f"✓ Recorded 10 requests for Acme Corporation")
    
    # Check usage
    print("\n5. Checking usage and limits...")
    
    # Tenant 1 usage
    summary1 = db_manager.get_usage_summary(tenant1.tenant_id)
    print(f"\n{tenant1.name} ({tenant1.plan.value}):")
    print(f"  Total requests: {summary1['total_requests']}")
    print(f"  Successful: {summary1['successful_requests']}")
    print(f"  Total tokens: {summary1['total_tokens']:,}")
    print(f"  Estimated cost: ${summary1['total_cost_cents'] / 100:.2f}")
    print(f"  Avg execution time: {summary1['avg_execution_time_ms']:.2f}ms")
    
    # Check limits
    limits1 = tenant_manager.check_tenant_limits(tenant1.tenant_id)
    print(f"  Within limits: {'✓' if limits1['can_proceed'] else '✗'}")
    if limits1.get('warnings'):
        print(f"  Warnings: {limits1['warnings']}")
    
    # Tenant 2 usage
    summary2 = db_manager.get_usage_summary(tenant2_id)
    print(f"\nAcme Corporation (professional):")
    print(f"  Total requests: {summary2['total_requests']}")
    print(f"  Successful: {summary2['successful_requests']}")
    print(f"  Failed: {summary2['failed_requests']}")
    print(f"  Total tokens: {summary2['total_tokens']:,}")
    print(f"  Estimated cost: ${summary2['total_cost_cents'] / 100:.2f}")
    print(f"  Avg execution time: {summary2['avg_execution_time_ms']:.2f}ms")
    
    limits2 = tenant_manager.check_tenant_limits(tenant2_id)
    print(f"  Within limits: {'✓' if limits2['can_proceed'] else '✗'}")
    
    # Generate billing report
    print("\n6. Generating billing report...")
    
    start_date = datetime.utcnow() - timedelta(days=1)
    end_date = datetime.utcnow()
    
    billing = usage_tracker.export_usage_for_billing(
        tenant_id=tenant2_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    print(f"\nBilling Report for Acme Corporation")
    print(f"Period: {billing['billing_period']['start'][:10]} to {billing['billing_period']['end'][:10]}")
    print(f"Total requests: {billing['usage']['total_requests']}")
    print(f"Total tokens: {billing['usage']['total_tokens']:,}")
    print(f"  Input: {billing['usage']['input_tokens']:,}")
    print(f"  Output: {billing['usage']['output_tokens']:,}")
    print(f"Total cost: ${billing['cost']['total_dollars']:.2f}")
    print(f"Avg execution time: {billing['performance']['avg_execution_time_ms']:.2f}ms")
    
    # Upgrade plan
    print("\n7. Upgrading tenant plan...")
    print(f"Current plan for {tenant1.name}: {tenant1.plan.value}")
    
    if tenant_manager.upgrade_plan(tenant1.tenant_id, TenantPlan.STARTER):
        print(f"✓ Upgraded to: starter")
        
        # Get updated tenant
        updated_tenant = db_manager.get_tenant(tenant1.tenant_id)
        print(f"  New limits:")
        print(f"    Requests/day: {updated_tenant.plan_limits.requests_per_day}")
        print(f"    Tokens/month: {updated_tenant.plan_limits.tokens_per_month:,}")
        print(f"    Max users: {updated_tenant.plan_limits.max_users}")
    
    # Suspend and reactivate
    print("\n8. Testing suspension...")
    
    print(f"Suspending {tenant1.name}...")
    tenant_manager.suspend_tenant(tenant1.tenant_id, reason="Demo suspension")
    
    suspended = db_manager.get_tenant(tenant1.tenant_id)
    print(f"✓ Status: {suspended.status.value}")
    print(f"  Can make requests: {suspended.can_make_request()}")
    
    print(f"Reactivating {tenant1.name}...")
    tenant_manager.activate_tenant(tenant1.tenant_id)
    
    activated = db_manager.get_tenant(tenant1.tenant_id)
    print(f"✓ Status: {activated.status.value}")
    print(f"  Can make requests: {activated.can_make_request()}")
    
    # List all tenants
    print("\n9. Listing all tenants...")
    all_tenants = tenant_manager.list_all_tenants()
    print(f"Total tenants: {len(all_tenants)}")
    for t in all_tenants:
        print(f"  - {t['name']} ({t['plan']}) - {t['status']}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    
    # Print summary
    print("\nKey Features Demonstrated:")
    print("✓ Tenant creation and onboarding")
    print("✓ Tenant-specific configuration")
    print("✓ Usage tracking and metering")
    print("✓ Limit checking")
    print("✓ Billing report generation")
    print("✓ Plan upgrades")
    print("✓ Tenant suspension/activation")
    print("✓ Complete data isolation")
    
    print("\nNext Steps:")
    print("- Run tenant management API: python web/api_tenant_management.py")
    print("- Check documentation: docs/MULTI_TENANT.md")
    print("- Run tests: pytest tests/test_multi_tenant.py -v")


if __name__ == "__main__":
    main()
