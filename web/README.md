# Advanced API Features

This directory contains the implementation of advanced API features for the AutonomAI system.

## Features

### 1. GraphQL API (`graphql_schema.py`)

Provides a GraphQL endpoint for flexible data queries and mutations.

**Key Components:**
- Type definitions for all data models
- Query resolvers for fetching data
- Mutation resolvers for operations
- Full schema with introspection support

**Available Operations:**
- Query: `status`, `versions`, `webhooks`
- Mutations: `execute`, `provideFeedback`, `registerWebhook`, `unregisterWebhook`, `rollback`

### 2. WebSocket Support (`websocket_handlers.py`)

Real-time bidirectional communication for live updates.

**Key Components:**
- Connection manager for WebSocket lifecycle
- Channel-based subscriptions
- Broadcast and targeted messaging
- Notification helpers for common events

**Supported Events:**
- `workflow_update` - Workflow status changes
- `job_completed` - Job execution completion
- `optimization_completed` - System optimization finished
- `regression_detected` - Performance regression alerts

### 3. Webhook System (`webhook_manager.py`)

Event-driven HTTP POST notifications for system integration.

**Key Components:**
- Webhook registration and management
- Event queue and delivery system
- Retry logic with exponential backoff
- HMAC signature verification
- Automatic webhook deactivation on failure

**Supported Events:**
- `job_finished` - Execution completed
- `optimization_completed` - System improved
- `regression_detected` - Performance issue detected

### 4. API Versioning (`api_v2.py`)

Clear versioning scheme with deprecation support.

**Features:**
- URL-based versioning (`/v1/`, `/v2/`)
- Deprecation headers for old versions
- Version information endpoint
- Migration guide support

## Installation

### Requirements

```bash
pip install -r requirements/web.txt
```

Additional dependencies:
- `strawberry-graphql>=0.219.0` - GraphQL implementation
- `websockets>=12.0` - WebSocket support
- `httpx>=0.25.0` - Async HTTP client for webhooks

### Running the API

```bash
# Start the API v2 server
python web/api_v2.py

# Or with custom host/port
HOST=0.0.0.0 PORT=8000 python web/api_v2.py
```

The server will start with:
- REST API at: `http://localhost:8000/v2/`
- GraphQL at: `http://localhost:8000/v2/graphql`
- WebSocket at: `ws://localhost:8000/v2/ws`

## Usage Examples

See `examples/api_v2_demo.py` for comprehensive examples of:
- REST API calls
- GraphQL queries and mutations
- WebSocket connections
- Webhook registration and management

### Quick Start - REST API

```python
import requests

# Execute a query
response = requests.post(
    "http://localhost:8000/v2/execute",
    json={"query": "Explain AI"}
)
result = response.json()
print(result["output"])
```

### Quick Start - GraphQL

```python
import requests

query = """
query {
  status {
    systemHealth
    totalOptimizations
  }
}
"""

response = requests.post(
    "http://localhost:8000/v2/graphql",
    json={"query": query}
)
data = response.json()
print(data["data"]["status"])
```

### Quick Start - WebSocket

```python
import asyncio
import websockets
import json

async def listen():
    uri = "ws://localhost:8000/v2/ws/jobs"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "subscribe", "channel": "jobs"}))
        async for message in ws:
            print(json.loads(message))

asyncio.run(listen())
```

### 4. Batch Processing API (`api_batch.py`, `batch_routes.py`) ✨ NEW

Production-ready async job queuing with Celery for batch operations.

**Key Components:**
- Celery task queue with Redis backend
- Batch job models with progress tracking
- REST API endpoints for job management
- Parallel workflow execution
- Fault tolerance and retry logic
- Multi-worker support

**Supported Batch Types:**
- `failure_optimization` - Optimize multiple failures
- `workflow_batch` - Execute multiple workflows
- `validation_batch` - Validate multiple outputs
- `custom` - Custom batch processing

**API Endpoints:**
- `POST /v2/batch/submit` - Submit batch jobs
- `GET /v2/batch/{job_id}/status` - Get job status
- `GET /v2/batch/{job_id}/results` - Get job results
- `POST /v2/batch/{job_id}/cancel` - Cancel jobs
- `GET /v2/batch/jobs` - List all jobs
- `GET /v2/batch/stats` - Get statistics

### Quick Start - Batch Processing ✨ NEW

**Prerequisites:**
```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Start Celery worker
celery -A src.batch.celery_config worker --loglevel=info

# Start API
python web/api_v2.py
```

**Submit batch job:**
```python
import requests

response = requests.post(
    "http://localhost:8000/v2/batch/submit",
    json={
        "job_type": "failure_optimization",
        "tasks": [
            {"failure_description": "Output too short", "severity": "high"},
            {"failure_description": "Missing fields", "severity": "high"},
        ],
        "max_workers": 4,
        "priority": 1,
    }
)
job = response.json()
print(f"Job ID: {job['job_id']}")
```

**Monitor progress:**
```python
# Get job status
response = requests.get(f"http://localhost:8000/v2/batch/{job_id}/status")
status = response.json()

print(f"Status: {status['status']}")
print(f"Progress: {status['progress']['progress_percent']:.1f}%")
print(f"Completed: {status['progress']['completed_tasks']}/{status['progress']['total_tasks']}")
```

