# Distributed System and Horizontal Scaling Guide

This guide explains how to deploy AutonomAI in a distributed, horizontally scalable configuration for production environments.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start with Docker Compose](#quick-start-with-docker-compose)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Load Balancing](#load-balancing)
6. [Distributed State Management](#distributed-state-management)
7. [Scaling Guidelines](#scaling-guidelines)
8. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
9. [Security Considerations](#security-considerations)

## Architecture Overview

AutonomAI's distributed architecture consists of:

```
┌─────────────┐
│  Load       │
│  Balancer   │ (Nginx/Kubernetes Ingress)
│  (Nginx)    │
└──────┬──────┘
       │
       ├───────────┬───────────┬───────────┐
       ▼           ▼           ▼           ▼
   ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐
   │API-1│     │API-2│     │API-3│ ... │API-N│  (Horizontal API Instances)
   └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘
      │           │           │           │
      └───────────┴───────────┴───────────┘
                  │
                  ▼
           ┌──────────┐
           │  Redis   │  (State, Cache, Queue)
           └────┬─────┘
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
   ┌──────┐ ┌──────┐ ┌──────┐
   │Worker│ │Worker│ │Worker│  (Celery Workers)
   └──────┘ └──────┘ └──────┘
```

### Key Components

1. **Redis Cluster**: Central coordination for:
   - **Cache** (DB 0): LLM response caching
   - **Task Queue** (DB 1): Celery broker and result backend
   - **Distributed State** (DB 2): Cross-instance locks and state management

2. **API Servers**: Stateless FastAPI instances that:
   - Handle HTTP requests
   - Use distributed locks for critical operations
   - Share state via Redis
   - Can scale horizontally

3. **Celery Workers**: Background task processors for:
   - Batch job processing
   - Workflow execution
   - Failure optimization
   - Can scale independently

4. **Load Balancer**: Distributes traffic across API instances

## Prerequisites

### Required
- Docker and Docker Compose (for containerized deployment)
- Redis 7.0+ (for distributed state and caching)
- Python 3.11+ (for local development)

### Optional
- Kubernetes cluster (for orchestrated deployment)
- Nginx (for custom load balancing)
- Monitoring tools (Prometheus, Grafana)

## Quick Start with Docker Compose

The fastest way to deploy a distributed system locally or on a single server.

### 1. Environment Setup

Create a `.env` file with your API keys:

```bash
# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
DEEPSEEK_API_KEY=your_deepseek_key
OPENROUTER_API_KEY=your_openrouter_key

# Security
SECRET_KEY=your-secret-key-change-in-production

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_STATE_URL=redis://redis:6379/2
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

This starts:
- 1 Redis instance
- 2 API server instances
- 2 Celery worker instances
- 1 Nginx load balancer
- 1 Flower monitoring dashboard (optional)

### 3. Verify Deployment

```bash
# Check API health via load balancer
curl http://localhost/health

# Check individual instances
curl http://localhost:8001/health  # API-1
curl http://localhost:8002/health  # API-2

# View Celery monitoring
open http://localhost:5555
```

### 4. Scale Services

```bash
# Scale API instances
docker-compose up -d --scale api-1=3

# Scale Celery workers
docker-compose up -d --scale celery-worker=5
```

## Kubernetes Deployment

For production-grade orchestration with auto-scaling and high availability.

### 1. Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Container registry (Docker Hub, GCR, ECR, etc.)

### 2. Build and Push Image

```bash
# Build the Docker image
docker build -t your-registry/autonomai:latest .

# Push to registry
docker push your-registry/autonomai:latest
```

### 3. Update Manifests

Edit `k8s/02-api.yaml` and `k8s/03-celery-workers.yaml`:

```yaml
image: your-registry/autonomai:latest  # Replace with your image
```

### 4. Create Secrets

```bash
# Create namespace
kubectl apply -f k8s/00-namespace-config.yaml

# Update secrets with your API keys
kubectl edit secret autonomai-secrets -n autonomai
```

### 5. Deploy

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n autonomai
kubectl get services -n autonomai
kubectl get ingress -n autonomai
```

### 6. Configure Ingress

Update `k8s/04-ingress.yaml` with your domain:

```yaml
spec:
  rules:
  - host: api.yourdomain.com  # Your domain
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: autonomai-api
            port:
              number: 8000
```

Apply the changes:
```bash
kubectl apply -f k8s/04-ingress.yaml
```

### 7. Enable Auto-Scaling

The HPA (Horizontal Pod Autoscaler) is included and will:
- Scale API pods: 3-10 replicas based on CPU/memory
- Scale Celery workers: 2-8 replicas based on CPU/memory

Monitor scaling:
```bash
kubectl get hpa -n autonomai -w
```

## Load Balancing

### Docker Compose (Nginx)

The included `nginx.conf` provides:
- Round-robin load balancing (configurable)
- Health checks with automatic failover
- Rate limiting (10 req/s per IP)
- Connection limiting
- WebSocket support

**Load Balancing Strategies:**

Edit `nginx.conf` to change strategy:

```nginx
upstream autonomai_backend {
    # Round-robin (default)
    server api-1:8000;
    server api-2:8000;
    
    # OR least connections
    # least_conn;
    
    # OR IP hash (sticky sessions)
    # ip_hash;
}
```

### Kubernetes (Ingress)

Kubernetes Ingress provides:
- Automatic load balancing across pods
- Health-based routing
- SSL/TLS termination
- Rate limiting via annotations

**Configure rate limiting:**

```yaml
annotations:
  nginx.ingress.kubernetes.io/rate-limit: "10"  # req/s per IP
  nginx.ingress.kubernetes.io/limit-connections: "10"
  nginx.ingress.kubernetes.io/limit-rps: "10"
```

## Distributed State Management

### Overview

AutonomAI uses Redis for distributed state management to ensure:
- **Thread-safety**: Multiple instances can safely update shared resources
- **Consistency**: No race conditions when updating instructions or versions
- **Coordination**: Distributed locks prevent conflicts

### Key Features

1. **Distributed Locks**: Protect critical sections
   - Instruction updates
   - Version creation
   - Failure logging

2. **Instance Registration**: Track active instances

3. **Shared State**: Cross-instance data sharing

### Configuration

Enable distributed state in your application:

```python
from src.models.config import SystemConfig

config = SystemConfig(
    enable_distributed_state=True,
    redis_state_url="redis://localhost:6379/2",
    distributed_lock_timeout=30,  # seconds
)
```

Or via environment variables:

```bash
export ENABLE_DISTRIBUTED_STATE=true
export REDIS_STATE_URL=redis://localhost:6379/2
```

### Monitoring Active Instances

```python
from src.storage.distributed_state import DistributedStateManager, DistributedStateConfig

state_config = DistributedStateConfig()
state_manager = DistributedStateManager(state_config)

# Get active instances
instances = state_manager.get_active_instances()
print(f"Active instances: {len(instances)}")

# Health check
health = state_manager.health_check()
print(health)
```

### Manual Lock Usage

For custom critical sections:

```python
# Using context manager
with state_manager.lock("my_resource", timeout=30):
    # Critical section
    # Only one instance can execute this at a time
    pass

# Or manual lock management
lock = state_manager.get_lock("my_resource")
if lock.acquire(blocking=True, timeout=10):
    try:
        # Critical section
        pass
    finally:
        lock.release()
```

## Scaling Guidelines

### Horizontal Scaling

**API Servers:**
- Start with 2-3 instances
- Add 1 instance per 100 concurrent users
- Monitor CPU/memory usage
- Scale up if response time > 1s

**Celery Workers:**
- Start with 2 workers
- Add 1 worker per 50 queued jobs
- Monitor queue length and job latency
- Scale based on workload patterns

### Vertical Scaling

**Memory:**
- Minimum: 512MB per API instance
- Recommended: 1-2GB per API instance
- Increase if OOM errors occur

**CPU:**
- Minimum: 0.5 cores per API instance
- Recommended: 1 core per API instance
- Increase for CPU-intensive operations

### Redis Scaling

**Memory:**
- Cache: Allocate based on response sizes
- State: Usually < 100MB
- Queue: Depends on job volume
- Recommended: 2-4GB total

**Persistence:**
- Enable AOF for data safety
- Use Redis Cluster for > 10GB data
- Configure eviction policy (allkeys-lru)

### Auto-Scaling Configuration

**Kubernetes HPA:**

```yaml
spec:
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # Scale at 70% CPU
```

**Docker Swarm:**

```yaml
deploy:
  replicas: 3
  resources:
    limits:
      cpus: '1'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## Monitoring and Troubleshooting

### Health Checks

All components expose health endpoints:

```bash
# API health
curl http://localhost/health

# Redis health
redis-cli ping

# Celery workers (via Flower)
curl http://localhost:5555/api/workers
```

### Metrics to Monitor

1. **API Metrics:**
   - Request rate (req/s)
   - Response time (p50, p95, p99)
   - Error rate (%)
   - Active connections

2. **Worker Metrics:**
   - Queue length
   - Job success/failure rate
   - Job execution time
   - Active tasks

3. **Redis Metrics:**
   - Memory usage
   - Cache hit rate
   - Connection count
   - Key eviction rate

### Common Issues

**Issue: Lock timeouts**
```
Error: Could not acquire lock for instruction_update
```

Solution:
- Increase lock timeout in config
- Check Redis connectivity
- Verify no deadlocks

**Issue: High memory usage**
```
Redis: maxmemory reached
```

Solution:
- Increase Redis memory limit
- Configure eviction policy
- Clear old cache entries

**Issue: Slow response times**
```
API response > 5s
```

Solution:
- Scale API instances
- Check Redis latency
- Enable caching
- Optimize queries

### Logging

**Centralized logging:**

```bash
# Docker Compose
docker-compose logs -f --tail=100 api-1

# Kubernetes
kubectl logs -f deployment/autonomai-api -n autonomai

# Follow logs from all pods
kubectl logs -f -l app=autonomai-api -n autonomai
```

**Log levels:**

```python
import logging
logging.basicConfig(level=logging.INFO)

# For debugging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

### Network Security

1. **Use HTTPS**: Always use TLS in production
2. **Firewall Rules**: Restrict Redis access to internal network
3. **API Authentication**: Enable JWT authentication
4. **Rate Limiting**: Prevent abuse

### Secret Management

**Docker Compose:**
```bash
# Use .env file (not in git)
echo ".env" >> .gitignore
```

**Kubernetes:**
```bash
# Use Secrets
kubectl create secret generic autonomai-secrets \
  --from-literal=ANTHROPIC_API_KEY=your_key \
  --from-literal=SECRET_KEY=your_secret \
  -n autonomai
```

### Redis Security

1. **Enable Authentication:**
   ```bash
   # redis.conf
   requirepass your_secure_password
   ```

2. **Disable Dangerous Commands:**
   ```bash
   rename-command FLUSHDB ""
   rename-command FLUSHALL ""
   ```

3. **Use SSL/TLS:**
   ```bash
   # Connect with TLS
   redis_url = "rediss://localhost:6379/0"
   ```

### Best Practices

1. **Rotate API Keys**: Regularly update AI provider keys
2. **Use Secrets Management**: Vault, AWS Secrets Manager, etc.
3. **Enable Audit Logging**: Track all operations
4. **Regular Updates**: Keep dependencies updated
5. **Backup Data**: Regular Redis snapshots

## Performance Tuning

### Redis Configuration

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

### Nginx Optimization

```nginx
worker_processes auto;
worker_connections 2048;

keepalive_timeout 65;
keepalive_requests 100;

gzip on;
gzip_types text/plain application/json;
```

### API Server Tuning

```bash
# Increase workers for I/O bound operations
uvicorn web.api_secure:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# For CPU-bound operations
uvicorn web.api_secure:app --workers 2
```

## Testing Distributed Setup

### Load Testing

```bash
# Install tools
pip install locust

# Run load test
locust -f tests/load_test.py --host http://localhost
```

### Race Condition Testing

```python
# Test concurrent updates
import concurrent.futures
from src import SelfOptimizingSystem, SystemConfig

config = SystemConfig(enable_distributed_state=True)
system = SelfOptimizingSystem(config)

def update_instructions(i):
    # Simulate concurrent updates
    system.instruction_manager.update_appendix(
        f"Rule {i}",
        metadata
    )

# Run 10 concurrent updates
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(update_instructions, i) for i in range(10)]
    concurrent.futures.wait(futures)

# Verify no conflicts occurred
```

## Maintenance

### Rolling Updates

**Docker Compose:**
```bash
# Update without downtime
docker-compose up -d --no-deps --build api-1
docker-compose up -d --no-deps --build api-2
```

**Kubernetes:**
```bash
# Rolling update
kubectl set image deployment/autonomai-api \
  api=your-registry/autonomai:v2 -n autonomai

# Watch rollout
kubectl rollout status deployment/autonomai-api -n autonomai
```

### Backup and Restore

**Redis Data:**
```bash
# Backup
docker exec autonomai-redis redis-cli BGSAVE
docker cp autonomai-redis:/data/dump.rdb ./backup/

# Restore
docker cp ./backup/dump.rdb autonomai-redis:/data/
docker-compose restart redis
```

**Instruction Files:**
```bash
# Backup
tar -czf instructions-backup.tar.gz instructions/

# Restore
tar -xzf instructions-backup.tar.gz
```

## Support and Troubleshooting

For issues and questions:
- GitHub Issues: [Report a bug](https://github.com/abxba0/autonomai/issues)
- Documentation: [Full docs](../docs/)
- Examples: [Distributed examples](../examples/)

## Next Steps

- [Security Guide](security.md)
- [Monitoring Setup](monitoring.md)
- [API Reference](api-reference.md)
- [Contributing](contributing.md)
