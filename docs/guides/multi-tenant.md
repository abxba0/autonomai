# Multi-Tenant Support Documentation

## Overview

The AutonomAI system now includes production-ready multi-tenant support with complete tenant data isolation, usage tracking, and comprehensive management tools.

## Features

### 1. **Tenant Data Isolation**
- Strict separation at the database level with `tenant_id` foreign keys
- Isolated instruction files and configuration per tenant
- Separate audit logs and metrics per tenant
- No data leakage between tenants

### 2. **Tenant Plans & Limits**
Four subscription tiers with customizable limits:

- **FREE**: Basic tier for testing
  - 1,000 requests/day
  - 10,000 requests/month
  - 500K tokens/month
  - 1 user, 1 API key
  
- **STARTER**: Small teams
  - 5,000 requests/day
  - 100K requests/month
  - 3M tokens/month
  - 3 users, 3 API keys
  - Advanced optimization enabled
  
- **PROFESSIONAL**: Growing businesses
  - 20,000 requests/day
  - 500K requests/month
  - 15M tokens/month
  - 10 users, 10 API keys
  - All features enabled
  
- **ENTERPRISE**: Large organizations
  - 100,000 requests/day
  - 2M requests/month
  - 100M tokens/month
  - 50 users, 50 API keys
  - All features + extended retention

### 3. **Usage Tracking & Metering**
- Real-time usage tracking for requests, tokens, and costs
- Aggregated usage summaries by time period
- Billing-ready export functionality
- Cost estimation per model/provider
- Performance metrics (execution time)

### 4. **Tenant Configuration**
Each tenant can configure:
- API keys for AI providers (Anthropic, OpenAI, Google, Deepseek, Openrouter)
- Default models (main and critic)
- Feature flags (auto-optimization, multimodal, workflows, etc.)
- Custom validators

### 5. **Admin Tools**
Complete API for tenant management:
- Tenant CRUD operations
- Onboarding workflow
- Plan upgrades/downgrades
- Suspension/activation
- Soft/hard deletion
- Configuration management
- Usage monitoring
- Limit checking

## Architecture

### Data Models

#### Tenant
```python
@dataclass
class Tenant:
    tenant_id: str
    name: str
    email: str
    status: TenantStatus  # active, suspended, trial, pending, deleted
    plan: TenantPlan  # free, starter, professional, enterprise
    plan_limits: TenantPlanLimits
    created_at: datetime
    # ... additional fields
```

#### TenantConfig
```python
@dataclass
class TenantConfig:
    tenant_id: str
    # API Keys (encrypted in production)
    anthropic_api_key: Optional[str]
    openai_api_key: Optional[str]
    # Model preferences
    default_main_model: str
    default_critic_model: str
    # Feature flags
    enable_auto_optimization: bool
    enable_multimodal: bool
    # ... additional fields
```

#### UsageRecord
```python
@dataclass
class UsageRecord:
    usage_id: str
    tenant_id: str
    request_count: int
    tokens_used: int
    input_tokens: int
    output_tokens: int
    estimated_cost_cents: float
    # ... additional fields
```

### Database Schema

All tables include `tenant_id` with indexes:
- `tenants` - Tenant master data
- `tenant_configs` - Tenant-specific configuration
- `usage_records` - Usage tracking (indexed by tenant_id + timestamp)
- `failure_entries` - Failures isolated by tenant
- `version_metadata` - Instruction versions per tenant
- `instruction_versions` - Version content per tenant

### Components

#### TenantManager
Handles tenant lifecycle operations:
```python
from src.storage import TenantManager

# Create tenant
tenant = tenant_manager.create_tenant(
    name="Acme Corp",
    email="admin@acme.com",
    plan=TenantPlan.PROFESSIONAL
)

# Onboard tenant with API keys
result = tenant_manager.onboard_tenant(
    name="Acme Corp",
    email="admin@acme.com",
    plan=TenantPlan.PROFESSIONAL,
    api_keys={"anthropic_api_key": "sk-..."}
)

# Check limits
limits = tenant_manager.check_tenant_limits(tenant_id)
if not limits["can_proceed"]:
    print(f"Limits exceeded: {limits['exceeded']}")
```

