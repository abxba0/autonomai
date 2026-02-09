# Content Moderation Platform

A production-ready, AI-powered content moderation system built with AutonomAI and DeepSeek. This platform demonstrates 85%+ of AutonomAI's features in a real-world SaaS application.

## 🎯 Overview

This is a complete content moderation platform that learns from human moderator decisions and continuously improves. It's designed as a multi-tenant SaaS where each community/platform can have custom moderation rules.

### Key Features

- 🏢 **Multi-Tenant Architecture**: Isolated moderation rules per community
- 🤖 **AI-Powered Detection**: Uses DeepSeek for intelligent content analysis
- 🔄 **Self-Learning**: Improves from moderator corrections and overrides
- 🔌 **Plugin System**: Custom moderation rules per tenant
- ⚡ **High Performance**: Caching for common patterns (1000x+ speedup)
- 📊 **Batch Processing**: Handle bulk content review efficiently
- 🔒 **Enterprise Security**: RBAC, audit logging, GDPR compliance
- 🌐 **Distributed Ready**: Redis-based state management
- 📈 **Analytics**: Comprehensive moderation metrics and trends

## 🏗️ Architecture

```
User Content → Validation → Classification → Decision → Action → Audit Log
                    ↓                                       ↓
              Human Override ←────── Learning System ──────┘
```

### Workflow Steps

1. **Content Ingestion**: Receive content for moderation
2. **Pre-Validation**: Check format, length, metadata
3. **AI Analysis**: DeepSeek analyzes for violations
4. **Multi-Validator Check**: Run all configured validators
5. **Decision Making**: Approve, flag, or reject
6. **Action Execution**: Apply moderation decision
7. **Audit Logging**: Record all decisions (GDPR compliant)
8. **Learning**: Update rules based on human overrides

## 🚀 Quick Start

### Prerequisites

```bash
# Install AutonomAI with web features
pip install -e ".[web]"

# Set up environment variables
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export REDIS_URL="redis://localhost:6379"  # Optional

# Start Redis (optional, for distributed features)
docker run -d -p 6379:6379 redis:latest
```

### Installation

```bash
cd examples/content_moderation_platform
pip install -r requirements.txt
```

### Run Interactive Demo

```bash
python demo.py
```

### Run as API Server

```bash
python api.py
# Access at http://localhost:8080
```

### Run CLI

```bash
python cli.py moderate --text "Your content here" --tenant gaming_community
```

## 📋 Usage Examples

### 1. Basic Moderation

```python
from engine import ModerationEngine

# Initialize engine
engine = ModerationEngine(tenant_id="gaming_community")

# Moderate content
result = engine.moderate_content(
    content="Check out my new gaming video!",
    content_type="comment",
    author_id="user123"
)

print(f"Decision: {result['decision']}")  # APPROVED
print(f"Confidence: {result['confidence']}")  # 0.95
```

### 2. Batch Moderation

```python
# Moderate multiple items
contents = [
    {"text": "Great game!", "type": "comment"},
    {"text": "Spam spam spam...", "type": "comment"},
    {"text": "Hate speech example", "type": "comment"}
]

results = engine.moderate_batch(contents)
for content, result in zip(contents, results):
    print(f"{content['text']}: {result['decision']}")
```

### 3. Human Override & Learning

```python
# AI decision
result = engine.moderate_content("Borderline content...")

# Human moderator override
engine.override_decision(
    content_id=result['content_id'],
    new_decision="APPROVED",
    moderator_id="mod_sarah",
    reason="Context: This is acceptable in our community"
)

# System learns from this override automatically!
```

### 4. Multi-Tenant Setup

```python
# Gaming community (lenient on competitive language)
gaming_engine = ModerationEngine(tenant_id="gaming_community")

# Professional forum (strict professionalism)
prof_engine = ModerationEngine(tenant_id="professional_forum")

# Same content, different decisions based on community standards
text = "You got destroyed in that match!"
gaming_result = gaming_engine.moderate_content(text)  # APPROVED
prof_result = prof_engine.moderate_content(text)      # FLAGGED
```

### 5. Custom Validators (Plugin System)

