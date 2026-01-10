# Troubleshooting Guide

Common issues and solutions for the Self-Optimizing Instruction Library.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Runtime Errors](#runtime-errors)
- [API Issues](#api-issues)
- [Security Issues](#security-issues)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)

## Installation Issues

### Python Version Error

**Problem:**
```
ERROR: This package requires Python 3.8 or higher
```

**Solution:**
```bash
# Check Python version
python --version
# or
python3 --version

# Install Python 3.8+ if needed
sudo apt-get update
sudo apt-get install python3.12
```

### Dependency Installation Fails

**Problem:**
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solution:**
```bash
# Ensure pip is up to date
pip install --upgrade pip

# Try installing with --no-cache-dir
pip install --no-cache-dir -r requirements.txt

# If specific package fails, install it separately
pip install langchain==0.1.0
```

### Virtual Environment Issues

**Problem:**
```
Command 'python' not found in virtual environment
```

**Solution:**
```bash
# Deactivate and remove old venv
deactivate
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Import Errors

**Problem:**
```python
ImportError: No module named 'src'
```

**Solution:**
```bash
# Ensure you're in the project root directory
cd /path/to/autonomai

# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

## Configuration Issues

### Missing .env File

**Problem:**
```
Warning: .env file not found
```

**Solution:**
```bash
# Copy example file
cp .env.example .env

# Edit with your configuration
nano .env
```

### Invalid API Keys

**Problem:**
```
ERROR: Invalid Anthropic API key
```

**Solution:**
```bash
# Verify API key is set correctly in .env
ANTHROPIC_API_KEY=sk-ant-...

# Or set as environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Test with mock models first
MAIN_MODEL_TYPE=mock
CRITIC_MODEL_TYPE=mock
```

### Invalid SECRET_KEY

**Problem:**
```
ERROR: SECRET_KEY not configured or invalid
```

**Solution:**
```bash
# Generate a secure random key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env
SECRET_KEY=your_generated_key_here
```

### Configuration Not Loading

**Problem:**
Configuration changes in `.env` not taking effect.

**Solution:**
```bash
# Restart the application
# Kill the process
pkill -f "python web/api.py"

# Start again
python web/api.py

# Verify environment variables are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SECRET_KEY'))"
```

## Runtime Errors

### Model Execution Fails

**Problem:**
```
ERROR: Model execution failed
```

**Solution:**
```python
# Check if using mock models for testing
from src import SystemConfig

config = SystemConfig(
    main_model_type="mock",
    critic_model_type="mock"
)

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check instructions file exists
import os
os.path.exists("instructions/instructions.md")
```

### Validation Always Fails

**Problem:**
All queries fail validation unexpectedly.

**Solution:**
```python
# Review validator configuration
system.validators  # Check active validators

# Remove validators to test
system.validators.clear()

# Add validators one by one
from src import JSONValidator
system.add_validator(JSONValidator(required_fields=["status"]))

# Test with simple query
result = system.execute("Test query")
print(result['validation_results'])
```

### Optimization Loop

**Problem:**
```
WARNING: Circuit breaker activated - too many optimization failures
```

**Solution:**
```python
# Circuit breaker is working correctly to prevent loops
# Review recent failures
failures = system.get_failure_history()
for f in failures[-5:]:
    print(f"Query: {f.user_query}")
    print(f"Error: {f.failure_description}")

# Wait for circuit breaker to reset (automatic)
# Or manually reset if needed
system.reset_circuit_breaker()

# Adjust circuit breaker threshold
config = SystemConfig(circuit_breaker_threshold=5)
```

### File Permission Errors

**Problem:**
```
PermissionError: [Errno 13] Permission denied: 'instructions/instructions.md'
```

**Solution:**
```bash
# Fix permissions
chmod -R 755 instructions/

# Check ownership
ls -la instructions/

# Change owner if needed
sudo chown -R $USER:$USER instructions/
```

### Memory Errors

**Problem:**
```
MemoryError: Unable to allocate array
```

**Solution:**
```python
# Reduce failure log size
config = SystemConfig(max_failure_log_size=25)

# Clear old failures
system.clear_old_failures(keep_recent=10)

# Use database storage instead of in-memory
DATABASE_URL=postgresql://user:pass@localhost/db
```

## API Issues

### Port Already in Use

**Problem:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
# Edit api.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### CORS Errors

**Problem:**
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS
```

**Solution:**
```python
# Update allowed origins in .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Or in api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 401 Unauthorized

**Problem:**
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

**Solution:**
```bash
# Login again to get fresh token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use the new token
TOKEN=<new_token>

# Check token expiration
python -c "import jwt; print(jwt.decode('$TOKEN', options={'verify_signature': False}))"
```

### 429 Rate Limit Exceeded

**Problem:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests"
}
```

**Solution:**
```bash
# Wait for rate limit window to reset
# Check retry_after header

# Or adjust rate limits in .env
RATE_LIMIT_REQUESTS_PER_MINUTE=1000

# Or use different API key with higher limits
```

### Request Timeout

**Problem:**
```
TimeoutError: Request timed out after 30 seconds
```

**Solution:**
```python
# Increase timeout
import httpx

client = httpx.Client(timeout=60.0)

# Or in api.py
@app.post("/execute", timeout=60)
async def execute_query(...):
    ...

# For LLM calls, increase timeout
config = SystemConfig(request_timeout=120)
```

## Security Issues

### Authentication Not Working

**Problem:**
Users cannot login despite correct credentials.

**Solution:**
```bash
# Check SECRET_KEY is set
echo $SECRET_KEY

# Verify database connection
python -c "from src.security import get_db; next(get_db())"

# Check user exists
python -c "from src.security import get_user; print(get_user('username'))"

# Reset password if needed
python scripts/reset_password.py username
```

### JWT Token Invalid

**Problem:**
```
ERROR: Invalid token signature
```

**Solution:**
```bash
# Ensure SECRET_KEY hasn't changed
# Tokens are invalid if SECRET_KEY changes

# Generate new token
curl -X POST http://localhost:8000/auth/login \
  -d '{"username": "user", "password": "pass"}'

# Check token format
echo $TOKEN | cut -d. -f2 | base64 -d
```

### API Key Not Accepted

**Problem:**
```
ERROR: Invalid API key
```

**Solution:**
```bash
# Verify API key format
# Should start with sk_live_ or sk_test_

# Check if key is revoked
curl http://localhost:8000/admin/api-keys/<key_id> \
  -H "Authorization: Bearer $TOKEN"

# Generate new API key
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "New Key"}'
```

### Permission Denied

**Problem:**
```json
{
  "error": "permission_denied",
  "message": "User lacks required permission"
}
```

**Solution:**
```bash
# Check user role
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Update user role (admin only)
curl -X PUT http://localhost:8000/admin/users/<user_id>/role \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"role": "editor"}'
```

## Performance Issues

### Slow Response Times

**Problem:**
API responses take too long (>5 seconds).

**Solution:**
```python
# Enable caching
REDIS_URL=redis://localhost:6379/0

# Use faster models
config = SystemConfig(
    main_model="claude-3-haiku-20240307",  # Faster than sonnet
    critic_model="claude-3-haiku-20240307"
)

# Reduce validation complexity
# Remove unnecessary validators

# Monitor performance
import time
start = time.time()
result = system.execute(query)
print(f"Took {time.time() - start:.2f} seconds")
```

### High Memory Usage

**Problem:**
Memory usage grows over time.

**Solution:**
```python
# Clear failure history periodically
system.clear_old_failures(keep_recent=50)

# Limit failure log size
config = SystemConfig(max_failure_log_size=50)

# Use database instead of in-memory storage
DATABASE_URL=postgresql://localhost/autonomai

# Monitor memory
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

### Database Query Slow

**Problem:**
Database queries are slow.

**Solution:**
```sql
-- Add indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_failures_timestamp ON failures(timestamp);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM audit_logs WHERE timestamp > '2025-01-01';

-- Archive old data
DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '90 days';
```

### Rate Limiter Slow

**Problem:**
Rate limit checks are slow.

**Solution:**
```python
# Use Redis instead of in-memory
REDIS_URL=redis://localhost:6379/0

# Use fixed window instead of sliding window
rate_config = RateLimitConfig(
    strategy="fixed_window"  # Faster than sliding_window
)

# Reduce rate limit check frequency
# Use middleware caching
```

## Database Issues

### Connection Errors

**Problem:**
```
ERROR: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check database is running
# For PostgreSQL:
sudo systemctl status postgresql
sudo systemctl start postgresql

# For MySQL:
sudo systemctl status mysql
sudo systemctl start mysql

# Verify connection string
psql -h localhost -U postgres -d autonomai

# Check firewall
sudo ufw allow 5432  # PostgreSQL
sudo ufw allow 3306  # MySQL
```

### Migration Errors

**Problem:**
```
ERROR: relation "users" does not exist
```

**Solution:**
```bash
# Run migrations
alembic upgrade head

# Or create tables manually
python scripts/create_tables.py

# Check current schema
psql -d autonomai -c "\dt"
```

### Data Corruption

**Problem:**
Data appears corrupted or inconsistent.

**Solution:**
```bash
# Backup database first
pg_dump autonomai > backup.sql

# Check data integrity
python scripts/verify_data.py

# Restore from backup if needed
psql autonomai < backup.sql

# Rebuild from scratch
dropdb autonomai
createdb autonomai
python scripts/create_tables.py
```

### Disk Space Issues

**Problem:**
```
ERROR: could not write to file: No space left on device
```

**Solution:**
```bash
# Check disk space
df -h

# Clean up old logs
rm -rf logs/*.log.old

# Archive old audit logs
python scripts/archive_audit_logs.py --older-than 90

# Move to larger disk
# Backup, move, and restore database
```

## Redis Issues

### Connection Failed

**Problem:**
```
ERROR: Error connecting to Redis
```

**Solution:**
```bash
# Check Redis is running
sudo systemctl status redis
sudo systemctl start redis

# Test connection
redis-cli ping
# Should return: PONG

# Check Redis configuration
redis-cli CONFIG GET bind
redis-cli CONFIG GET port

# Update connection string
REDIS_URL=redis://localhost:6379/0
```

### Out of Memory

**Problem:**
```
ERROR: OOM command not allowed when used memory > 'maxmemory'
```

**Solution:**
```bash
# Check Redis memory usage
redis-cli INFO memory

# Increase max memory
redis-cli CONFIG SET maxmemory 512mb

# Enable eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Or clear cache
redis-cli FLUSHDB
```

## Debug Mode

Enable detailed logging to troubleshoot issues:

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log to file
logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG
)

