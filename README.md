# Self-Optimizing Instruction Library

A LangChain-based system that learns from failures and automatically improves its own instructions through a critic-actor architecture. Now with enterprise-grade security features including authentication, authorization, rate limiting, and audit logging.

## Overview

This system implements a self-optimizing AI assistant that:
1. **Executes** user queries using current instructions (Actor/Main Model)
2. **Validates** outputs against configurable rules
3. **Learns** from failures by analyzing what went wrong
4. **Optimizes** its own instruction set to prevent similar failures
5. **Maintains** version history for rollback and audit

## Architecture

### Core Components

1. **MainModel (Actor)**: Executes user queries with current instructions
2. **CriticModel (Optimizer)**: Analyzes failures and proposes instruction updates
3. **InstructionManager**: Manages instruction files and version control
4. **ValidationPipeline**: Validates model outputs against configurable rules
5. **VersionController**: Maintains history of instruction changes

### Data Models

- `SystemConfig`: Configuration for the entire system
- `FailureEntry`: Represents a single failure with metadata
- `CriticResponse`: Structured output from the Critic model
- `VersionMetadata`: Tracks changes and version history

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd self_optimizing_system

# Install dependencies (if using LangChain)
pip install langchain langchain-anthropic
```

## Quick Start

```python
from self_optimizing_system import SelfOptimizingSystem, JSONValidator, LengthValidator

# Initialize system
system = SelfOptimizingSystem()

# Add validators
system.add_validator(JSONValidator(required_fields=["status", "result"]))
system.add_validator(LengthValidator(min_length=10, max_length=500))

# Execute query
result = system.execute("Generate a JSON status report")

print(f"Output: {result['output']}")
print(f"Validation passed: {result['validation_passed']}")

# If validation failed, system automatically learns from it
if not result['validation_passed'] and result.get('optimization_attempted'):
    print("System learned from failure and updated instructions!")
```

## Features

### Automatic Optimization
- Learns from validation failures
- Proposes instruction updates via Critic model
- Maintains safety by checking for conflicts
- Version-controlled changes with rollback capability

### Custom Validators
- JSON validation with required fields
- Length validation (min/max)
- Regex pattern matching
- Custom validation functions

### Version Control
- Git-style versioning of instructions
- Rollback to any previous version
- Audit trail of all changes
- Metadata tracking (who changed what and why)

### Failure Analysis
- Tiered compression of failure history
- Pattern detection for recurring issues
- Circuit breaker to prevent optimization loops
- Semantic similarity for finding related failures

## Configuration

```python
from self_optimizing_system import SystemConfig
from pathlib import Path

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

system = SelfOptimizingSystem(config)
```

## Advanced Usage

### Custom Validators
```python
from self_optimizing_system import CustomValidator
import re

def check_citation_format(output: str, context) -> bool:
    """Ensure citations are in [Author, Year] format"""
    pattern = r'\[[A-Z][a-z]+,\s*\d{4}\]'
    citations = re.findall(pattern, output)
    return len(citations) > 0

system.add_validator(CustomValidator("CitationValidator", check_citation_format))
```

### Manual Feedback
```python
# Provide manual feedback for instruction improvement
result = system.request_instruction_update(
    "The responses are too technical. Please use simpler language.",
    severity="moderate"
)
```

### Version Management
```python
# View version history
history = system.get_version_history()
for version in history:
    print(f"{version['version_id']}: {version['diff_summary']}")

# Rollback if needed
system.rollback(steps=2)  # Go back 2 versions
# or
system.rollback_to_version("v20250110_143000")
```

## Project Structure

```
self_optimizing_system/
├── src/
│   ├── core/
│   │   ├── main_model.py          # Main Actor model
│   │   ├── critic_model.py        # Optimization engine
│   │   ├── instruction_manager.py # Handles .md file operations
│   │   └── validator.py           # Auto-validation framework
│   ├── models/
│   │   ├── config.py              # Configuration dataclasses
│   │   ├── failure.py             # Failure log entries
│   │   ├── version.py             # Version control models
│   │   └── critic_response.py     # Structured Critic output
│   ├── storage/
│   │   ├── markdown_handler.py    # .md file I/O
│   │   └── version_control.py     # Git-style versioning
│   └── __init__.py                # Main interface
├── instructions/
│   ├── instructions.md            # Active state
│   ├── .versions/                 # Version history
│   ├── pending_review.md          # Failed optimizations
│   └── archived_failures.md       # Old failure log
├── examples/
│   └── basic_usage.py             # Usage examples
└── README.md
```

## Integration with LangChain

The system is designed to work with LangChain models and now supports multiple AI providers:

### Supported Providers

1. **Anthropic Claude** - Advanced reasoning and instruction following
2. **OpenAI GPT** - General-purpose language models
3. **Google Gemini** - Multi-modal AI capabilities
4. **Deepseek** - Efficient and cost-effective models
5. **Openrouter** - Access to multiple providers through one API

### Quick Setup

1. Install LangChain and provider packages:
```bash
pip install -r requirements.txt
```

2. Set up API keys in `.env`:
```bash
# Choose one or more providers
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