```python
from validators.custom_validator import CustomValidator

# Add community-specific rules
custom_validator = CustomValidator(
    banned_keywords=["specific_term", "another_term"],
    whitelist_patterns=[r"moderator:\w+"],
    severity_threshold=0.7
)

engine.add_validator(custom_validator)
```

## 🔧 Configuration

### Tenant Configuration (`config/tenant_configs.yaml`)

```yaml
gaming_community:
  name: "Gaming Community"
  moderation_level: "moderate"  # lenient, moderate, strict
  auto_approve_threshold: 0.9
  auto_reject_threshold: 0.3
  require_review_threshold: 0.6
  custom_rules:
    - allow_competitive_language: true
    - block_external_links: false

professional_forum:
  name: "Professional Forum"
  moderation_level: "strict"
  auto_approve_threshold: 0.95
  auto_reject_threshold: 0.5
  require_review_threshold: 0.8
  custom_rules:
    - allow_competitive_language: false
    - block_external_links: true
```

### Environment Variables

```bash
# Required
DEEPSEEK_API_KEY=your-deepseek-api-key

# Optional
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/moderation
CACHE_TTL=3600
BATCH_SIZE=100
LOG_LEVEL=INFO
```

## 📊 Validators

### Built-in Validators

1. **ProfanityValidator** (`validators/profanity_validator.py`)
   - Detects profane language
   - Configurable word lists
   - Context-aware scoring

2. **HateSpeechValidator** (`validators/hate_speech_validator.py`)
   - Identifies hate speech and discrimination
   - Multi-category detection
   - Severity scoring

3. **SpamValidator** (`validators/spam_validator.py`)
   - Detects spam patterns
   - Link analysis
   - Repetition detection

4. **ToxicityValidator** (`validators/toxicity_validator.py`)
   - Overall toxicity scoring
   - Combines multiple signals
   - Configurable thresholds

### Creating Custom Validators

```python
from src.plugins.base import ValidatorPlugin
from src.core.validator import ValidationResult

class MyCustomValidator(ValidatorPlugin):
    def validate(self, output: str, context: dict) -> ValidationResult:
        # Your validation logic
        if "banned_pattern" in output.lower():
            return ValidationResult(
                passed=False,
                message="Contains banned pattern"
            )
        return ValidationResult(passed=True)
```

## 🔄 Workflow Orchestration

The platform uses AutonomAI's workflow orchestrator for complex moderation flows:

```python
workflow_steps = [
    {
        "name": "preprocess",
        "type": "preprocessing",
        "action": "normalize_text"
    },
    {
        "name": "detect_violations",
        "type": "analysis",
        "action": "run_validators"
    },
    {
        "name": "classify_severity",
        "type": "classification",
        "action": "determine_severity"
    },
    {
        "name": "make_decision",
        "type": "decision",
        "action": "apply_rules",
        "conditions": [
            {"if": "severity > 0.8", "then": "reject"},
            {"if": "severity < 0.3", "then": "approve"},
            {"else": "flag_for_review"}
        ]
    },
    {
        "name": "execute_action",
        "type": "action",
        "action": "apply_moderation"
    }
]
```

## 📈 Analytics & Reporting

### View Moderation Stats

```python
# Get tenant statistics
stats = engine.get_moderation_stats(
    tenant_id="gaming_community",
    date_range="last_7_days"
)

print(f"Total Moderated: {stats['total']}")
print(f"Auto-Approved: {stats['approved']}")
print(f"Rejected: {stats['rejected']}")
print(f"Flagged for Review: {stats['flagged']}")
print(f"Override Rate: {stats['override_rate']}")
```

### Export Audit Logs (GDPR)

```python
# Export all decisions for a user
audit_log = engine.export_user_data(user_id="user123")

# Export tenant data
tenant_data = engine.export_tenant_data(
    tenant_id="gaming_community",
    start_date="2026-01-01",
    end_date="2026-01-31"
)
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_moderation.py::test_profanity_detection -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Categories

- Unit tests for validators
- Integration tests for workflow
- Multi-tenant isolation tests
- Performance benchmarks
- Load tests

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build image
docker build -t content-moderation-platform .

# Run container
docker run -d \
  -p 8080:8080 \
  -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
  -e REDIS_URL=redis://redis:6379 \
  --name moderation-api \
  content-moderation-platform
```

