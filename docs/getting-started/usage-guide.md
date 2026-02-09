# Usage Guide

This guide provides comprehensive instructions on how to use the Self-Optimizing Instruction Library effectively.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Validators](#validators)
- [Feedback and Optimization](#feedback-and-optimization)
- [Version Management](#version-management)
- [Web API Usage](#web-api-usage)
- [Code Examples](#code-examples)

## Basic Usage

### Initialize the System

```python
from src import SelfOptimizingSystem

# Create system with default configuration
system = SelfOptimizingSystem()
```

### Execute a Query

```python
# Simple query execution
result = system.execute("What is the capital of France?")

print(f"Output: {result['output']}")
print(f"Validation passed: {result['validation_passed']}")
```

### Check Results

The `execute()` method returns a dictionary with:
- `output`: The model's response
- `validation_passed`: Boolean indicating if validation succeeded
- `validation_results`: List of validation results
- `optimization_attempted`: Whether auto-optimization was triggered
- `optimization_result`: Details of optimization if attempted

## Advanced Features

### Custom Configuration

```python
from src import SelfOptimizingSystem, SystemConfig
from pathlib import Path

# Create custom configuration
config = SystemConfig(
    # Model settings
    main_model="claude-3-5-sonnet-20241022",
    critic_model="claude-3-haiku-20240307",
    temperature_main=0.7,
    temperature_critic=0.3,
    
    # Optimization controls
    max_optimization_attempts=3,
    enable_auto_optimization=True,
    
    # Failure management
    max_failure_log_size=50,
    circuit_breaker_threshold=3,
    
    # File paths
    instructions_dir=Path("./custom_instructions"),
    instructions_file="my_instructions.md"
)

# Initialize with custom config
system = SelfOptimizingSystem(config)
```

### Using Real LLM Models

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set API key
os.environ['ANTHROPIC_API_KEY'] = 'your_api_key_here'

# System will automatically use real models if API key is set
# and model type is configured properly
system = SelfOptimizingSystem()
```

## Validators

Validators check if the model output meets specific criteria. Add validators before executing queries.

### JSON Validator

Ensures output is valid JSON with required fields:

```python
from src import JSONValidator

# Create validator
json_validator = JSONValidator(
    required_fields=["status", "data", "message"]
)

# Add to system
system.add_validator(json_validator)

# Now all outputs will be validated for JSON format
result = system.execute("Generate a status report in JSON format")
```

### Length Validator

Ensures output length is within specified bounds:

```python
from src import LengthValidator

# Create validator
length_validator = LengthValidator(
    min_length=50,    # Minimum 50 characters
    max_length=1000   # Maximum 1000 characters
)

system.add_validator(length_validator)
```

### Regex Validator

Validates output against a regular expression pattern:

```python
from src import RegexValidator

# Ensure output contains email addresses
email_validator = RegexValidator(
    pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    description="Must contain at least one email address"
)

system.add_validator(email_validator)
```

### Custom Validator

Create your own validation logic:

```python
from src import CustomValidator

def check_citation_format(output: str, context) -> bool:
    """Ensure citations are in [Author, Year] format"""
    import re
    pattern = r'\[[A-Z][a-z]+,\s*\d{4}\]'
    citations = re.findall(pattern, output)
    return len(citations) > 0

# Create custom validator
citation_validator = CustomValidator(
    name="CitationValidator",
    validation_func=check_citation_format
)

system.add_validator(citation_validator)
```

### Multiple Validators

Add multiple validators to enforce complex requirements:

```python
from src import SelfOptimizingSystem, JSONValidator, LengthValidator, RegexValidator

system = SelfOptimizingSystem()

# Add multiple validators
system.add_validator(JSONValidator(required_fields=["status", "result"]))
system.add_validator(LengthValidator(min_length=100, max_length=500))
system.add_validator(RegexValidator(
    pattern=r'\d{4}-\d{2}-\d{2}',
    description="Must include a date in YYYY-MM-DD format"
))

# All validators must pass for validation to succeed
result = system.execute("Generate a JSON report with date")
```

## Feedback and Optimization

### Automatic Optimization

The system automatically learns from validation failures:

```python
# Execute query
result = system.execute("Generate a JSON status report")

# If validation fails, system automatically:
# 1. Records the failure
# 2. Analyzes what went wrong (using Critic model)
# 3. Proposes instruction updates
# 4. Applies safe updates

if result.get('optimization_attempted'):
    opt_result = result['optimization_result']
    if opt_result['success']:
        print("System learned from failure!")
        print(f"Change: {opt_result['diff_summary']}")
```

### Manual Feedback

Provide explicit feedback for instruction improvement:

```python
# Request instruction update
result = system.request_instruction_update(
    feedback="The responses are too technical. Use simpler language.",
    severity="moderate"  # Options: minor, moderate, critical
)

if result['success']:
    print("Instructions updated based on feedback")
    print(f"Changes: {result['diff_summary']}")
```

### Process Failure Manually

Manually trigger optimization for a specific failure:

```python
result = system.process_failure(
    trigger_type="manual",
    failure_description="Output format incorrect",
    user_query="Give me JSON data",
    last_model_output="Here is your data: [plain text]",
    validation_results=[(False, "Output must be valid JSON")]
)
```

## Version Management

### View Version History

```python
# Get all versions
history = system.get_version_history()

for version in history:
    print(f"Version: {version['version_id']}")
    print(f"Timestamp: {version['timestamp']}")
    print(f"Trigger: {version['trigger_type']}")
    print(f"Changes: {version['diff_summary']}")
    print(f"Author: {version['change_author']}")
    print("---")
```

### Rollback to Previous Version

```python
# Rollback by number of steps
system.rollback(steps=2)  # Go back 2 versions

# Or rollback to specific version
system.rollback_to_version("v20250110_143000")
```

### Get Current Instructions

```python
# View current instructions
current = system.get_current_instructions()
print(current)
```

### View Failure History

```python
# Get all recorded failures
failures = system.get_failure_history()

for failure in failures:
    print(f"Query: {failure.user_query}")
    print(f"Description: {failure.failure_description}")
    print(f"Output: {failure.last_model_output}")
    print(f"Timestamp: {failure.timestamp}")
    print("---")
```

## Web API Usage

### Starting the API Server

```bash
# Basic API (no security)
cd web
python api.py

# Secure API (with authentication)
cd web
python api_secure.py
```

### API Endpoints

#### Execute Query

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is 2+2?",
    "include_metadata": true
  }'
```

Response:
```json
{
  "output": "2+2 equals 4",
  "validation_passed": true,
  "validation_results": [],
  "optimization_attempted": false,
  "timestamp": "2025-01-10T15:00:00Z"
}
```

#### Submit Feedback

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "What is 2+2?",
    "model_output": "2+2 equals 4",
    "feedback_type": "manual",
    "feedback_details": "Response is good but could include more detail",
    "severity": "minor"
  }'
```

#### Get System Status

```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600,
  "total_executions": 150,
  "total_failures": 5,
  "total_optimizations": 3,
  "current_version": "v20250110_150000"
}
```

#### Get Version History

```bash
curl http://localhost:8000/versions
```

#### Get Failure History

```bash
curl http://localhost:8000/failures?limit=10
```

### Authenticated API Usage

For the secure API, you need to authenticate first:

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myuser",
    "password": "SecurePassword123!",
    "email": "user@example.com"
  }'

# Login to get token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myuser",
    "password": "SecurePassword123!"
  }' | jq -r '.access_token')

# Use token for requests
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "Test query"}'
```

## Code Examples

### Example 1: Basic Query Execution

```python
from src import SelfOptimizingSystem

# Initialize system
system = SelfOptimizingSystem()

# Execute query
result = system.execute("Explain quantum computing in simple terms")

print(result['output'])
```

### Example 2: JSON Output Validation

```python
from src import SelfOptimizingSystem, JSONValidator

# Initialize with JSON validator
system = SelfOptimizingSystem()
system.add_validator(JSONValidator(required_fields=["summary", "details"]))

# Execute query requiring JSON
result = system.execute(
    "Generate a JSON report with 'summary' and 'details' fields"
)

if result['validation_passed']:
    print("Valid JSON output received")
    print(result['output'])
else:
    print("Validation failed:")
    print(result['validation_results'])
```

### Example 3: Learning from Failures

```python
from src import SelfOptimizingSystem, LengthValidator

system = SelfOptimizingSystem()
system.add_validator(LengthValidator(min_length=100))

# First attempt (may fail if too short)
result1 = system.execute("Summarize climate change")

if not result1['validation_passed']:
    print("First attempt failed - system learning...")
    
# Second attempt (should be better after learning)
result2 = system.execute("Summarize climate change")

if result2['validation_passed']:
    print("System learned and improved!")
```

### Example 4: Custom Validation Logic

```python
from src import SelfOptimizingSystem, CustomValidator

def validate_code_block(output: str, context) -> bool:
    """Ensure output contains code blocks"""
    return '```' in output and output.count('```') >= 2

system = SelfOptimizingSystem()
system.add_validator(CustomValidator(
    name="CodeBlockValidator",
    validation_func=validate_code_block
))

result = system.execute("Show me a Python hello world example")
```

### Example 5: Version Control

```python
from src import SelfOptimizingSystem

system = SelfOptimizingSystem()

# Make some changes through feedback
system.request_instruction_update(
    "Add more examples in responses",
    severity="moderate"
)

# Check history
history = system.get_version_history()
print(f"Total versions: {len(history)}")

# Rollback if needed
system.rollback(steps=1)
print("Rolled back to previous version")
```

### Example 6: Batch Processing

```python
from src import SelfOptimizingSystem

system = SelfOptimizingSystem()

queries = [
    "What is AI?",
    "Explain machine learning",
    "What is deep learning?"
]

results = []
for query in queries:
    result = system.execute(query)
    results.append({
        'query': query,
        'output': result['output'],
        'passed': result['validation_passed']
    })

# Analyze results
passed = sum(1 for r in results if r['passed'])
print(f"Passed: {passed}/{len(results)}")
```

## Best Practices

### 1. Start Simple
Begin with basic validators and gradually add complexity.

### 2. Monitor Failures
Regularly review failure history to identify patterns:
```python
failures = system.get_failure_history()
# Analyze common failure patterns
```

### 3. Use Appropriate Model Types
- Use faster/cheaper models for testing (`mock` or `claude-3-haiku`)
- Use powerful models for production (`claude-3-5-sonnet` or `gpt-4`)

### 4. Version Control
Always check version history before rolling back:
```python
history = system.get_version_history()
# Review changes before rollback
system.rollback(steps=1)
```

### 5. Circuit Breaker
The system has a built-in circuit breaker to prevent optimization loops. If you see repeated failures, investigate the root cause.

### 6. Custom Validators
Create specific validators for your use case rather than generic ones.

### 7. Security
Always use the secure API (`api_secure.py`) in production environments.

## Troubleshooting

See the [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.

## Next Steps

- Review [API Reference](api-reference.md) for detailed API documentation
- Check [Security Guide](security.md) for production deployment
- Explore [Architecture](architecture.md) to understand system internals
