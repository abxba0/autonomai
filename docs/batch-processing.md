# Batch Processing & Progress Monitoring

This document describes the batch processing capabilities with async job queuing, progress monitoring, and result retrieval.

## Overview

The batch processing system provides:

- **Async Job Queuing**: Celery-based task queue with Redis backend
- **Progress Monitoring**: Real-time progress tracking with estimated completion times
- **Parallel Execution**: Process multiple tasks simultaneously with configurable workers
- **Fault Tolerance**: Automatic retry logic and error handling
- **Multi-Worker Support**: Distributed processing across multiple workers
- **Workflow Batch Operations**: Execute multiple workflows in parallel

## Architecture

### Components

1. **BatchProcessor**: High-level interface for job management
2. **Celery Tasks**: Async task processing with parallelism
3. **BatchJob Models**: Data structures for job tracking
4. **API Endpoints**: REST API for job submission and monitoring
5. **WorkflowOrchestrator Extensions**: Batch workflow execution

### Technology Stack

- **Celery 5.3+**: Distributed task queue
- **Redis**: Message broker and result backend
- **Flower**: Web-based monitoring (optional)
- **FastAPI**: REST API for job management

## Installation

### Install Dependencies

```bash
# Install with web extras (includes Celery and Redis)
pip install -e ".[web]"

# Or install manually
pip install celery>=5.3.0 flower>=2.0.0 redis>=4.0.0
```

### Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally
# macOS: brew install redis && redis-server
# Ubuntu: sudo apt install redis-server && redis-server
```

### Start Celery Worker

```bash
# Start worker
celery -A src.batch.celery_config worker --loglevel=info

# With multiple workers
celery -A src.batch.celery_config worker --loglevel=info --concurrency=4

# Start Flower for monitoring (optional)
celery -A src.batch.celery_config flower
# Access at http://localhost:5555
```

## Usage

### 1. Batch Job Submission

#### Using BatchProcessor

```python
from src.batch import BatchProcessor, BatchJobType
from pathlib import Path

# Initialize processor
processor = BatchProcessor(storage_path=Path("./data/batch_jobs"))

# Prepare tasks
failures = [
    {
        "trigger_type": "validation_failure",
        "failure_description": "Output was too short",
        "user_query": "Summarize the article",
        "last_model_output": "OK",
        "severity": "high",
    },
    {
        "trigger_type": "validation_failure",
        "failure_description": "Missing required JSON fields",
        "user_query": "Generate user profile",
        "last_model_output": '{"name": "John"}',
        "severity": "high",
    },
]

# Submit batch job
job = processor.submit_batch_job(
    job_type=BatchJobType.FAILURE_OPTIMIZATION,
    tasks=failures,
    created_by="user123",
    priority=1,
    max_workers=4,
    retry_failed=True,
    max_retries=3,
)

print(f"Job submitted: {job.job_id}")
```

#### Using API

```bash
# Start API server
python web/api_batch.py --port 8001

# Submit job via API
curl -X POST http://localhost:8001/batch/submit \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "failure_optimization",
    "tasks": [
      {
        "failure_description": "Output too short",
        "severity": "high"
      }
    ],
    "max_workers": 4,
    "priority": 1
  }'
```

### 2. Progress Monitoring

#### Check Job Status

```python
# Get job status
status = processor.get_job_status(job.job_id)

print(f"Status: {status['status']}")
print(f"Progress: {status['progress']['progress_percent']:.1f}%")
print(f"Completed: {status['progress']['completed_tasks']}/{status['progress']['total_tasks']}")
print(f"Failed: {status['progress']['failed_tasks']}")
```

#### Via API

```bash
# Get job status
curl http://localhost:8001/batch/{job_id}/status

# Response
{
  "job_id": "abc123",
  "job_type": "failure_optimization",
  "status": "running",
  "progress": {
    "total_tasks": 10,
    "completed_tasks": 5,
    "failed_tasks": 1,
    "running_tasks": 2,
    "pending_tasks": 2,
    "progress_percent": 60.0,
    "estimated_time_remaining_seconds": 30.5
  }
}
```

### 3. Result Retrieval

```python
# Get job results
results = processor.get_job_results(job.job_id)

