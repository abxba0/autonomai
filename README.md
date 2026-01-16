# autonomai⛭

A LangChain-based system that learns from failures and automatically improves its own instructions through a critic-actor architecture. Now with enterprise-grade security features, implicit negative feedback detection, and context-based rule extraction.

## Overview

This system implements a self-optimizing AI assistant that:
1. **Executes** user queries using current instructions (Actor/Main Model)
2. **Validates** outputs against configurable rules
3. **Detects** implicit corrections and dissatisfaction automatically
4. **Learns** from failures by analyzing what went wrong
5. **Extracts** rules from conversation patterns and user feedback
6. **Optimizes** its own instruction set to prevent similar failures
7. **Maintains** version history for rollback and audit

## Key Features

### 🔄 Automatic Optimization
- Learns from validation failures
- Proposes instruction updates via Critic model
- Maintains safety by checking for conflicts
- Version-controlled changes with rollback capability

### 🔌 Production-Grade Plugin System (NEW)
- **Extensible Architecture**: Extend validators, optimizers, and workflow steps
- **Multiple Discovery Methods**: Entry points, directory scanning, configuration files
- **Lifecycle Management**: Complete plugin lifecycle (load, initialize, activate, cleanup)
- **Runtime Loading**: Discover and load plugins at runtime
- **Example Plugins**: Includes working examples for validators, analyzers, and workflow steps
- **Full Documentation**: Comprehensive guides for plugin development

### 🎯 Implicit Negative Feedback Detection
- **NEW**: Automatically detects when users correct the AI or express dissatisfaction
- Recognizes patterns like "No, that's not right", "That doesn't help", etc.
- Triggers optimization pipeline without explicit feedback commands
- Configurable confidence thresholds

### 📊 Context-Based Rule Extraction
- **NEW**: `/feedback-context` command analyzes conversation history
- Extracts both positive ("DO") and negative ("DON'T") rules
- Identifies user preferences and recurring patterns
- Available in terminal chatbot and web API

### ✅ Custom Validators
- JSON validation with required fields
- Length validation (min/max)
- Regex pattern matching
- Custom validation functions

### 🔀 Autonomous Workflow Orchestrator (NEW)
- **Planner-Executor-Critic Pattern**: Dynamic multi-step workflow automation
- **Dynamic Planning**: Generates workflow plans from high-level goals using specialized Planner LLM
- **Specialized Execution**: Executes steps with role-specific Actor instructions
- **Self-Optimizing**: Learns from workflow failures to improve both planning and execution
- **Trajectory Correction**: Optimizes entire workflow patterns, not just individual steps
- **Granular Versioning**: Separate version control for planner and actor instructions
- **Failure Analysis**: Distinguishes between planning failures and execution failures
- **Automatic Recovery**: Retries failed steps with optimized instructions

## Architecture

### Core Components

1. **MainModel (Actor)**: Executes user queries with current instructions
2. **CriticModel (Optimizer)**: Analyzes failures and proposes instruction updates
3. **CorrectionDetector**: Detects implicit corrections in user messages
4. **ContextAnalyzer**: Extracts rules from conversation patterns
5. **InstructionManager**: Manages instruction files and version control
6. **ValidationPipeline**: Validates model outputs against configurable rules
7. **VersionController**: Maintains history of instruction changes
8. **WorkflowOrchestrator**: Orchestrates multi-step workflows with Planner-Executor-Critic pattern
9. **PluginManager (NEW)**: Manages plugin discovery, loading, and lifecycle

### Data Models

- `SystemConfig`: Configuration for the entire system
- `FailureEntry`: Represents a single failure with metadata (supports `implicit_feedback` trigger)
- `CriticResponse`: Structured output from the Critic model
- `VersionMetadata`: Tracks changes and version history
- `WorkflowPlan`: Multi-step workflow with dependencies and execution state
- `WorkflowStep`: Individual step in a workflow with status tracking
- `WorkflowFailure`: Failure context for Critic analysis with planning/execution distinction

## Installation

### Basic Installation (Cloud AI Only)

For minimal installation with cloud AI providers only:

```bash
# Clone the repository
git clone <repository-url>
cd self_optimizing_system

# Install core dependencies only
pip install -r requirements.txt
# Or install as package
pip install -e .
```

### Optional Features

Install additional features as needed:

```bash
# For web API and security features (FastAPI, JWT, Redis)
pip install -e ".[web]"

# For local AI embeddings (ChromaDB, sentence-transformers)
pip install -e ".[local]"

# For multi-modal features (vision, audio processing)
pip install -e ".[multimodal]"

# Install everything
pip install -e ".[all]"
```

**Modular Dependencies:**
- **Base**: Core logic, cloud AI providers (Anthropic, OpenAI, Google), SQLAlchemy
- **Web**: FastAPI, Uvicorn, JWT authentication, Redis, input sanitization
- **Local**: ChromaDB vector database, sentence-transformers for embeddings
- **Multimodal**: Pillow, OpenCV, EasyOCR, PyDub, Transformers for vision/audio processing

