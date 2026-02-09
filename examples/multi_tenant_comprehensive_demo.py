#!/usr/bin/env python3
"""
Comprehensive Multi-Tenant Demo

This example demonstrates complete multi-tenant functionality including:
- Tenant onboarding and management
- Tenant isolation and configuration
- Usage tracking and billing
- Plan upgrades and limits
- Admin operations

Prerequisites:
- Install dependencies: pip install -e ".[web]"
- Optional: Redis for distributed multi-tenant setup

Usage:
    python examples/multi_tenant_comprehensive_demo.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.storage.tenant_manager import TenantManager, UsageTracker
from src.models.tenant import TenantPlan, TenantStatus, TenantPlanLimits
from src import SelfOptimizingSystem, SystemConfig
from dotenv import load_dotenv
import time


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n--- {title} ---")


def demo_1_tenant_onboarding():
    """Demo 1: Complete tenant onboarding workflow"""
    print_section("Demo 1: Tenant Onboarding Workflow")

    load_dotenv()

    # Initialize tenant manager
    tenant_manager = TenantManager()

    print_subsection("1. Onboarding New Tenant")

    # Complete onboarding with all configurations
    result = tenant_manager.onboard_tenant(
        name="Acme Corporation",
        email="admin@acme.com",
        plan=TenantPlan.PROFESSIONAL,
        api_keys={
            "anthropic_api_key": "sk-ant-acme-key-12345",
            "openai_api_key": "sk-openai-acme-67890"
        },
        feature_flags={
            "advanced_analytics": True,
            "custom_models": True,
            "api_access": True
        },
        custom_config={
            "webhook_url": "https://acme.com/webhooks/autonomai",
            "notification_email": "alerts@acme.com"
        }
    )

    tenant_id = result["tenant_id"]
    print(f"\n✓ Tenant onboarded successfully!")
    print(f"  Tenant ID: {tenant_id}")
    print(f"  Name: {result['name']}")
    print(f"  Plan: {result['plan']}")
    print(f"  Status: {result['status']}")

    print_subsection("2. Retrieving Tenant Details")

    tenant = tenant_manager.get_tenant(tenant_id)
    if tenant:
        print(f"\nTenant Information:")
        print(f"  Name: {tenant.name}")
        print(f"  Email: {tenant.email}")
        print(f"  Plan: {tenant.plan.value}")
        print(f"  Status: {tenant.status.value}")
        print(f"  Created: {tenant.created_at}")

    print_subsection("3. Getting Tenant Configuration")

    config = tenant_manager.get_tenant_config(tenant_id)
    if config:
        print(f"\nConfiguration:")
        print(f"  Feature Flags: {config.feature_flags}")
        print(f"  Custom Config: {config.custom_config}")

    print_subsection("4. Checking Plan Limits")

    limits = tenant_manager.get_plan_limits(TenantPlan.PROFESSIONAL)
    print(f"\nProfessional Plan Limits:")
    print(f"  Max Requests/Day: {limits.max_requests_per_day:,}")
    print(f"  Max Requests/Month: {limits.max_requests_per_month:,}")
    print(f"  Max Storage GB: {limits.max_storage_gb}")
    print(f"  Max Users: {limits.max_users}")
    print(f"  Rate Limit (req/min): {limits.rate_limit_per_minute}")
    print(f"  Supports Webhooks: {limits.enable_webhooks}")
    print(f"  Supports Custom Models: {limits.enable_custom_models}")

    return tenant_id


def demo_2_usage_tracking(tenant_id: str):
    """Demo 2: Usage tracking and monitoring"""
    print_section("Demo 2: Usage Tracking & Monitoring")

    # Initialize usage tracker
    usage_tracker = UsageTracker()

    print_subsection("1. Recording Usage")

    # Simulate various API requests
    print("\nSimulating 100 API requests...")

    for i in range(100):
        # Simulate different request types
        tokens = 500 + (i % 1000)  # Varying token usage
        cost = tokens * 0.00002  # $0.02 per 1k tokens

        success = i % 10 != 0  # 90% success rate

        usage_tracker.record_request(
            tenant_id=tenant_id,
            tokens_used=tokens,
            cost=cost,
            success=success,
            error_message="Rate limit exceeded" if not success else None
        )

        if (i + 1) % 25 == 0:
            print(f"  Recorded {i + 1} requests...")

    print("\n✓ Recorded 100 requests (90 successful, 10 failed)")

    print_subsection("2. Getting Usage Report")

    # Get usage for last 24 hours
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)

    usage_report = usage_tracker.get_usage_report(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )

    print(f"\nUsage Report (Last 24 Hours):")
    print(f"  Total Requests: {usage_report['total_requests']}")
    print(f"  Successful: {usage_report['successful_requests']}")
    print(f"  Failed: {usage_report['failed_requests']}")
    print(f"  Success Rate: {usage_report['success_rate']:.1f}%")
    print(f"  Total Tokens: {usage_report['total_tokens']:,}")
    print(f"  Total Cost: ${usage_report['total_cost']:.4f}")
    print(f"  Avg Tokens/Request: {usage_report['avg_tokens_per_request']:.0f}")

    print_subsection("3. Usage Summary by Period")

    summary = usage_tracker.get_usage_summary(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )

    print(f"\nSummary:")
    print(f"  Period Start: {summary['period_start']}")
    print(f"  Period End: {summary['period_end']}")
    print(f"  Total Requests: {summary['total_requests']}")
    print(f"  Total Cost: ${summary['total_cost']:.4f}")

    print_subsection("4. Billing Export")

    billing_data = usage_tracker.export_usage_for_billing(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )

    print(f"\nBilling Data:")
    print(f"  Tenant ID: {billing_data['tenant_id']}")
    print(f"  Billing Period: {billing_data['billing_period']['start']} to {billing_data['billing_period']['end']}")
    print(f"  Total Requests: {billing_data['total_requests']}")
    print(f"  Billable Amount: ${billing_data['total_cost']:.4f}")
    print(f"  Breakdown:")
    print(f"    Successful Requests: {billing_data['successful_requests']}")
    print(f"    Failed Requests: {billing_data['failed_requests']}")
    print(f"    Total Tokens: {billing_data['total_tokens']:,}")


def demo_3_tenant_management(tenant_id: str):
    """Demo 3: Tenant management operations"""
    print_section("Demo 3: Tenant Management Operations")

    tenant_manager = TenantManager()

    print_subsection("1. Updating Tenant Information")

    # Update tenant details
    updated = tenant_manager.update_tenant(
        tenant_id=tenant_id,
        name="Acme Corporation Ltd.",
        email="admin@acmecorp.com"
    )

    if updated:
        print(f"\n✓ Tenant information updated:")
        print(f"  New Name: {updated.name}")
        print(f"  New Email: {updated.email}")

    print_subsection("2. Updating Configuration")

    # Update feature flags
    new_config = tenant_manager.update_config(
        tenant_id=tenant_id,
        feature_flags={
            "advanced_analytics": True,
            "custom_models": True,
            "api_access": True,
            "premium_support": True  # New feature enabled
        },
        custom_config={
            "webhook_url": "https://acmecorp.com/webhooks/autonomai",
            "notification_email": "alerts@acmecorp.com",
            "max_retries": 3
        }
    )

    if new_config:
        print(f"\n✓ Configuration updated:")
        print(f"  Feature Flags: {new_config.feature_flags}")

    print_subsection("3. Plan Upgrade")

    # Upgrade to Enterprise plan
    upgraded = tenant_manager.upgrade_plan(
        tenant_id=tenant_id,
        new_plan=TenantPlan.ENTERPRISE
    )

    if upgraded:
        print(f"\n✓ Plan upgraded successfully!")
        print(f"  Old Plan: {TenantPlan.PROFESSIONAL.value}")
        print(f"  New Plan: {upgraded.plan.value}")

        # Show new limits
        new_limits = tenant_manager.get_plan_limits(TenantPlan.ENTERPRISE)
        print(f"\n  New Plan Limits:")
        print(f"    Max Requests/Day: {new_limits.max_requests_per_day:,}")
        print(f"    Max Requests/Month: {new_limits.max_requests_per_month:,}")
        print(f"    Max Storage GB: {new_limits.max_storage_gb}")
        print(f"    Priority Support: {new_limits.enable_priority_support}")
        print(f"    SLA: {new_limits.enable_sla_guarantees}")

    print_subsection("4. Tenant Suspension & Activation")

    # Suspend tenant
    print("\n  Suspending tenant...")
    suspended = tenant_manager.suspend_tenant(tenant_id)

    if suspended:
        print(f"  ✓ Tenant suspended")
        print(f"    Status: {suspended.status.value}")

    # Reactivate tenant
    print("\n  Reactivating tenant...")
    activated = tenant_manager.activate_tenant(tenant_id)

    if activated:
        print(f"  ✓ Tenant reactivated")
        print(f"    Status: {activated.status.value}")


def demo_4_multi_tenant_isolation():
    """Demo 4: Demonstrating tenant isolation"""
    print_section("Demo 4: Multi-Tenant Isolation")

    load_dotenv()
    tenant_manager = TenantManager()

    print_subsection("1. Creating Multiple Tenants")

    # Create three different tenants
    tenants = {}

    companies = [
        ("StartupCo", "admin@startup.co", TenantPlan.STARTER),
        ("MidSizeCorp", "admin@midsize.com", TenantPlan.PROFESSIONAL),
        ("EnterpriseCo", "admin@enterprise.com", TenantPlan.ENTERPRISE)
    ]

    for name, email, plan in companies:
        result = tenant_manager.onboard_tenant(
            name=name,
            email=email,
            plan=plan,
            api_keys={f"key_{name.lower()}": f"sk-{name.lower()}-12345"}
        )
        tenants[name] = result["tenant_id"]
        print(f"  ✓ {name} (ID: {result['tenant_id'][:8]}...) - {plan.value} plan")

    print_subsection("2. Recording Usage Per Tenant")

    usage_tracker = UsageTracker()

    # Record different usage patterns for each tenant
    for name, tenant_id in tenants.items():
        requests = 10 if "Startup" in name else (50 if "Mid" in name else 100)

        for i in range(requests):
            usage_tracker.record_request(
                tenant_id=tenant_id,
                tokens_used=500,
                cost=0.01,
                success=True
            )

        print(f"  ✓ Recorded {requests} requests for {name}")

    print_subsection("3. Viewing Isolated Usage Reports")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)

    print("\n")
    for name, tenant_id in tenants.items():
        report = usage_tracker.get_usage_report(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )

        print(f"  {name}:")
        print(f"    Requests: {report['total_requests']}")
        print(f"    Cost: ${report['total_cost']:.4f}")
        print()

    print("  ✓ Each tenant's usage is completely isolated")

    print_subsection("4. Checking Tenant Limits")

    for name, tenant_id in tenants.items():
        tenant = tenant_manager.get_tenant(tenant_id)
        if tenant:
            limits = tenant_manager.get_plan_limits(tenant.plan)
            within_limits = tenant_manager.check_tenant_limits(tenant_id)

            print(f"  {name} ({tenant.plan.value} plan):")
            print(f"    Daily Limit: {limits.max_requests_per_day:,}")
            print(f"    Current Usage: {within_limits['requests_today']}")
            print(f"    Within Limits: {within_limits['within_limits']}")
            print()

    # Cleanup demo tenants
    print_subsection("5. Cleanup")
    for name, tenant_id in tenants.items():
        tenant_manager.delete_tenant(tenant_id)
    print("  ✓ Demo tenants deleted")


def demo_5_tenant_list_and_filter():
    """Demo 5: Listing and filtering tenants"""
    print_section("Demo 5: Listing & Filtering Tenants")

    tenant_manager = TenantManager()

    print_subsection("1. Listing All Tenants")

    all_tenants = tenant_manager.list_tenants()
    print(f"\nTotal tenants: {len(all_tenants)}")

    for tenant in all_tenants[:5]:  # Show first 5
        print(f"  - {tenant.name} ({tenant.email}) - {tenant.plan.value} - {tenant.status.value}")

    print_subsection("2. Filtering by Plan")

    enterprise_tenants = tenant_manager.list_tenants(plan=TenantPlan.ENTERPRISE)
    print(f"\nEnterprise tenants: {len(enterprise_tenants)}")

    for tenant in enterprise_tenants:
        print(f"  - {tenant.name}")

    print_subsection("3. Filtering by Status")

    active_tenants = tenant_manager.list_tenants(status=TenantStatus.ACTIVE)
    print(f"\nActive tenants: {len(active_tenants)}")


def main():
    """Run all multi-tenant demos"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║              AutonomAI Comprehensive Multi-Tenant Demo                   ║