# Test system
from src import SelfOptimizingSystem
system = SelfOptimizingSystem()
result = system.execute("Test query")
```

## Getting Help

If you cannot resolve your issue:

1. **Check Documentation**
   - [Setup Guide](setup-guide.md)
   - [Usage Guide](usage-guide.md)
   - [API Reference](api-reference.md)

2. **Search Issues**
   - [GitHub Issues](https://github.com/abxba0/autonomai/issues)
   - Search for similar problems

3. **Create Issue**
   - Describe the problem
   - Include error messages
   - Provide steps to reproduce
   - Share configuration (without secrets)

4. **Community Support**
   - Join discussions
   - Ask questions
   - Share solutions

## Diagnostic Script

Run this script to collect diagnostic information:

```python
#!/usr/bin/env python3
"""Diagnostic script for troubleshooting"""

import sys
import os
import platform
from pathlib import Path

print("=== System Diagnostics ===\n")

# Python version
print(f"Python Version: {sys.version}")
print(f"Platform: {platform.platform()}\n")

# Dependencies
print("=== Installed Packages ===")
import subprocess
result = subprocess.run(["pip", "list"], capture_output=True, text=True)
print(result.stdout)

# Environment
print("\n=== Environment Variables ===")
env_vars = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL"
]
for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        masked = value[:10] + "..." if len(value) > 10 else "***"
        print(f"{var}: {masked}")
    else:
        print(f"{var}: Not set")

# File structure
print("\n=== File Structure ===")
for path in ["instructions/", "src/", "web/", ".env"]:
    exists = Path(path).exists()
    print(f"{path}: {'✓ Exists' if exists else '✗ Missing'}")

# Database connection
print("\n=== Database Connection ===")
try:
    from src.security import get_db
    db = next(get_db())
    print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")

# Redis connection
print("\n=== Redis Connection ===")
try:
    import redis
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    r.ping()
    print("✓ Redis connection successful")
except Exception as e:
    print(f"✗ Redis connection failed: {e}")

# System test
print("\n=== System Test ===")
try:
    from src import SelfOptimizingSystem
    system = SelfOptimizingSystem()
    result = system.execute("Test query")
    print("✓ System test passed")
except Exception as e:
    print(f"✗ System test failed: {e}")

print("\n=== End Diagnostics ===")
```

Save as `diagnostic.py` and run:

```bash
python diagnostic.py > diagnostics.txt
```

Share `diagnostics.txt` when reporting issues.

## Next Steps

- Review [Setup Guide](setup-guide.md) for proper configuration
- Check [Security Guide](security.md) for security-related issues
- See [Architecture](architecture.md) to understand system design