The system gracefully falls back to simpler alternatives if optional dependencies are missing.

## Quick Start

### Basic Usage

```python
from src import SelfOptimizingSystem, JSONValidator, LengthValidator

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

### Using Implicit Correction Detection

```python
from src import SelfOptimizingSystem, SystemConfig

# Enable correction detection
config = SystemConfig(
    enable_correction_detection=True,
    enable_auto_optimization=True
)
system = SelfOptimizingSystem(config)

# User interacts normally
result = system.execute("What is 2+2?")
# ... bot responds ...

# User implicitly corrects (automatically detected!)
result = system.execute("No, that's not right")

if result.get("correction_detected"):
    print(f"Correction detected! Confidence: {result['correction_confidence']:.2f}")
    print("System is learning from your feedback...")
```

### Using Context-Based Rule Extraction

```python
# After a conversation...
conversation_history = [
    {"role": "user", "content": "I prefer concise answers"},
    {"role": "assistant", "content": "Understood."},
    {"role": "user", "content": "Don't use technical jargon"},
    {"role": "assistant", "content": "Got it."},
]

# Analyze and extract rules
result = system.analyze_feedback_context(
    conversation_history,
    auto_apply=True  # Automatically apply extracted rules
)

print(f"Extracted {result['rules_count']} positive rules")
print(f"Extracted {result['dont_rules_count']} negative rules")
print(result['formatted_display'])  # Show detailed analysis
```

### Using the Workflow Orchestrator (NEW)

```python
from src import SelfOptimizingSystem

# Initialize system
system = SelfOptimizingSystem()

# Execute a multi-step workflow from a high-level goal
result = system.execute_workflow(
    goal="Research and create a comprehensive report on autonomous AI agents",
    context={
        "output_format": "markdown report",
        "focus_areas": ["capabilities", "challenges", "future directions"],
        "target_length": "1500-2000 words"
    },
    max_retries=3  # Automatic retry with optimized instructions on failure
)

print(f"Workflow Status: {result['status']}")
print(f"Steps Completed: {result['steps_completed']}/{result['total_steps']}")

# Access detailed workflow information
workflow = result['workflow']
print(f"Workflow Plan: {workflow['name']}")
print(f"Planner Version: {workflow['planner_version']}")
print(f"Actor Version: {workflow['actor_version']}")

# Review step execution
for step_result in result['results']:
    print(f"Step {step_result['step_id']}: {step_result['status']}")
    if step_result['success']:
        print(f"  Outputs: {step_result['outputs']}")
```

**Key Workflow Features:**
- **Dynamic Planning**: The Planner LLM analyzes your goal and creates a multi-step plan
- **Dependency Management**: Steps execute in proper order based on dependencies
- **Automatic Recovery**: If a step fails, the Critic determines if it was a planning or execution issue
- **Targeted Optimization**: Failures improve either planner.md or actor.md instructions accordingly
- **Version Tracking**: Separate versioning for planning and execution strategies

See `examples/autonomous_researcher.py` for a complete workflow demo.

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
from src import SystemConfig
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
    
    # Implicit feedback / correction detection
    enable_correction_detection=True,
    correction_detection_confidence_threshold=0.7,
    
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

## Plugin System

### Overview

AutonomAI features a production-grade plugin system that enables developers to extend the system with custom:
- **Validators**: Custom validation logic for model outputs
- **Optimizers**: Custom failure analysis and instruction optimization
- **Workflow Steps**: Custom step executors for workflows

### Quick Start

```python
from src.plugins import PluginManager, ValidatorPlugin, PluginMetadata

# Create a custom validator plugin
class MyValidatorPlugin(ValidatorPlugin):
    @classmethod
    def get_metadata(cls):
        return PluginMetadata(
            name="my_validator",
            version="1.0.0",
            author="Your Name",
            description="Custom validator",
            plugin_type="validator"
        )
    
    def create_validator(self):
        # Return your validator implementation
        pass

# Load and use plugins
manager = PluginManager()
manager.discover_and_load_plugins(
    plugin_dirs=[Path("./plugins")],
    config_file=Path("./plugin_config.yaml")
)

# Integrate with system
system = SelfOptimizingSystem()
for validator in manager.get_validators_for_pipeline():
    system.add_validator(validator)
