# Architecture

System architecture and design documentation for the Self-Optimizing Instruction Library.

## Table of Contents

- [System Overview](#system-overview)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Storage Layer](#storage-layer)
- [Security Architecture](#security-architecture)
- [Scalability](#scalability)
- [Design Patterns](#design-patterns)

## System Overview

The Self-Optimizing Instruction Library is a feedback-driven AI system that continuously improves its own instructions through a critic-actor architecture.

### High-Level Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         Web API Layer               │
│  (FastAPI + Security Middleware)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    Self-Optimizing System Core      │
│  ┌──────────────────────────────┐   │
│  │    Main Model (Actor)        │   │
│  │  - Executes queries          │   │
│  │  - Uses current instructions │   │
│  └──────────────────────────────┘   │
│               │                      │
│               ▼                      │
│  ┌──────────────────────────────┐   │
│  │    Validation Pipeline       │   │
│  │  - JSON Validator            │   │
│  │  - Length Validator          │   │
│  │  - Regex Validator           │   │
│  │  - Custom Validators         │   │
│  └──────────────────────────────┘   │
│               │                      │
│               ▼                      │
│  ┌──────────────────────────────┐   │
│  │    Critic Model (Optimizer)  │   │
│  │  - Analyzes failures         │   │
│  │  - Proposes improvements     │   │
│  │  - Safety checks             │   │
│  └──────────────────────────────┘   │
│               │                      │
│               ▼                      │
│  ┌──────────────────────────────┐   │
│  │    Instruction Manager       │   │
│  │  - Version control           │   │
│  │  - File management           │   │
│  │  - Rollback support          │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Storage Layer               │
│  - Instructions (Markdown)          │
│  - Version History                  │
│  - Failure Logs                     │
│  - Audit Logs (Database)            │
└─────────────────────────────────────┘
```

### Key Principles

1. **Self-Improvement**: System learns from failures automatically
2. **Safety First**: All changes go through safety checks
3. **Traceability**: Full audit trail of all changes
4. **Modularity**: Pluggable validators and models
5. **Security**: Enterprise-grade security features

## Core Components

### 1. Main Model (Actor)

**Location**: `src/core/main_model.py`

The Main Model executes user queries using current instructions.

**Responsibilities:**
- Execute user queries
- Apply current instructions
- Return structured outputs
- Handle errors gracefully

**Interfaces:**
```python
class MainModel:
    def execute(self, query: str, context: dict) -> str:
        """Execute query with current instructions"""
        
    def get_instructions(self) -> str:
        """Get current instruction text"""
```

**Model Support:**
- Mock models (for testing)
- Anthropic Claude
- OpenAI GPT
- Custom LLM providers

### 2. Critic Model (Optimizer)

**Location**: `src/core/critic_model.py`

The Critic Model analyzes failures and proposes instruction improvements.

**Responsibilities:**
- Analyze failure patterns
- Propose instruction updates
- Perform impact analysis
- Conduct safety checks

**Interfaces:**
```python
class CriticModel:
    def analyze_failure(self, failure: FailureEntry) -> CriticResponse:
        """Analyze failure and propose improvements"""
        
    def verify_safety(self, proposed_changes: str) -> bool:
        """Verify changes are safe to apply"""
```

**Analysis Process:**
1. Review failure context
2. Identify root cause
3. Propose specific changes
4. Assess impact and safety
5. Return structured response

### 3. Validation Pipeline

**Location**: `src/core/validator.py`

Extensible validation framework for checking outputs.

**Responsibilities:**
- Validate model outputs
- Support multiple validators
- Provide detailed feedback
- Enable custom validation logic

**Built-in Validators:**
- `JSONValidator`: Validates JSON format and required fields
- `LengthValidator`: Checks length constraints
- `RegexValidator`: Pattern matching
- `CustomValidator`: User-defined validation functions

**Interface:**
```python
class Validator:
    def validate(self, output: str, context: dict) -> tuple[bool, str]:
        """Validate output, return (success, message)"""
```

**Pipeline Process:**
```
Input → Validator 1 → Validator 2 → ... → Validator N → Result
         ↓ fail         ↓ fail              ↓ fail
      Record         Record              Record
```

### 4. Instruction Manager

**Location**: `src/core/instruction_manager.py`

Manages instruction files and version control.

**Responsibilities:**
- Load/save instructions
- Track version history
- Support rollback operations
- Manage file structure

**File Structure:**
```
instructions/
├── instructions.md          # Current active instructions
├── .versions/              # Version history
│   ├── v20250110_140000.md
│   ├── v20250110_150000.md
│   └── ...
├── pending_review.md       # Failed optimization attempts
└── archived_failures.md    # Historical failure log
```

**Version Control:**
- Git-style versioning
- Diff tracking
- Metadata storage
- Rollback support

### 5. Version Controller

**Location**: `src/storage/version_control.py`

Maintains version history and enables rollback.

**Responsibilities:**
- Create version snapshots
- Store version metadata
- Enable version comparison
- Support rollback operations

**Metadata Tracked:**
- Version ID
- Timestamp
- Trigger type
- Change summary
- Author
- Previous version link

## Data Flow

### Query Execution Flow

```
1. Client Request
   ↓
2. API Endpoint (Security Checks)
   ↓
3. SelfOptimizingSystem.execute()
   ↓
4. MainModel.execute() → Uses current instructions
   ↓
5. Validation Pipeline
   ├─ Pass → Return success
   └─ Fail ↓
6. Record Failure
   ↓
7. CriticModel.analyze_failure()
   ↓
8. Propose Instruction Update
   ↓
9. Safety Checks
   ├─ Pass → Apply update
   └─ Fail → Save to pending_review
   ↓
10. Return result with optimization info
```

### Optimization Flow

```
1. Failure Detected
   ↓
2. Create FailureEntry
   ↓
3. Check Circuit Breaker
   ├─ Open → Skip optimization
   └─ Closed ↓
4. Load Failure Context
   ↓
5. Critic Analyzes Failure
   ↓
6. Generate CriticResponse
   ├─ proposed_changes
   ├─ impact_analysis
   ├─ safety_check
   └─ confidence
   ↓
7. Verify Safety
   ├─ Safe → Apply changes
   └─ Unsafe → Reject
   ↓
8. Update Instructions
   ↓
9. Create Version Snapshot
   ↓
10. Update Circuit Breaker State
```

### Feedback Flow

```
1. User Provides Feedback
   ↓
2. Create Failure Entry (manual trigger)
   ↓
3. Trigger Optimization
   ↓
4. [Follow Optimization Flow]
   ↓
5. Return Update Result
```

## Storage Layer

### File-Based Storage

**Instructions:**
- Format: Markdown (.md)
- Location: `instructions/instructions.md`
- Versioned: Yes
- Backup: Automatic

**Version History:**
- Format: Markdown snapshots
- Location: `instructions/.versions/`
- Naming: `vYYYYMMDD_HHMMSS.md`
- Metadata: Separate JSON or embedded

**Failure Logs:**
- Format: Markdown or JSON
- Location: `instructions/archived_failures.md`
- Rotation: Based on size
- Compression: Tiered

### Database Storage (Optional)

**Schema:**

```sql
-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys table
CREATE TABLE api_keys (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    permissions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP NULL
);

-- Audit Logs table
CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(36) REFERENCES users(id),
    ip_address VARCHAR(45),
    details JSON,
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id)
);

-- Failures table (optional)
CREATE TABLE failures (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trigger_type VARCHAR(50),
    user_query TEXT,
    model_output TEXT,
    failure_description TEXT,
    validation_results JSON,
    INDEX idx_timestamp (timestamp)
);

-- Versions table (optional)
CREATE TABLE versions (
    id VARCHAR(36) PRIMARY KEY,
    version_id VARCHAR(50) UNIQUE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trigger_type VARCHAR(50),
    instructions TEXT,
    diff_summary TEXT,
    change_author VARCHAR(255),
    metadata JSON,
    INDEX idx_version_id (version_id),
    INDEX idx_timestamp (timestamp)
);
```

### Caching Layer (Optional)

**Redis Cache:**
- Current instructions
- Recent query results
- Rate limit counters
- Session data

**Configuration:**
```python
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "ttl": {
        "instructions": 300,  # 5 minutes
        "query_results": 60,  # 1 minute
        "rate_limits": 3600   # 1 hour
    }
}
```

## Security Architecture

### Authentication Layer

```
Request → JWT Validation → User Identity
       ↓
    API Key Validation → Service Identity
```

**JWT Token Flow:**
1. User logs in with credentials
2. System validates credentials
3. Generate access + refresh tokens
4. Return tokens to client
5. Client includes token in requests
6. System validates token on each request

### Authorization Layer

```
User Identity → Role Lookup → Permissions Check → Allow/Deny
```

**RBAC Model:**
- Users have roles
- Roles have permissions
- Permissions control actions
- Hierarchical roles supported

### Input Validation

```
Request → Sanitization → Type Validation → Business Logic
                ↓
           Security Checks
           - XSS prevention
           - SQL injection detection
           - Command injection check
```

### Rate Limiting

```
Request → Identify User → Check Rate Limit → Allow/Deny
                              ↓
                         Update Counter
```

**Strategies:**
- **Fixed Window**: Simple, fast, allows bursts
- **Sliding Window**: Smooth, accurate, fair
- **Token Bucket**: Flexible, supports bursts

### Audit Logging

```
Action → Log Event → Store in Database → Monitor/Alert
```

**Logged Information:**
- Who (user_id, username)
- What (event_type, details)
- When (timestamp)
- Where (ip_address, user_agent)
- Result (success/failure)

## Scalability

### Horizontal Scaling

**Stateless API:**
- No server-side session state
- JWT tokens for authentication
- Redis for shared state

**Load Balancing:**
```
            ┌─────────────┐
Client ────►│Load Balancer│
            └──────┬──────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    ┌─────┐    ┌─────┐    ┌─────┐
    │ API │    │ API │    │ API │
    │  1  │    │  2  │    │  3  │
    └─────┘    └─────┘    └─────┘
        │          │          │
        └──────────┼──────────┘
                   ▼
            ┌────────────┐
            │  Database  │
            └────────────┘
```

**Shared Components:**
- Centralized database
- Redis for caching/rate limiting
- Shared file storage (S3, NFS)

### Vertical Scaling

**Resource Allocation:**
- CPU: For LLM inference
- Memory: For caching
- Disk: For logs and history
- Network: For API requests

**Optimization:**
- Model caching
- Response caching
- Connection pooling
- Async processing

### Performance Considerations

**Bottlenecks:**
1. LLM API calls (highest latency)
2. Database queries
3. File I/O operations
4. Rate limit checks

**Solutions:**
1. Cache LLM responses
2. Optimize database queries
3. Use async file operations
4. Use Redis for rate limiting

## Design Patterns

### 1. Strategy Pattern

**Used in:** Validators, Rate Limiters

```python
class ValidationStrategy:
    def validate(self, output: str) -> bool:
        pass

class JSONValidator(ValidationStrategy):
    def validate(self, output: str) -> bool:
        # JSON-specific validation
        pass
```

### 2. Observer Pattern

**Used in:** Event logging, Monitoring

```python
class EventObserver:
    def on_event(self, event: Event) -> None:
        pass

class AuditLogger(EventObserver):
    def on_event(self, event: Event) -> None:
        # Log to database
        pass
```

### 3. Factory Pattern

**Used in:** Model creation, Validator creation

```python
class ModelFactory:
    @staticmethod
    def create_model(model_type: str) -> Model:
        if model_type == "anthropic":
            return AnthropicModel()
        elif model_type == "openai":
            return OpenAIModel()
        # ...
```

### 4. Chain of Responsibility

**Used in:** Validation pipeline

```python
class Validator:
    def __init__(self, next_validator=None):
        self.next = next_validator
    
    def validate(self, output: str) -> bool:
        if self.check(output):
            if self.next:
                return self.next.validate(output)
            return True
        return False
```

### 5. Memento Pattern

**Used in:** Version control, Rollback

```python
class InstructionMemento:
    def __init__(self, state: str):
        self._state = state
    
    def get_state(self) -> str:
        return self._state

class InstructionManager:
    def save(self) -> InstructionMemento:
        return InstructionMemento(self._instructions)
    
    def restore(self, memento: InstructionMemento):
        self._instructions = memento.get_state()
```

### 6. Decorator Pattern

**Used in:** Security middleware, Caching

```python
@require_auth
@rate_limit(requests=100, window=60)
@cache(ttl=300)
def execute_query(query: str):
    # Execute query
    pass
```

## Extension Points

### Custom Validators

Implement `Validator` interface:

```python
class CustomValidator(Validator):
    def validate(self, output: str, context: dict) -> tuple[bool, str]:
        # Your validation logic
        return (success, message)
```

### Custom Models

Implement `Model` interface:

```python
class CustomModel(Model):
    def execute(self, query: str, instructions: str) -> str:
        # Your model logic
        return output
```

### Custom Storage

Implement storage interfaces:

```python
class CustomStorage:
    def save_instructions(self, content: str) -> None:
        pass
    
    def load_instructions(self) -> str:
        pass
```

### Custom Rate Limiters

Implement `RateLimiter` interface:

```python
class CustomRateLimiter(RateLimiter):
    def check_limit(self, key: str) -> bool:
        # Your rate limiting logic
        pass
```

## Deployment Architecture

### Development

```
Local Machine
├── Python application
├── SQLite database
├── Local file storage
└── Mock LLM models
```

### Production

```
┌─────────────────┐
│   Load Balancer │
│     (nginx)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ API 1 │ │ API 2 │
└───┬───┘ └──┬────┘
    │        │
    └────┬───┘
         │
    ┌────┴────────────┐
    │                 │
┌───▼─────────┐  ┌───▼────┐
│  PostgreSQL │  │ Redis  │
└─────────────┘  └────────┘
```

## Monitoring

**Metrics to Track:**
- Request rate
- Response time
- Error rate
- Optimization success rate
- Cache hit rate
- Database query time
- LLM API latency

**Tools:**
- Prometheus for metrics
- Grafana for visualization
- ELK stack for log analysis
- Sentry for error tracking

## Next Steps

- Review [Security Guide](security.md) for security architecture
- Check [API Reference](api-reference.md) for endpoint details
- See [Usage Guide](usage-guide.md) for practical examples
