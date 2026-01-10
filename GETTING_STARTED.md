# Getting Started with Self-Optimizing Instruction Library

## Overview

The Self-Optimizing Instruction Library is a system that automatically improves its own instructions through a continuous feedback loop. It learns from failures, analyzes them with a critic model, and updates its instructions to prevent similar failures in the future.

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd self_optimizing_system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Basic Usage

```python
from src import SelfOptimizingSystem

# Create the system
system = SelfOptimizingSystem()

# Execute a query
result = system.execute("What is 2+2?")
print(f"Result: {result}")

# Process feedback
feedback_result = system.process_feedback(
    user_query="What is 2+2?",
    model_output=result,
    feedback_type="auto_validation",
    feedback_details="Output validation passed"
)

# Get version history
versions = system.get_version_history()
print(f"Total versions: {len(versions)}")
```

### 3. Configuration

Create a `.env` file in the project root:

```env
# API Keys (optional - system works with mock models by default)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Database Configuration (optional)
DATABASE_URL=sqlite:///./self_optimizing.db

# System Settings
ENABLE_AUTO_OPTIMIZATION=true
MAIN_MODEL_TYPE=mock  # or "anthropic", "openai"
CRITIC_MODEL_TYPE=mock  # or "anthropic", "openai"
```

## Core Components

### 1. Main Model
- Executes user queries using current instructions
- Can use mock models or real LLMs (Anthropic Claude, OpenAI GPT)
- Validates outputs against defined rules

### 2. Critic Model
- Analyzes failures and suggests instruction improvements
- Ensures safety and consistency of changes
- Provides detailed impact analysis

### 3. Instruction Manager
- Manages instruction versions
- Handles rollbacks if needed
- Maintains version history

### 4. Validation Pipeline
- JSON validation
- Length validation
- Custom rule validation
- Automatic failure detection

## Advanced Usage

### Custom Validators

```python
from src import SelfOptimizingSystem, JSONValidator, LengthValidator

# Create system with custom validators
system = SelfOptimizingSystem()

# Add custom validator
system.add_validator(JSONValidator(required_fields=["status", "data"]))
system.add_validator(LengthValidator(min_length=10, max_length=1000))
```

### Manual Optimization Trigger

```python
# Manually trigger optimization for a failure
optimization_result = system.process_failure(
    trigger_type="manual",
    failure_description="Output format incorrect",
    user_query="Give me JSON data",
    last_model_output="Here is your data",
    validation_results=[(False, "Output must be valid JSON")]
)
```

### Database Integration

```python
# The system automatically uses database if DATABASE_URL is set
# Otherwise, it uses file-based storage

# Query failure history
failures = system.get_failure_history()
for failure in failures:
    print(f"Failure: {failure.failure_description}")
    print(f"  Query: {failure.user_query}")
    print(f"  Timestamp: {failure.timestamp}")
```

## Web Interface

### Start the API Server

```bash
cd web
python api.py
```

### API Endpoints

- `POST /execute` - Execute a query
- `POST /feedback` - Submit feedback
- `GET /status` - System status
- `GET /versions` - Version history
- `GET /failures` - Failure history

### Example API Usage

```bash
# Execute a query
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2+2?"}'

# Get system status
curl http://localhost:8000/status
```

## Testing

### Run Basic Tests

```bash
# Test core functionality
python simple_test.py

# Test system with mock models
python test_mock_system.py

# Run comprehensive tests
python -m pytest tests/
```

### Test with Real LLMs

1. Set up API keys in `.env`
2. Update model types to "anthropic" or "openai"
3. Run the basic usage example

## Deployment

### Production Considerations

1. **Database**: Use PostgreSQL or MySQL for production
2. **Caching**: Implement Redis for frequent queries
3. **Monitoring**: Add logging and metrics collection
4. **Security**: Implement API key rotation and rate limiting

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "web/api.py"]
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **API Key Issues**: Check `.env` file and environment variables
3. **Database Errors**: Verify DATABASE_URL and permissions
4. **Validation Failures**: Check validator configurations

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [Repository URL]/issues
- Documentation: [Documentation URL]
- Email: [Support Email]