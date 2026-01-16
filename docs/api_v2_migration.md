# API v2 Migration Guide

## Overview

API v2 introduces several advanced features to the Self-Optimizing Instruction Library:

- **GraphQL**: Advanced queries and mutations for complex data fetching
- **WebSockets**: Real-time updates for workflow status, job completion, and system events
- **Webhooks**: Event-driven notifications for integration with external systems
- **API Versioning**: Clear versioning scheme with deprecation warnings

## What's New in v2

### 1. GraphQL Endpoint

GraphQL provides a more flexible way to query and mutate data compared to REST APIs.

**Endpoint**: `/v2/graphql`

**Example Query**:
```graphql
query {
  status {
    totalFailures
    totalOptimizations
    currentVersion
    systemHealth
  }
  versions {
    versionId
    timestamp
    triggerType
    rulesAdded
  }
}
```

**Example Mutation**:
```graphql
mutation {
  execute(input: {
    query: "Explain quantum computing"
  }) {
    output
    validationPassed
    optimizationAttempted
  }
}
```

**Register a Webhook**:
```graphql
mutation {
  registerWebhook(input: {
    url: "https://your-domain.com/webhook"
    events: ["job_finished", "optimization_completed"]
  }) {
    id
    url
    events
    active
  }
}
```

### 2. WebSocket Support

Real-time updates via WebSocket connections.

**Endpoints**:
- `/v2/ws` - General updates
- `/v2/ws/workflows` - Workflow-specific updates
- `/v2/ws/jobs` - Job-specific updates

