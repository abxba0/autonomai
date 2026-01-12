# Setup Guide

This guide will walk you through the installation and configuration of the Self-Optimizing Instruction Library.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Next Steps](#next-steps)

## Prerequisites

Before installing the system, ensure you have:

### Required
- **Python 3.8+** - Check version with `python --version` or `python3 --version`
- **pip** - Python package manager (usually included with Python)
- **Git** - For cloning the repository

### Optional
- **Redis** - For distributed rate limiting (production environments)
- **PostgreSQL/MySQL** - For production database (SQLite used by default)
- **Docker** - For containerized deployment

## Installation

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/abxba0/autonomai.git
cd autonomai
```

### Step 2: Create Virtual Environment

It's recommended to use a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

#### Option A: Minimal Installation (Cloud AI Only)

For basic usage with cloud AI providers only:

```bash
# Install core dependencies only
pip install -r requirements.txt
# Or install as editable package
pip install -e .
```

**Core Dependencies Included:**
- `langchain` - LLM framework
- `langchain-anthropic` - Anthropic Claude integration
- `langchain-openai` - OpenAI GPT integration
- `langchain-google-genai` - Google Gemini integration
- `pydantic` - Data validation
- `sqlalchemy` - Database ORM
- `python-dotenv` - Environment configuration
- And more...

#### Option B: Install with Optional Features

Choose additional features based on your needs:

```bash
# For web API and security features
pip install -e ".[web]"

# For local AI embeddings and vector database
pip install -e ".[local]"

# Install everything
pip install -e ".[all]"
```

**Optional Dependencies:**

- **Web extras** (`.[web]`):
  - `fastapi` & `uvicorn` - Web API framework
  - `pyjwt` - JWT authentication
  - `bleach` - Input sanitization
  - `redis` - Distributed rate limiting

- **Local extras** (`.[local]`):
  - `chromadb` - Vector database for embeddings
  - `sentence-transformers` - ML models for semantic similarity

**Note:** The system gracefully degrades if optional dependencies are missing:
- Without `redis`: Falls back to in-memory rate limiting
- Without `chromadb`/`sentence-transformers`: Falls back to simple text similarity

### Step 4: Verify Installation

```bash
# Run a simple test to verify installation
python simple_test.py
```

Expected output:
```
=== Running Simple Test ===
✓ System initialized successfully
✓ Test execution completed
✓ All tests passed
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# API Keys (Optional - system works with mock models by default)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Security Configuration
SECRET_KEY=your_secret_key_for_jwt_signing
ENABLE_AUTHENTICATION=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true

# Model Configuration
MAIN_MODEL_TYPE=mock  # Options: mock, anthropic, openai
CRITIC_MODEL_TYPE=mock
MAIN_MODEL=claude-3-5-sonnet-20241022
CRITIC_MODEL=claude-3-haiku-20240307

# System Settings
ENABLE_AUTO_OPTIMIZATION=true
MAX_OPTIMIZATION_ATTEMPTS=3
CIRCUIT_BREAKER_THRESHOLD=3

# Database (Optional - SQLite used by default)
DATABASE_URL=sqlite:///./self_optimizing.db
# For PostgreSQL: postgresql://user:password@localhost/dbname
# For MySQL: mysql://user:password@localhost/dbname

# Redis (Optional - for distributed rate limiting)
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_REQUESTS_PER_DAY=10000

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

### Configuration Options Explained

#### API Keys
- **ANTHROPIC_API_KEY**: Required only if using Anthropic Claude models
- **OPENAI_API_KEY**: Required only if using OpenAI GPT models
- Leave blank to use mock models for testing

#### Security Settings
- **SECRET_KEY**: Generate a secure random key for JWT signing
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- **ENABLE_AUTHENTICATION**: Enable JWT-based authentication (recommended for production)
- **ENABLE_RATE_LIMITING**: Protect API from abuse
- **ENABLE_AUDIT_LOGGING**: Track all system operations

#### Model Selection
- **MAIN_MODEL_TYPE**: `mock` for testing, `anthropic` or `openai` for production
- **CRITIC_MODEL_TYPE**: Same options as MAIN_MODEL_TYPE
- **MAIN_MODEL**: Specific model name (e.g., `claude-3-5-sonnet-20241022`)
- **CRITIC_MODEL**: Usually a faster/cheaper model for analysis

#### System Behavior
- **ENABLE_AUTO_OPTIMIZATION**: Automatically improve instructions on failures
- **MAX_OPTIMIZATION_ATTEMPTS**: Maximum retries before giving up
- **CIRCUIT_BREAKER_THRESHOLD**: Consecutive failures before pausing optimization

### Database Setup

#### SQLite (Default)
No setup required. SQLite database file is created automatically.

#### PostgreSQL (Production)
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb autonomai

# Update .env with connection string
DATABASE_URL=postgresql://postgres:password@localhost/autonomai
```

#### MySQL (Production)
```bash
# Install MySQL
sudo apt-get install mysql-server

# Create database
mysql -u root -p
CREATE DATABASE autonomai;

# Update .env with connection string
DATABASE_URL=mysql://root:password@localhost/autonomai
```

### Redis Setup (Optional)

For distributed rate limiting:

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

## Verification

### Test Core Functionality

```bash
# Run basic system test
python simple_test.py

# Run mock system test
python test_mock_system.py

# Run security tests
python test_security_simple.py
```

### Test Web API

Start the API server:

```bash
cd web
python api.py
```

In another terminal, test the API:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test execute endpoint
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2+2?"}'

# Test status endpoint
curl http://localhost:8000/status
```

### Test Secure API

For production deployment with security features:

```bash
cd web
python api_secure.py
```

Test authentication:

```bash
# Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!",
    "email": "test@example.com"
  }'

# Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePassword123!"
  }'

# Use the token for authenticated requests
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"query": "Test query"}'
```

## Next Steps

After successful installation and verification:

1. **Read the [Usage Guide](usage-guide.md)** to learn how to use the system
2. **Review [Security Guide](security.md)** for production deployment
3. **Check [API Reference](api-reference.md)** for detailed API documentation
4. **Explore [Architecture](architecture.md)** to understand the system design

## Troubleshooting

If you encounter issues during setup, see the [Troubleshooting Guide](troubleshooting.md).

### Common Issues

**Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

**Port Already in Use**
```bash
# Change port in api.py or api_secure.py
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use different port
```

**Database Connection Errors**
```bash
# Verify database is running
# For PostgreSQL:
sudo systemctl status postgresql

# For MySQL:
sudo systemctl status mysql
```

**Redis Connection Errors**
```bash
# Verify Redis is running
sudo systemctl status redis
redis-cli ping
```

## Docker Installation (Alternative)

For containerized deployment:

```bash
# Build Docker image
docker build -t autonomai .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  -e SECRET_KEY=your_secret \
  autonomai
```

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "web/api.py"]
```

## Production Deployment

For production environments:

1. **Use a production database** (PostgreSQL/MySQL)
2. **Enable all security features** in `.env`
3. **Set up Redis** for distributed rate limiting
4. **Configure proper logging** and monitoring
5. **Use HTTPS** with proper SSL certificates
6. **Set strong SECRET_KEY** for JWT signing
7. **Configure CORS** with specific allowed origins
8. **Set up backup** and disaster recovery

See [Security Guide](security.md) for detailed production configuration.