**Get results:**
```python
response = requests.get(f"http://localhost:8000/v2/batch/{job_id}/results")
results = response.json()

for result in results['results']:
    print(f"Task {result['task_id']}: {'✓' if result['success'] else '✗'}")
```

See [docs/batch-processing.md](../docs/batch-processing.md) for complete documentation.

### Quick Start - Webhooks

```python
import requests

# Register webhook
response = requests.post(
    "http://localhost:8000/v2/webhooks",
    json={
        "url": "https://example.com/webhook",
        "events": ["job_finished"],
        "secret": "my-secret"
    }
)
webhook = response.json()
print(f"Webhook ID: {webhook['id']}")
```

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────┐
│         API v2 (FastAPI App)            │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐            │
│  │   REST   │  │ GraphQL  │            │
│  │Endpoints │  │ Endpoint │            │
│  └────┬─────┘  └────┬─────┘            │
│       │             │                   │
│       └─────┬───────┘                   │
│             │                           │
│  ┌──────────▼──────────┐               │
│  │  Core System Logic  │               │
│  └──────────┬──────────┘               │
│             │                           │
│       ┌─────┴─────┬────────────┐       │
│       │           │            │       │
│  ┌────▼────┐ ┌───▼───┐  ┌────▼─────┐ │
│  │WebSocket│ │Webhook│  │ Version  │ │
│  │ Manager │ │Manager│  │ Control  │ │
│  └─────────┘ └───────┘  └──────────┘ │
└─────────────────────────────────────────┘
```

### Event Flow

```
User Request
    │
    ▼
API Endpoint (REST/GraphQL)
    │
    ▼
Execute Operation
    │
    ├──► Webhook Manager ──► External Services
    │
    └──► WebSocket Manager ──► Connected Clients
```

## Testing

Run tests with pytest:

```bash
pytest tests/test_advanced_api.py -v
```

Test coverage:
- Webhook registration and management
- WebSocket connection handling
- GraphQL schema validation
- API versioning headers
- Event triggering and delivery

## Security Considerations

### Webhook Signatures

Webhooks include HMAC-SHA256 signatures for verification:

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### WebSocket Authentication

For production, implement authentication:

```python
from fastapi import WebSocket, HTTPException

async def verify_websocket_token(websocket: WebSocket):
    # Implement your authentication logic
    token = websocket.query_params.get("token")
    if not is_valid_token(token):
        await websocket.close(code=1008)
        return False
    return True
```

### Rate Limiting

Consider adding rate limiting for production:

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/execute", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def execute(...):
    ...
```

## Configuration

### Environment Variables

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Model configuration
MAIN_MODEL=claude-3-5-sonnet-20241022
CRITIC_MODEL=claude-3-haiku-20240307

# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Webhook Configuration

Webhooks can be configured with:
- `retry_count`: Number of retry attempts (default: 3)
- `timeout`: Request timeout in seconds (default: 30)
- `secret`: HMAC secret for signature verification

## Monitoring

### Health Check

```bash
curl http://localhost:8000/v2/health
```

Response:
```json
{
  "status": "healthy",
  "service": "self-optimizing-system",
  "version": "2.0.0",
  "features": {
    "graphql": true,
    "websockets": true,
    "webhooks": true,
    "versioning": true
  }
}
```

### Metrics

For production monitoring, consider integrating:
- Prometheus metrics export
- Application Performance Monitoring (APM)
- Log aggregation (ELK stack)
- Error tracking (Sentry)

## Migration from v1

See API documentation in [`docs/guides/api-reference.md`](../docs/api-reference.md) for complete details.

**Key Changes:**
- v1 endpoints deprecated (sunset: 2026-06-01)
- All v1 functionality available in v2
- New features only in v2 (GraphQL, WebSockets, Webhooks)

## Contributing

When adding new features:

1. Update the schema in `graphql_schema.py`
2. Add WebSocket notifications in `websocket_handlers.py`
3. Add webhook events in `webhook_manager.py`
4. Update version endpoints in `api_v2.py`
5. Add tests in `tests/test_advanced_api.py`
6. Update documentation

## Troubleshooting

### WebSocket Connection Issues

```python
# Check if WebSocket is accessible
import websockets

async def test_connection():
    try:
        async with websockets.connect("ws://localhost:8000/v2/ws") as ws:
            print("Connected successfully")
    except Exception as e:
        print(f"Connection failed: {e}")
```

### Webhook Delivery Failures

Check webhook manager logs:
```python
import logging
logging.getLogger("web.webhook_manager").setLevel(logging.DEBUG)
```

Common issues:
- Invalid URL
- Network timeout
- SSL certificate issues
- Rate limiting at destination

### GraphQL Schema Issues

Validate schema:
```bash
curl http://localhost:8000/v2/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}'
```

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: https://github.com/abxba0/autonomai/issues
- Documentation: `/docs/guides/api-reference.md`
- Examples: `/examples/api_v2_demo.py`