#### UsageTracker
Tracks and reports usage:
```python
from src.storage import UsageTracker

# Record request
usage_tracker.record_request(
    tenant_id="tenant_abc123",
    tokens_used=1000,
    input_tokens=400,
    output_tokens=600,
    success=True,
    model_used="claude-3-sonnet"
)

# Get usage report
report = usage_tracker.get_usage_report(
    tenant_id="tenant_abc123",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Export for billing
billing_data = usage_tracker.export_usage_for_billing(
    tenant_id="tenant_abc123",
    start_date=period_start,
    end_date=period_end
)
```

#### TenantContextMiddleware
Automatically extracts and validates tenant context:
```python
from fastapi import FastAPI
from src.core.tenant_context import TenantContextMiddleware
from src.storage import DatabaseManager, TenantManager, UsageTracker

app = FastAPI()

# Add middleware
app.add_middleware(
    TenantContextMiddleware,
    db_manager=db_manager,
    tenant_manager=tenant_manager,
    usage_tracker=usage_tracker,
    require_tenant=True
)

# Use in endpoints
@app.get("/api/data")
async def get_data(tenant_id: str = Depends(get_tenant_id)):
    # tenant_id automatically extracted from request
    return {"tenant_id": tenant_id, "data": [...]}
```

## API Endpoints

### Tenant Management API
Run on port 8001 (separate from main API):
```bash
python web/api_tenant_management.py
```

#### Create Tenant
```http
POST /tenants
Authorization: Bearer <admin_token>

{
    "name": "Acme Corp",
    "email": "admin@acme.com",
    "plan": "professional",
    "company": "Acme Corporation",
    "trial_days": 14
}
```

#### Onboard Tenant
```http
POST /tenants/onboard
Authorization: Bearer <admin_token>

{
    "name": "Acme Corp",
    "email": "admin@acme.com",
    "plan": "professional",
    "anthropic_api_key": "sk-...",
    "openai_api_key": "sk-..."
}
```

#### Get Tenant
```http
GET /tenants/{tenant_id}
Authorization: Bearer <admin_token>
```

#### List Tenants
```http
GET /tenants?status=active&plan=professional
Authorization: Bearer <admin_token>
```

#### Update Tenant
```http
PUT /tenants/{tenant_id}
Authorization: Bearer <admin_token>

{
    "name": "Acme Corporation",
    "company": "Acme Corp Inc.",
    "notes": "VIP customer"
}
```

#### Suspend/Activate Tenant
```http
POST /tenants/{tenant_id}/suspend
POST /tenants/{tenant_id}/activate
Authorization: Bearer <admin_token>
```

#### Get Configuration
```http
GET /tenants/{tenant_id}/config
Authorization: Bearer <admin_token>
```

#### Update Configuration
```http
PUT /tenants/{tenant_id}/config
Authorization: Bearer <admin_token>

{
    "anthropic_api_key": "sk-...",
    "enable_multimodal": true
}
```

#### Upgrade Plan
```http
POST /tenants/{tenant_id}/upgrade
Authorization: Bearer <admin_token>

{
    "new_plan": "enterprise"
}
```

#### Get Usage
```http
GET /tenants/{tenant_id}/usage?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <admin_token>
```

#### Export for Billing
```http
GET /tenants/{tenant_id}/usage/billing?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <admin_token>
```

#### Check Limits
```http
GET /tenants/{tenant_id}/limits
Authorization: Bearer <admin_token>
```

## Usage Examples

### Complete Onboarding Flow

```python
from src.models.config import SystemConfig
from src.storage import DatabaseManager, TenantManager

# Initialize
config = SystemConfig()
db_manager = DatabaseManager(config)
tenant_manager = TenantManager(db_manager)

# Onboard new tenant
result = tenant_manager.onboard_tenant(
    name="Acme Corporation",
    email="admin@acme.com",
    plan=TenantPlan.PROFESSIONAL,
    company="Acme Corp",
    api_keys={
        "anthropic_api_key": "sk-ant-...",
        "openai_api_key": "sk-..."
    }
)

if result["success"]:
    tenant_id = result["tenant_id"]
    print(f"Tenant created: {tenant_id}")
    
    # Create directory structure
    tenant_manager.create_tenant_directory_structure(
        tenant_id,
        Path("/data/tenants")
    )
```

### Usage Tracking in API