print(f"Job status: {results['status']}")
for result in results['results']:
    print(f"Task {result['task_id']}: {'✓' if result['success'] else '✗'}")
    if result['error']:
        print(f"  Error: {result['error']}")
    if result['result']:
        print(f"  Result: {result['result']}")
```

#### Via API

```bash
curl http://localhost:8001/batch/{job_id}/results
```

### 4. Batch Workflow Execution

#### Sequential Workflows with Shared Context

```python
from src.core.workflow_orchestrator import WorkflowOrchestrator
from src.models.config import SystemConfig

config = SystemConfig()
orchestrator = WorkflowOrchestrator(config)

workflows = [
    {"goal": "Analyze sales data", "context": {"period": "Q1"}},
    {"goal": "Generate report", "context": {"format": "pdf"}},
]

# Execute with shared context
result = orchestrator.execute_workflows_with_shared_context(
    workflows=workflows,
    shared_context={"company": "Acme Corp"},
    max_parallel=2,
    max_retries=3,
)

print(f"Successful: {result['successful']}/{result['total']}")
print(f"Shared context: {result['shared_context']}")
```

#### Parallel Workflows

```python
# Execute workflows in parallel
results = orchestrator.execute_workflows_batch(
    workflows=workflows,
    max_parallel=4,
    max_retries=3,
)

for i, result in enumerate(results):
    print(f"Workflow {i+1}: {'✓' if result['success'] else '✗'}")
```

### 5. Job Management

#### List Jobs

```python
# List all jobs
jobs = processor.list_jobs(limit=100)

# Filter by status
running_jobs = processor.list_jobs(
    status=BatchJobStatus.RUNNING,
    limit=50,
)

# Filter by type
workflow_jobs = processor.list_jobs(
    job_type=BatchJobType.WORKFLOW_BATCH,
    limit=50,
)
```

#### Cancel Job

```python
# Cancel a running job
success = processor.cancel_job(job.job_id)
if success:
    print("Job cancelled successfully")
```

#### Via API

```bash
# List jobs
curl "http://localhost:8001/batch/jobs?status=running&limit=10"

# Cancel job
curl -X POST http://localhost:8001/batch/{job_id}/cancel
```

## Batch Job Types

### 1. Failure Optimization

Optimize multiple failures in batch:

```python
job = processor.submit_batch_job(
    job_type=BatchJobType.FAILURE_OPTIMIZATION,
    tasks=[
        {
            "trigger_type": "validation_failure",
            "failure_description": "Output too short",
            "user_query": "Summarize article",
            "last_model_output": "OK",
            "severity": "high",
        }
    ],
    max_workers=4,
)
```

### 2. Workflow Batch

Execute multiple workflows:

```python
job = processor.submit_batch_job(
    job_type=BatchJobType.WORKFLOW_BATCH,
    tasks=[
        {
            "goal": "Research AI trends",
            "context": {"output_format": "summary"},
        }
    ],
    max_workers=2,
)
```

### 3. Validation Batch

Validate multiple outputs:

```python
job = processor.submit_batch_job(
    job_type=BatchJobType.VALIDATION_BATCH,
    tasks=[
        {"output": '{"status": "success", "result": "data"}'},
    ],
    max_workers=4,
)
```

### 4. Custom Batch

Custom processing logic:

```python
job = processor.submit_batch_job(
    job_type=BatchJobType.CUSTOM,
    tasks=[{"custom_data": "value"}],
    max_workers=4,
)
```

## Configuration

### Celery Configuration

Edit `src/batch/celery_config.py`:

```python
# Redis URLs
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_BACKEND = os.getenv("REDIS_BACKEND", "redis://localhost:6379/1")

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 100

# Task limits
task_time_limit = 3600  # 1 hour
task_soft_time_limit = 3000  # 50 minutes