**Connection Example** (JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8000/v2/ws/jobs');

ws.onopen = () => {
  console.log('Connected to WebSocket');
  
  // Subscribe to a channel
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'jobs'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  if (data.type === 'job_completed') {
    console.log(`Job ${data.job_id} completed: ${data.success}`);
  }
};
```

**Event Types**:
- `workflow_update` - Workflow status changed
- `job_completed` - Job finished execution
- `optimization_completed` - System optimization completed
- `regression_detected` - Performance regression detected

**Commands**:
```javascript
// Subscribe to channel
ws.send(JSON.stringify({ type: 'subscribe', channel: 'workflows' }));

// Unsubscribe from channel
ws.send(JSON.stringify({ type: 'unsubscribe', channel: 'workflows' }));

// Ping/pong for keepalive
ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
```

### 3. Webhook System

Register webhooks to receive HTTP POST notifications for events.

**Register a Webhook**:
```bash
curl -X POST http://localhost:8000/v2/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook",
    "events": ["job_finished", "optimization_completed", "regression_detected"],
    "secret": "your-webhook-secret"
  }'
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://your-domain.com/webhook",
  "events": ["job_finished", "optimization_completed", "regression_detected"],
  "created_at": "2026-01-16T10:30:00Z",
  "active": true
}
```

**List Webhooks**:
```bash
curl http://localhost:8000/v2/webhooks
```

**Unregister a Webhook**:
```bash
curl -X DELETE http://localhost:8000/v2/webhooks/{webhook_id}
```

**Webhook Payload**:
```json
{
  "event": "job_finished",
  "data": {
    "query": "Explain quantum computing",
    "validation_passed": true,
    "optimization_attempted": false
  },
  "timestamp": "2026-01-16T10:30:00Z",
  "webhook_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Webhook Signature Verification**:

If you provided a secret during webhook registration, each request includes an `X-Webhook-Signature` header containing an HMAC-SHA256 signature:

```python
import hmac
import hashlib

def verify_webhook_signature(payload_bytes, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

# In your webhook handler
@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    
    if not verify_webhook_signature(payload, signature, YOUR_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook...
```

**Available Events**:
- `job_finished` - Execution completed
- `optimization_completed` - System optimization finished
- `regression_detected` - Performance regression detected

**Webhook Retry Logic**:
- Failed deliveries are retried up to 3 times
- Exponential backoff between retries (1s, 2s, 4s)
- Webhooks are automatically deactivated after 3 consecutive failures
- Can be manually reactivated via `/v2/webhooks/{id}/activate`

### 4. API Versioning

Clear versioning with deprecation warnings.

**Version Paths**:
- `/v1/*` - Legacy API (deprecated)
- `/v2/*` - Current API

**Deprecation Headers**:

When calling deprecated v1 endpoints, you'll receive:
```
X-API-Deprecated: true
X-API-Sunset: 2026-06-01
X-API-Migration: Please migrate to /v2/ endpoints
```

**Version Information**:
```bash
curl http://localhost:8000/
```

Response:
```json
{
  "message": "Self-Optimizing Instruction Library API",
  "current_version": "v2",
  "deprecated_versions": ["v1"],
  "available_versions": {
    "v1": {
      "path": "/v1",
      "status": "deprecated",
      "sunset_date": "2026-06-01",
      "docs": "/v1/docs"
    },
    "v2": {
      "path": "/v2",
      "status": "current",
      "docs": "/v2/docs",
      "features": ["graphql", "websockets", "webhooks"]
    }
  },
  "migration_guide": "/docs/v2-migration"
}
```

## Migration from v1 to v2

### REST Endpoints

Most v1 endpoints have equivalent v2 versions:

| v1 Endpoint | v2 Endpoint | Changes |
|-------------|-------------|---------|
| `/v1/execute` | `/v2/execute` | Sends webhook events |
| `/v1/feedback` | `/v2/feedback` | Sends webhook events |
| `/v1/status` | `/v2/status` | No changes |
| `/v1/versions` | `/v2/versions` | No changes |

### Breaking Changes

**None** - v2 is backward compatible with v1 for existing REST endpoints.

### New Features (v2 only)

1. GraphQL endpoint at `/v2/graphql`
2. WebSocket endpoints at `/v2/ws/*`
3. Webhook management at `/v2/webhooks`
4. Enhanced event notifications

### Migration Steps

1. **Update Base URL**: Change from `/v1/` to `/v2/`
2. **Optional - Add Webhook**: Register webhooks for event notifications
3. **Optional - Use GraphQL**: Migrate to GraphQL for complex queries
4. **Optional - Use WebSockets**: Connect to WebSocket for real-time updates

### Example Migration

**Before (v1)**:
```python
import requests

# Execute query
response = requests.post(
    "http://localhost:8000/v1/execute",
    json={"query": "Explain AI"}
)
```

**After (v2 with webhooks)**:
```python
import requests

# Register webhook first
webhook_response = requests.post(
    "http://localhost:8000/v2/webhooks",
    json={
        "url": "https://your-domain.com/webhook",
        "events": ["job_finished"]
    }
)

# Execute query (webhook will be notified on completion)
response = requests.post(
    "http://localhost:8000/v2/execute",
    json={"query": "Explain AI"}
)
```

## Python Client Examples

### Using REST API

```python
import requests

base_url = "http://localhost:8000/v2"

# Execute query
response = requests.post(
    f"{base_url}/execute",
    json={
        "query": "Explain machine learning",
        "conversation_context": []
    }
)
result = response.json()
print(f"Output: {result['output']}")
```

### Using GraphQL

```python
import requests

graphql_url = "http://localhost:8000/v2/graphql"

query = """
query {
  status {
    totalFailures
    totalOptimizations
    systemHealth
  }
}
"""

response = requests.post(graphql_url, json={"query": query})
data = response.json()
print(data["data"]["status"])
```

### Using WebSocket

```python
import asyncio
import websockets
import json

async def listen_for_updates():
    uri = "ws://localhost:8000/v2/ws/jobs"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to jobs channel
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channel": "jobs"
        }))
        
        # Listen for updates
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(listen_for_updates())
```

### Managing Webhooks

```python
import requests

base_url = "http://localhost:8000/v2"

# Register webhook
webhook = requests.post(
    f"{base_url}/webhooks",
    json={
        "url": "https://your-domain.com/webhook",
        "events": ["job_finished", "optimization_completed"],
        "secret": "my-secret-key"
    }
).json()

webhook_id = webhook["id"]
print(f"Registered webhook: {webhook_id}")

# List webhooks
webhooks = requests.get(f"{base_url}/webhooks").json()
print(f"Total webhooks: {len(webhooks)}")

# Deactivate webhook
requests.post(f"{base_url}/webhooks/{webhook_id}/deactivate")

# Reactivate webhook
requests.post(f"{base_url}/webhooks/{webhook_id}/activate")

# Unregister webhook
requests.delete(f"{base_url}/webhooks/{webhook_id}")
```

## JavaScript/TypeScript Client Examples

### Using REST API

```typescript
// Execute query
const response = await fetch('http://localhost:8000/v2/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Explain machine learning'
  })
});

const result = await response.json();
console.log('Output:', result.output);
```

### Using GraphQL

```typescript
const query = `
  query {
    status {
      totalFailures
      totalOptimizations
      systemHealth
    }
  }
`;

const response = await fetch('http://localhost:8000/v2/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query })
});

const data = await response.json();
console.log('Status:', data.data.status);
```

### Using WebSocket

```typescript
const ws = new WebSocket('ws://localhost:8000/v2/ws/jobs');

ws.onopen = () => {
  // Subscribe to jobs channel
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'jobs'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'job_completed') {
    console.log(`Job ${data.job_id} completed`);
  }
};
```

## Best Practices

1. **Use WebSockets for Real-Time Updates**: For monitoring dashboards or real-time applications
2. **Use Webhooks for Integration**: For event-driven workflows and system integration
3. **Use GraphQL for Complex Queries**: When you need to fetch multiple related resources efficiently
4. **Use REST for Simple Operations**: For basic CRUD operations and simple queries

## Support Timeline

- **v1**: Deprecated as of 2026-01-16, sunset date 2026-06-01
- **v2**: Current version, full support

## Additional Resources

- [Interactive API Docs (Swagger)]: http://localhost:8000/v2/docs
- [GraphQL Playground]: http://localhost:8000/v2/graphql
- [GitHub Repository]: https://github.com/abxba0/autonomai
- [Issue Tracker]: https://github.com/abxba0/autonomai/issues