3. Configure your system:
```python
from src.models.config import SystemConfig
from src import SelfOptimizingSystem

config = SystemConfig(
    main_model="claude-3-5-sonnet-20241022",
    main_model_provider="anthropic",  # Optional: auto-detected
    critic_model="gpt-4-turbo-preview",
    critic_model_provider="openai",
)

system = SelfOptimizingSystem(config)
```

For detailed provider configuration, see [Provider Configuration Guide](docs/provider-configuration.md).

### Example Usage

```python
# Use different providers for main and critic models
config = SystemConfig(
    main_model="claude-3-5-sonnet-20241022",  # Anthropic
    critic_model="gpt-4-turbo-preview",       # OpenAI
)

system = SelfOptimizingSystem(config)
result = system.execute("Your query here")
```

See `examples/multi_provider_usage.py` for more examples.

## Limitations

- Mock models are used as fallback when API keys are not configured
- Semantic similarity features require additional setup (ChromaDB, sentence-transformers)
- File-based storage (not suitable for high-volume production)
- Some providers may have specific rate limits or model availability

## Security Features

### 🔐 Enterprise-Grade Security

The system now includes comprehensive security features:

#### **Authentication & Authorization**
- **JWT Token-based authentication** with refresh tokens
- **Role-based access control** (Admin, Editor, Viewer, API_Client)
- **Granular permissions** system for fine-grained access control
- **API Key management** with secure key generation and revocation

#### **Input Validation & Sanitization**
- **XSS prevention** with HTML sanitization
- **SQL injection detection** using pattern matching
- **Command injection prevention** for shell commands
- **JSON validation** with size and depth limits
- **Pydantic models** for type-safe input validation

#### **Rate Limiting**
- **Multiple strategies**: Fixed window, sliding window, token bucket
- **Redis support** for scalable rate limiting
- **API key-specific limits** with different quotas
- **Standard headers** (X-RateLimit-Limit, X-RateLimit-Remaining)

#### **Audit Logging & Monitoring**
- **Comprehensive audit trail** with 20+ event types
- **Security monitoring** for suspicious activity detection
- **Real-time alerts** for security events
- **Security reports** with recommendations

#### **Secure Web API**
- **Protected endpoints** requiring authentication
- **CORS configuration** with allowed origins
- **Security middleware** for request logging
- **Admin endpoints** for security management

### Security Configuration
```python
from src.security import SecurityConfig, RateLimitConfig

SECURITY_CONFIG = SecurityConfig(
    enable_authentication=True,
    enable_rate_limiting=True,
    enable_input_validation=True,
    enable_audit_logging=True,
    secret_key=os.getenv("SECRET_KEY"),
    rate_limit_config=RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
    ),
    allowed_origins=["http://localhost:3000", "http://localhost:8000"],
)
```

### Running the Secure API
```bash
# Run the secure API with all security features
cd web
python api_secure.py

# Or run the basic API (no security)
python api.py
```

## Future Enhancements

1. **Multi-tenant Support**: Tenant isolation and data separation
2. **Advanced Security**: Two-factor authentication, IP whitelisting
3. **Compliance Features**: GDPR tools, data retention policies
4. **Integration Features**: SSO support, OAuth2/OIDC integration
5. **Additional Providers**: Support for more AI providers (Cohere, AI21, etc.)
6. **Embedding Support**: Enhanced semantic similarity for failure analysis
7. **Database Backend**: Replace file storage with database
8. **Web Interface**: Add dashboard for monitoring and manual review
9. **Advanced Model Routing**: Automatic model selection based on task type
10. **Batch Processing**: Optimize multiple failures simultaneously

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.# autonomai