# Retry settings
task_default_retry_delay = 60
task_max_retries = 3
```

### Environment Variables

```bash
# .env file
REDIS_URL=redis://localhost:6379/0
REDIS_BACKEND=redis://localhost:6379/1
BATCH_STORAGE_PATH=./data/batch_jobs
ENVIRONMENT=production
```

## Fault Tolerance

### Automatic Retry

Failed tasks are automatically retried based on configuration:

```python
job = processor.submit_batch_job(
    job_type=BatchJobType.FAILURE_OPTIMIZATION,
    tasks=tasks,
    retry_failed=True,  # Enable retry
    max_retries=3,      # Maximum 3 retries per task
)
```

### Worker Failure Recovery

- **Task Acknowledgment**: Tasks are acknowledged only after successful completion
- **Worker Restart**: Failed workers can be restarted without losing tasks
- **Result Persistence**: Results are stored in Redis for recovery

### Multi-Worker Support

Scale horizontally with multiple workers:

```bash
# Start multiple workers on same machine
celery -A src.batch.celery_config worker --concurrency=4 -n worker1@%h
celery -A src.batch.celery_config worker --concurrency=4 -n worker2@%h

# Or on different machines
# Machine 1
celery -A src.batch.celery_config worker -n worker1@machine1

# Machine 2
celery -A src.batch.celery_config worker -n worker2@machine2
```

## Monitoring

### Flower Web UI

Access Flower at http://localhost:5555:

- View active/completed tasks
- Monitor worker status
- See task execution times
- View task arguments and results

### API Statistics

```bash
# Get batch statistics
curl http://localhost:8001/batch/stats

# Response
{
  "total_jobs": 150,
  "by_status": {
    "completed": 100,
    "running": 10,
    "failed": 5,
    "pending": 35
  },
  "by_type": {
    "failure_optimization": 80,
    "workflow_batch": 50,
    "validation_batch": 20
  }
}
```

### Custom Monitoring

```python
# Track job metrics
from datetime import datetime, timedelta

# Get recent jobs
recent_jobs = processor.list_jobs(limit=100)

# Calculate metrics
total_tasks = sum(j['tasks_count'] for j in recent_jobs)
avg_progress = sum(
    j['progress']['progress_percent'] 
    for j in recent_jobs 
    if j.get('progress')
) / len(recent_jobs)

print(f"Total tasks: {total_tasks}")
print(f"Average progress: {avg_progress:.1f}%")
```

## Best Practices

### 1. Task Design

- **Idempotency**: Design tasks to be safely retried
- **Granularity**: Balance task size (not too small, not too large)
- **Dependencies**: Minimize dependencies between tasks

### 2. Resource Management

- **Worker Count**: Match worker count to available CPU/memory
- **Task Timeout**: Set appropriate timeouts for your tasks
- **Queue Management**: Use different queues for different priorities

### 3. Error Handling

- **Graceful Degradation**: Handle failures without crashing
- **Logging**: Log errors with sufficient context
- **Monitoring**: Set up alerts for critical failures

### 4. Performance

- **Batch Size**: Optimal batch size: 10-1000 tasks
- **Parallelism**: Use max_workers = CPU count for CPU-bound tasks
- **Redis**: Use Redis cluster for high-volume scenarios

## Troubleshooting

### Redis Connection Issues

```python
# Test Redis connection
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # Should return True
```

### Celery Worker Not Starting

```bash
# Check logs
celery -A src.batch.celery_config worker --loglevel=debug

# Verify Redis
redis-cli ping
```

### Tasks Not Processing

1. Check worker is running
2. Verify Redis connection
3. Check task queue: `celery -A src.batch.celery_config inspect active`
4. Review Flower UI for errors

### Memory Issues

```bash
# Limit worker memory
celery -A src.batch.celery_config worker --max-memory-per-child=500000  # 500MB

# Restart workers periodically
celery -A src.batch.celery_config worker --max-tasks-per-child=100
```

## Examples

See `examples/batch_processing_demo.py` for comprehensive examples:

```bash
python examples/batch_processing_demo.py
```

## API Reference

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/batch/submit` | POST | Submit a new batch job |
| `/batch/{job_id}/status` | GET | Get job status and progress |
| `/batch/{job_id}/results` | GET | Get job results |
| `/batch/{job_id}/cancel` | POST | Cancel a running job |
| `/batch/jobs` | GET | List batch jobs |
| `/batch/stats` | GET | Get batch statistics |
| `/health` | GET | Health check |

### Python API

See the full API documentation in the source code:

- `src/batch/models.py`: Data models
- `src/batch/processor.py`: BatchProcessor class
- `src/batch/tasks.py`: Celery tasks
- `src/core/workflow_orchestrator.py`: Workflow batch methods

## License

MIT License - see LICENSE file for details.
