# API Reference

Complete API documentation for the Self-Optimizing Instruction Library.

## Table of Contents

- [Python API](#python-api)
- [REST API](#rest-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)

## Python API

### SelfOptimizingSystem

Main class for interacting with the self-optimizing system.

#### Constructor

```python
SelfOptimizingSystem(config: SystemConfig = None)
```

**Parameters:**
- `config` (SystemConfig, optional): System configuration. If not provided, uses default configuration.

**Returns:** SelfOptimizingSystem instance

**Example:**
```python
from src import SelfOptimizingSystem, SystemConfig

# Default configuration
system = SelfOptimizingSystem()

# Custom configuration
config = SystemConfig(main_model="claude-3-5-sonnet-20241022")
system = SelfOptimizingSystem(config)
```

#### execute()

Execute a user query with current instructions.

```python
execute(query: str, **kwargs) -> dict
```

**Parameters:**
- `query` (str): The user query to execute
- `**kwargs`: Additional parameters passed to the model

**Returns:** Dictionary containing:
- `output` (str): Model's response
- `validation_passed` (bool): Whether validation succeeded
- `validation_results` (list): List of validation results
- `optimization_attempted` (bool): Whether optimization was triggered
- `optimization_result` (dict, optional): Optimization details

**Example:**
```python
result = system.execute("What is the capital of France?")
print(result['output'])  # "The capital of France is Paris."
```

#### add_validator()

Add a validator to the validation pipeline.

```python
add_validator(validator: Validator) -> None
```

**Parameters:**
- `validator` (Validator): Validator instance to add

**Example:**
```python
from src import JSONValidator

system.add_validator(JSONValidator(required_fields=["status"]))
```

#### request_instruction_update()

Manually request an instruction update based on feedback.

```python
request_instruction_update(
    feedback: str,
    severity: str = "moderate"
) -> dict
```

**Parameters:**
- `feedback` (str): Description of desired improvement
- `severity` (str): Severity level - "minor", "moderate", or "critical"

**Returns:** Dictionary containing:
- `success` (bool): Whether update was successful
- `diff_summary` (str): Summary of changes
- `version_id` (str): New version identifier

**Example:**
```python
result = system.request_instruction_update(
    "Use simpler language",
    severity="moderate"
)
```

#### process_failure()

Manually process a failure for optimization.

```python
process_failure(
    trigger_type: str,
    failure_description: str,
    user_query: str,
    last_model_output: str,
    validation_results: list
) -> dict
```

**Parameters:**
- `trigger_type` (str): Type of trigger (e.g., "manual", "auto_validation")
- `failure_description` (str): Description of the failure
- `user_query` (str): Original user query
- `last_model_output` (str): Model's output that failed
- `validation_results` (list): List of validation result tuples

**Returns:** Optimization result dictionary

**Example:**
```python
result = system.process_failure(
    trigger_type="manual",
    failure_description="Invalid JSON format",
    user_query="Generate JSON report",
    last_model_output="Here is data",
    validation_results=[(False, "Not valid JSON")]
)
```

#### get_version_history()

Get the version history of instructions.

```python
get_version_history() -> list
```

**Returns:** List of version metadata dictionaries

**Example:**
```python
history = system.get_version_history()
for version in history:
    print(f"{version['version_id']}: {version['diff_summary']}")
```

#### rollback()

Rollback instructions by a number of versions.

```python
rollback(steps: int = 1) -> bool
```

**Parameters:**
- `steps` (int): Number of versions to rollback

**Returns:** True if successful, False otherwise

**Example:**
```python
system.rollback(steps=2)  # Go back 2 versions
```

#### rollback_to_version()

Rollback to a specific version.

```python
rollback_to_version(version_id: str) -> bool
```

**Parameters:**
- `version_id` (str): Target version identifier

**Returns:** True if successful, False otherwise

**Example:**
```python
system.rollback_to_version("v20250110_143000")
```

#### get_current_instructions()

Get the current instruction text.

```python
get_current_instructions() -> str
```

**Returns:** Current instruction text

**Example:**
```python
instructions = system.get_current_instructions()
print(instructions)
```

#### get_failure_history()

Get the history of recorded failures.

```python
get_failure_history() -> list
```

**Returns:** List of FailureEntry objects

**Example:**
```python
failures = system.get_failure_history()
for failure in failures:
    print(f"Query: {failure.user_query}")
```

### Validators

#### JSONValidator

Validates that output is valid JSON with required fields.

```python
JSONValidator(required_fields: list = None)
```

**Parameters:**
- `required_fields` (list, optional): List of required field names

**Example:**
```python
validator = JSONValidator(required_fields=["status", "data"])
```

#### LengthValidator

Validates output length is within bounds.

```python
LengthValidator(min_length: int = None, max_length: int = None)
```

**Parameters:**
- `min_length` (int, optional): Minimum character count
- `max_length` (int, optional): Maximum character count

**Example:**
```python
validator = LengthValidator(min_length=10, max_length=500)
```

#### RegexValidator

Validates output matches a regular expression pattern.

```python
RegexValidator(pattern: str, description: str = "")
```

**Parameters:**
- `pattern` (str): Regular expression pattern
- `description` (str, optional): Human-readable description

**Example:**
```python
validator = RegexValidator(
    pattern=r'\d{4}-\d{2}-\d{2}',
    description="Must contain date in YYYY-MM-DD format"
)
```

#### CustomValidator

Custom validation using a user-defined function.

```python
CustomValidator(name: str, validation_func: callable)
```

**Parameters:**
- `name` (str): Validator name
- `validation_func` (callable): Function that takes (output, context) and returns bool

**Example:**
```python
def check_greeting(output: str, context) -> bool:
    return "hello" in output.lower()

validator = CustomValidator("GreetingValidator", check_greeting)
```

### SystemConfig

Configuration dataclass for the system.

```python
SystemConfig(
    main_model: str = "claude-3-5-sonnet-20241022",
    critic_model: str = "claude-3-haiku-20240307",
    temperature_main: float = 0.7,
    temperature_critic: float = 0.3,
    max_optimization_attempts: int = 3,
    enable_auto_optimization: bool = True,
    max_failure_log_size: int = 50,
    circuit_breaker_threshold: int = 3,
    instructions_dir: Path = Path("./instructions"),
    instructions_file: str = "instructions.md"
)
```

**Attributes:**
- `main_model`: Main model identifier
- `critic_model`: Critic model identifier
- `temperature_main`: Temperature for main model (0.0-1.0)
- `temperature_critic`: Temperature for critic model (0.0-1.0)
- `max_optimization_attempts`: Maximum optimization retries
- `enable_auto_optimization`: Enable automatic learning
- `max_failure_log_size`: Maximum failures to store
- `circuit_breaker_threshold`: Failures before pausing optimization
- `instructions_dir`: Directory for instruction files
- `instructions_file`: Instruction file name

## REST API

### Base URL

```
http://localhost:8000
```

### Authentication

For secure API (`api_secure.py`), include JWT token in Authorization header:

```
Authorization: Bearer <token>
```

### Endpoints

#### POST /execute

Execute a query.

**Request:**
```json
{
  "query": "What is AI?",
  "include_metadata": true
}
```

**Response:**
```json
{
  "output": "AI stands for Artificial Intelligence...",
  "validation_passed": true,
  "validation_results": [],
  "optimization_attempted": false,
  "timestamp": "2025-01-10T15:00:00Z",
  "execution_time": 0.5
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request
- 401: Unauthorized (secure API only)
- 429: Rate limit exceeded (secure API only)
- 500: Server error

#### POST /feedback

Submit feedback for instruction improvement.

**Request:**
```json
{
  "user_query": "What is AI?",
  "model_output": "AI is...",
  "feedback_type": "manual",
  "feedback_details": "Add more examples",
  "severity": "moderate"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback processed successfully",
  "optimization_result": {
    "success": true,
    "version_id": "v20250110_150000",
    "diff_summary": "Added instruction to include examples"
  }
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request
- 401: Unauthorized
- 500: Server error

#### GET /status

Get system status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600,
  "total_executions": 150,
  "total_failures": 5,
  "total_optimizations": 3,
  "current_version": "v20250110_150000",
  "circuit_breaker_active": false
}
```

#### GET /versions

Get version history.

**Query Parameters:**
- `limit` (int, optional): Maximum number of versions to return

**Response:**
```json
{
  "versions": [
    {
      "version_id": "v20250110_150000",
      "timestamp": "2025-01-10T15:00:00Z",
      "trigger_type": "manual_feedback",
      "diff_summary": "Added instruction to include examples",
      "change_author": "system"
    }
  ],
  "total": 1
}
```

#### GET /failures

Get failure history.

**Query Parameters:**
- `limit` (int, optional): Maximum number of failures to return
- `since` (str, optional): ISO timestamp to filter failures after

**Response:**
```json
{
  "failures": [
    {
      "id": "fail_001",
      "timestamp": "2025-01-10T14:00:00Z",
      "user_query": "Generate JSON",
      "failure_description": "Invalid JSON format",
      "last_model_output": "Here is data",
      "validation_results": ["Not valid JSON"]
    }
  ],
  "total": 1
}
```

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T15:00:00Z"
}
```

### Secure API Endpoints

Additional endpoints in `api_secure.py`:

#### POST /auth/register

Register a new user.

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!",
  "email": "john@example.com",
  "role": "viewer"
}
```

**Response:**
```json
{
  "user_id": "user_123",
  "username": "johndoe",
  "role": "viewer",
  "created_at": "2025-01-10T15:00:00Z"
}
```

#### POST /auth/login

Login and get JWT token.

**Request:**
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/refresh

Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### GET /admin/users

List all users (admin only).

**Response:**
```json
{
  "users": [
    {
      "user_id": "user_123",
      "username": "johndoe",
      "email": "john@example.com",
      "role": "viewer",
      "created_at": "2025-01-10T15:00:00Z"
    }
  ],
  "total": 1
}
```

#### GET /admin/audit-logs

Get audit logs (admin only).

**Query Parameters:**
- `limit` (int, optional): Maximum logs to return
- `event_type` (str, optional): Filter by event type
- `since` (str, optional): ISO timestamp

**Response:**
```json
{
  "logs": [
    {
      "id": "log_001",
      "timestamp": "2025-01-10T15:00:00Z",
      "event_type": "user_login",
      "user_id": "user_123",
      "details": {"ip": "192.168.1.1"}
    }
  ],
  "total": 1
}
```

## Data Models

### FailureEntry

Represents a system failure.

**Attributes:**
- `id` (str): Unique identifier
- `timestamp` (datetime): When failure occurred
- `trigger_type` (str): How failure was triggered
- `failure_description` (str): Description of failure
- `user_query` (str): Original query
- `last_model_output` (str): Failed output
- `validation_results` (list): Validation result details

### VersionMetadata

Represents an instruction version.

**Attributes:**
- `version_id` (str): Version identifier
- `timestamp` (datetime): When version was created
- `trigger_type` (str): What triggered the change
- `diff_summary` (str): Summary of changes
- `change_author` (str): Who made the change
- `previous_version_id` (str): Previous version ID

### CriticResponse

Structured response from critic model.

**Attributes:**
- `proposed_changes` (str): Proposed instruction changes
- `impact_analysis` (str): Analysis of change impact
- `safety_check` (str): Safety considerations
- `confidence` (float): Confidence score (0.0-1.0)

## Error Handling

### Exception Types

**ValidationError**
- Raised when input validation fails
- Contains details about validation failure

**OptimizationError**
- Raised when optimization fails
- Contains reason for failure

**AuthenticationError** (Secure API only)
- Raised when authentication fails
- Invalid credentials or expired token

**RateLimitError** (Secure API only)
- Raised when rate limit is exceeded
- Contains retry-after information

### Error Response Format

All API errors return:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  },
  "status_code": 400
}
```

### Common Error Codes

- **400 Bad Request**: Invalid input or malformed request
- **401 Unauthorized**: Authentication required or invalid token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error

### Example Error Handling

```python
from src import SelfOptimizingSystem
from src.exceptions import ValidationError, OptimizationError

system = SelfOptimizingSystem()

try:
    result = system.execute("Query")
except ValidationError as e:
    print(f"Validation failed: {e}")
except OptimizationError as e:
    print(f"Optimization failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Rate Limiting

The secure API includes rate limiting with the following headers:

**Response Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

**Default Limits:**
- 60 requests per minute
- 1000 requests per hour
- 10000 requests per day

## Next Steps

- See [Usage Guide](usage-guide.md) for practical examples
- Review [Security Guide](security.md) for authentication details
- Check [Troubleshooting](troubleshooting.md) for common issues