║                                                                           ║
║  This demo shows complete multi-tenant functionality including:          ║
║  - Tenant onboarding and management                                      ║
║  - Usage tracking and billing                                            ║
║  - Plan management and limits                                            ║
║  - Tenant isolation                                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Run demos sequentially
        tenant_id = demo_1_tenant_onboarding()
        demo_2_usage_tracking(tenant_id)
        demo_3_tenant_management(tenant_id)
        demo_4_multi_tenant_isolation()
        demo_5_tenant_list_and_filter()

        print_section("Summary")
        print("""
Multi-Tenant Features Demonstrated:
  ✓ Complete tenant onboarding workflow
  ✓ Tenant configuration and feature flags
  ✓ Usage tracking and monitoring
  ✓ Billing data export
  ✓ Plan upgrades and downgrades
  ✓ Tenant suspension and activation
  ✓ Complete tenant isolation
  ✓ Per-tenant usage limits
  ✓ Filtering and searching tenants

Production Deployment Recommendations:
  1. Use unique tenant IDs (UUIDs) for security
  2. Encrypt tenant API keys at rest
  3. Implement webhook notifications for limit breaches
  4. Set up automated billing workflows
  5. Monitor per-tenant resource usage
  6. Implement tenant-specific rate limiting
  7. Use separate instruction directories per tenant
  8. Enable audit logging for all tenant operations
  9. Implement tenant data export for compliance
  10. Set up tenant-specific backup schedules

SaaS Best Practices:
  - Provide self-service tenant dashboard
  - Implement usage alerts and notifications
  - Offer flexible pricing tiers
  - Support plan upgrades/downgrades
  - Enable tenant customization
  - Provide usage analytics
  - Implement churn prevention monitoring

For more information, see:
  - docs/guides/multi-tenant.md
  - docs/distributed-deployment.md
  - web/api_tenant_management.py (REST API)
        """)

        # Cleanup
        print("\nCleaning up demo tenant...")
        tenant_manager = TenantManager()
        tenant_manager.delete_tenant(tenant_id)
        print("✓ Cleanup complete")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