```python
from fastapi import FastAPI, Depends
from src.core.tenant_context import get_tenant_id, TenantContextMiddleware

app = FastAPI()

# Add middleware (automatically tracks usage)
app.add_middleware(TenantContextMiddleware, ...)

@app.post("/api/generate")
async def generate_text(
    prompt: str,
    tenant_id: str = Depends(get_tenant_id)
):
    # Tenant context automatically validated
    # Usage automatically recorded by middleware
    
    # Your business logic here
    result = await generate_response(prompt, tenant_id)
    
    return {"result": result}
```

### Manual Usage Recording

```python
from src.storage import UsageTracker
import time

usage_tracker = UsageTracker(db_manager)

start_time = time.time()

# Process request
result = process_request(tenant_id, query)

execution_time = (time.time() - start_time) * 1000

# Record usage
usage_tracker.record_request(
    tenant_id=tenant_id,
    tokens_used=result["tokens_used"],
    input_tokens=result["input_tokens"],
    output_tokens=result["output_tokens"],
    success=True,
    execution_time_ms=execution_time,
    model_used="claude-3-sonnet",
    provider_used="anthropic",
    endpoint="/api/generate",
    operation_type="POST"
)
```

## Security Considerations

### 1. **API Key Storage**
- In production, encrypt API keys at rest
- Use environment variables or secrets manager
- Never log API keys
- Mask keys in API responses (show last 4 characters only)

### 2. **Authentication**
- Admin endpoints require admin role
- Use JWT tokens with proper expiration
- Implement API key rotation
- Audit all admin actions

### 3. **Data Isolation**
- All queries filtered by tenant_id
- Foreign key constraints prevent cross-tenant access
- Separate directory structures per tenant
- Tenant-specific logs and metrics

### 4. **Rate Limiting**
- Plan-based rate limits enforced
- Per-tenant request tracking
- Automatic limit checking before processing
- Graceful degradation when limits exceeded

### 5. **Audit Logging**
- All tenant operations logged
- Tenant creation, updates, deletions tracked
- Configuration changes audited
- Suspension/activation logged with reasons

## Testing

Run the comprehensive test suite:

```bash
# All tests
pytest tests/test_multi_tenant.py -v

# Specific test classes
pytest tests/test_multi_tenant.py::TestTenantModels -v
pytest tests/test_multi_tenant.py::TestDatabaseIntegration -v
pytest tests/test_multi_tenant.py::TestTenantManager -v
pytest tests/test_multi_tenant.py::TestUsageTracker -v
```

## Migration Guide

### From Single-Tenant to Multi-Tenant

1. **Update Database**
   ```python
   # Database automatically creates tables on first run
   from src.storage import DatabaseManager
   db = DatabaseManager(config)
   ```

2. **Create Default Tenant**
   ```python
   from src.models.tenant import Tenant, TenantPlan
   
   default_tenant = Tenant(
       tenant_id="default",
       name="Default",
       email="admin@example.com",
       plan=TenantPlan.ENTERPRISE
   )
   db_manager.create_tenant(default_tenant)
   ```

3. **Migrate Existing Data**
   ```python
   # Update existing records to default tenant
   # This is handled automatically by default tenant_id="default"
   ```

4. **Add Middleware**
   ```python
   app.add_middleware(
       TenantContextMiddleware,
       db_manager=db_manager,
       tenant_manager=tenant_manager,
       usage_tracker=usage_tracker,
       default_tenant_id="default"
   )
   ```

## Performance Considerations

### Database Indexes
All tenant-related queries are optimized with indexes:
- `tenant_id` on all tables
- Composite indexes on `(tenant_id, timestamp)` for usage queries
- Foreign key indexes for referential integrity

### Caching
Consider caching:
- Tenant configurations
- Plan limits
- Usage summaries (with TTL)

### Monitoring
Monitor:
- Database query performance per tenant
- Storage usage per tenant
- Request patterns per tenant
- Cost per tenant

## Future Enhancements

1. **Multi-region Support**
   - Tenant data residency options
   - Regional failover
   - Cross-region replication

2. **Advanced Billing**
   - Invoice generation
   - Payment integration
   - Usage alerts and notifications

3. **Self-Service Portal**
   - Tenant dashboard
   - Usage visualization
   - Plan management UI

4. **Advanced Analytics**
   - Tenant behavior analysis
   - Cost optimization recommendations
   - Predictive capacity planning

## Support

For issues or questions:
- Check the test suite for usage examples
- Review API endpoint documentation
- Open an issue on GitHub