### Kubernetes Deployment

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### Scaling Considerations

1. **Horizontal Scaling**: Run multiple API instances behind load balancer
2. **Redis Cluster**: Use Redis Cluster for distributed caching
3. **Database**: PostgreSQL with connection pooling
4. **Celery Workers**: Separate workers for batch processing
5. **Monitoring**: Prometheus + Grafana dashboards

## 📚 API Reference

### REST API Endpoints

```
POST   /api/v1/moderate              - Moderate single content
POST   /api/v1/moderate/batch        - Moderate multiple items
GET    /api/v1/moderation/{id}       - Get moderation result
POST   /api/v1/override/{id}         - Override decision
GET    /api/v1/stats/{tenant_id}     - Get tenant statistics
GET    /api/v1/export/{tenant_id}    - Export data (GDPR)
POST   /api/v1/tenants                - Create tenant
GET    /api/v1/tenants/{id}          - Get tenant info
PUT    /api/v1/tenants/{id}          - Update tenant config
```

### Authentication

```bash
# Get API token
curl -X POST http://localhost:8080/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token
curl -X POST http://localhost:8080/api/v1/moderate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Content to moderate", "tenant_id": "gaming_community"}'
```

## 🔒 Security Features

- **RBAC**: Role-based access control (Admin, Moderator, Viewer)
- **API Authentication**: JWT tokens with expiry
- **Rate Limiting**: Prevent abuse (configurable per tenant)
- **Input Validation**: All inputs sanitized
- **Audit Logging**: All actions logged for compliance
- **GDPR Compliance**: Data export, deletion, anonymization
- **Encryption**: Sensitive data encrypted at rest

## 📊 Performance Benchmarks

| Operation | Without Cache | With Cache | Speedup |
|-----------|--------------|------------|---------|
| Single Moderation | ~800ms | ~0.8ms | 1000x |
| Batch (100 items) | ~45s | ~5s | 9x |
| Validator Check | ~200ms | ~0.2ms | 1000x |

## 🎓 Learning & Optimization

The system learns from:

1. **Human Overrides**: Moderator corrections update rules
2. **Appeal Outcomes**: Appeal decisions refine classification
3. **User Reports**: Community feedback improves detection
4. **False Positives**: Auto-approved items later reported
5. **Consistency Patterns**: Different moderators' decisions

### Viewing Learning Progress

```python
# Check instruction improvements
history = engine.get_instruction_history()

for version in history:
    print(f"Version {version['version']}: {version['changes']}")
    print(f"  Accuracy: {version['metrics']['accuracy']}")
    print(f"  Override Rate: {version['metrics']['override_rate']}")
```

## 🤝 Contributing

Contributions welcome! Areas of interest:

- New validators (sentiment, sarcasm, context)
- Language support (currently English-focused)
- Integration with moderation tools (Discord, Reddit, etc.)
- Performance optimizations
- Additional test coverage

## 📄 License

This example is part of AutonomAI and follows the same MIT license.

## 🔗 Links

- [AutonomAI Documentation](../../docs/README.md)
- [Multi-Tenant Guide](../../docs/MULTI_TENANT.md)
- [Plugin Development](../../docs/plugin-system.md)
- [Workflow Orchestration](../../docs/architecture.md)

## 💡 Use Cases

This platform can be adapted for:

- Social media platforms (Twitter, Instagram clones)
- Gaming communities (Discord, Steam)
- Forums and discussion boards
- E-commerce reviews
- Educational platforms (homework plagiarism)
- Corporate collaboration tools
- Dating apps
- Marketplace listings

## 🆘 Support

For issues or questions:
1. Check the [troubleshooting guide](#troubleshooting)
2. Review [common issues](../../docs/troubleshooting.md)
3. Open an [issue](https://github.com/abxba0/autonomai/issues)

---

**Built with ❤️ using AutonomAI + DeepSeek**