```

### Plugin Discovery Methods

1. **Entry Points** (recommended for distribution):
   ```python
   # setup.py
   entry_points={
       "autonomai.plugins": [
           "my_plugin = my_package.plugin:MyPlugin",
       ],
   }
   ```

2. **Directory Scanning**:
   ```python
   manager.discover_and_load_plugins(plugin_dirs=[Path("./plugins")])
   ```

3. **Configuration File** (YAML/JSON):
   ```yaml
   plugins:
     - name: my_validator
       module: my_package.plugin
       class: MyValidatorPlugin
       config:
         enabled: true
         priority: 50
   ```

### Example Plugins

The repository includes example plugins demonstrating best practices:

- **Keyword Validator**: Validates required and forbidden keywords
- **Pattern Analyzer**: Extracts patterns from failure logs
- **Data Transform Step**: Custom workflow step for data transformations
- **Failure Frequency Analyzer**: Analyzes failure timing patterns

See `examples/plugins/` for complete implementations.

### Documentation

- [Plugin System Guide](docs/plugin-system.md) - Complete architecture and API reference
- [Plugin Quick Start](examples/plugins/README.md) - Quick reference for developers
- [Plugin Demo](examples/plugin_system_demo.py) - Working demonstration

### Running the Demo

```bash
python examples/plugin_system_demo.py
```

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

#### **UK GDPR Compliance** ✨ NEW
- **Complete implementation** of UK GDPR and Data Protection Act 2018
- **User Rights API**: Access, erasure, portability, rectification
- **Consent Management**: Track and manage user consents
- **Data Protection**: Encryption, minimization, retention policies
- **Third-Party Compliance**: AI provider data processing agreements
- **Comprehensive Documentation**: Privacy policy and compliance guides

#### **Secure Web API**
- **Protected endpoints** requiring authentication
- **CORS configuration** with allowed origins
- **Security middleware** for request logging
- **Admin endpoints** for security management

### UK GDPR Compliance

The system is fully compliant with UK data protection regulations:

**User Rights Implementation:**
- Right to Access (Article 15) - `/gdpr/access` and `/gdpr/export`
- Right to Erasure (Article 17) - `/gdpr/delete`
- Right to Data Portability (Article 20) - `/gdpr/export`
- Right to Rectification (Article 16) - `/gdpr/rectify`
- Consent Management - `/gdpr/consent/*`

**Data Protection Measures:**
- Encryption in transit (TLS 1.3) and at rest
- Secure password hashing (bcrypt/argon2)
- Comprehensive audit logging (7-year retention)
- Automated data retention and deletion
- Privacy by design and by default

**Documentation:**
- [UK GDPR Compliance Guide](docs/uk-gdpr-compliance.md)
- [Privacy Policy](docs/PRIVACY_POLICY.md)
- [Security Guide](docs/security.md)

**Third-Party Data Processors:**
- Anthropic Claude, OpenAI, Google Gemini, Deepseek, Openrouter
- Data Processing Agreements required
- International transfer safeguards
- User control over provider selection

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

## Multi-Tenant Support ✨ NEW

The system now includes production-ready multi-tenant support with complete tenant isolation:

### Key Features
- **Complete Data Isolation**: Strict separation at database, file, and log levels
- **Flexible Plans**: Free, Starter, Professional, Enterprise tiers with customizable limits
- **Usage Tracking**: Real-time metering for requests, tokens, and costs
- **Billing-Ready**: Export usage data in billing-ready format
- **Admin API**: Comprehensive tenant management, onboarding, and monitoring
- **Tenant Configuration**: Per-tenant API keys, models, and feature flags

### Quick Start
```python
from src.storage import TenantManager, UsageTracker

# Create and onboard tenant
result = tenant_manager.onboard_tenant(
    name="Acme Corp",
    email="admin@acme.com",
    plan=TenantPlan.PROFESSIONAL,
    api_keys={"anthropic_api_key": "sk-..."}
)

# Track usage
usage_tracker.record_request(
    tenant_id="tenant_abc123",
    tokens_used=1000,
    success=True,
    model_used="claude-3-sonnet"
)

# Get billing data
billing = usage_tracker.export_usage_for_billing(
    tenant_id="tenant_abc123",
    start_date=period_start,
    end_date=period_end
)
```

### Admin API
Run the tenant management API:
```bash
python web/api_tenant_management.py
```

See [Multi-Tenant Documentation](docs/MULTI_TENANT.md) for complete details.

## Future Enhancements

1. ~~**Multi-tenant Support**: Tenant isolation and data separation~~ ✅ **IMPLEMENTED**
2. **Advanced Security**: Two-factor authentication, IP whitelisting
3. **Integration Features**: SSO support, OAuth2/OIDC integration
4. **Additional Providers**: Support for more AI providers (Cohere, AI21, etc.)
5. **Embedding Support**: Enhanced semantic similarity for failure analysis
6. ~~**Database Backend**: Replace file storage with database~~ ✅ **IMPLEMENTED** (optional, file-based still supported)
7. **Web Interface**: Add dashboard for monitoring and manual review
8. **Advanced Model Routing**: Automatic model selection based on task type
9. **Batch Processing**: Optimize multiple failures simultaneously
10. **Automated Compliance Reporting**: Generate compliance reports for auditors

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
