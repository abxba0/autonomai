# AutonomAI Documentation

Welcome to the AutonomAI documentation! This guide will help you understand, install, and use the self-optimizing AI system effectively.

## 📚 Quick Navigation

### 🚀 Getting Started (Start Here!)
| Document | Description |
|----------|-------------|
| [Setup Guide](getting-started/setup-guide.md) | Installation, configuration, and initial setup |
| [Getting Started](../GETTING_STARTED.md) | Quick start guide in the main repo |
| [Usage Guide](getting-started/usage-guide.md) | How to use the system with examples |
| [Troubleshooting](getting-started/troubleshooting.md) | Common issues and solutions |
| [Examples](../examples/README.md) | Code examples and demos |

### 📖 Guides
| Document | Description |
|----------|-------------|
| [Architecture](guides/architecture.md) | System design and workflow orchestration |
| [API Reference](guides/api-reference.md) | Complete API documentation |
| [Provider Configuration](guides/provider-configuration.md) | Configure AI providers (Anthropic, OpenAI, etc.) |
| [Feedback Features](guides/feedback-features.md) | Implicit correction detection and context analysis |
| [Caching Guide](guides/caching-guide.md) | Production-grade caching for performance |
| [Batch Processing](guides/batch-processing.md) | Celery-based async job processing |
| [Plugin System](guides/plugin-system.md) | Extensible plugin architecture |
| [Multi-Tenant Support](guides/multi-tenant.md) | Tenant isolation and management |
| [Distributed Deployment](guides/distributed-deployment.md) | Horizontal scaling, load balancing, Kubernetes |

### 🔒 Security & Compliance
| Document | Description |
|----------|-------------|
| [Security Guide](security/security.md) | Authentication, authorization, rate limiting |
| [GDPR Quick Start](security/gdpr-quick-start.md) | Comprehensive GDPR compliance guide with checklists |
| [GDPR API Integration](security/gdpr-api-integration.md) | User rights API implementation |
| [Privacy Policy](security/privacy-policy.md) | User data handling policies |
| [Staff Training](security/staff-training.md) | GDPR staff training guide |

### 🛠️ Development
| Document | Description |
|----------|-------------|
| [Contributing Guide](contributing.md) | Development and contribution guidelines |

---

## 🎯 Quick Start Paths

### For New Users
1. 📖 Read [Getting Started](../GETTING_STARTED.md)
2. ⚙️ Follow [Setup Guide](getting-started/setup-guide.md)
3. 💡 Try [Basic Usage Example](../examples/basic_usage.py)
4. 📚 Review [Usage Guide](getting-started/usage-guide.md)

### For Developers
1. 🏗️ Understand the [Architecture](guides/architecture.md)
2. 🔌 Check [API Reference](guides/api-reference.md)
3. 🧩 Explore [Plugin System](guides/plugin-system.md)
4. 🤝 Read [Contributing Guide](contributing.md)

### For Production Deployment
1. 🌐 Review [Distributed Deployment](guides/distributed-deployment.md)
2. 🔒 Implement [Security Guide](security/security.md)
3. 📊 Set up [Caching](guides/caching-guide.md)
4. ⚡ Configure [Batch Processing](guides/batch-processing.md)

### For Enterprise/SaaS
1. 🏢 Set up [Multi-Tenant Support](guides/multi-tenant.md)
2. ⚖️ Ensure [GDPR Compliance](security/gdpr-quick-start.md)
3. 🔐 Configure [Security](security/security.md)
4. 📈 Monitor with [Batch Processing](guides/batch-processing.md)

---

## 💡 What is AutonomAI?

AutonomAI is a LangChain-based self-optimizing AI system that learns from failures and automatically improves its own instructions through a critic-actor architecture.

### Key Features

#### 🔄 Self-Optimizing Architecture
- **Actor-Critic Pattern**: Main model executes queries while Critic analyzes failures
- **Automatic Learning**: System learns from validation failures
- **Version Control**: Git-style versioning with rollback
- **Validation Pipeline**: JSON, regex, length, custom validators

#### 🎯 Advanced Learning
- **Implicit Correction Detection**: Detects user corrections automatically
- **Context-Based Rules**: Extracts DO/DON'T rules from conversations
- **Semantic De-duplication**: Prevents redundant rules
- **Golden Dataset Testing**: Regression testing for quality

#### 🔀 Autonomous Workflows
- **Planner-Executor-Critic**: Dynamic multi-step automation
- **Conditional Logic**: if/else and switch/case branching
- **Loop Constructs**: while, for, foreach iteration
- **Sub-Workflows**: Modular, reusable components

#### 🚀 Production Features
- **Distributed System**: Horizontal scaling with Redis coordination
- **Caching Layer**: 1000x+ speedup for repeated queries
- **Batch Processing**: Celery-based async job queue
- **Multi-Tenant**: Complete tenant isolation
- **Plugin System**: Extensible architecture

#### 🔒 Enterprise Security
- **JWT Authentication**: Token-based auth with RBAC
- **Rate Limiting**: Multiple strategies (fixed, sliding, token bucket)
- **Input Validation**: XSS, SQL injection, command injection prevention
- **UK GDPR Compliance**: Full data protection compliance
- **Audit Logging**: Comprehensive event tracking

#### 🔌 Multi-Provider Support
- Anthropic Claude (Opus, Sonnet, Haiku)
- OpenAI GPT (4, 4-Turbo, 3.5-Turbo)
- Google Gemini (Pro, 1.5)
- DeepSeek (Chat, Coder)
- OpenRouter (unified access)

---

## 📖 Documentation by Topic

### Core Functionality
- [Architecture Overview](guides/architecture.md)
- [Usage Patterns](getting-started/usage-guide.md)
- [Feedback & Learning](guides/feedback-features.md)
- [Validation Pipeline](getting-started/usage-guide.md#validation)

### Workflow Automation
- [Workflow Orchestration](guides/architecture.md)
- [Planner-Executor-Critic Pattern](guides/architecture.md)
- [Conditional Branching](guides/architecture.md)
- [Loop Constructs](guides/architecture.md)

### Performance & Scalability
- [Caching Strategies](guides/caching-guide.md)
- [Batch Processing](guides/batch-processing.md)
- [Distributed Deployment](guides/distributed-deployment.md)

### Extensibility
- [Plugin Development](guides/plugin-system.md)
- [Custom Validators](getting-started/usage-guide.md#custom-validators)
- [Provider Integration](guides/provider-configuration.md)
- [API Extensions](guides/api-reference.md)

### Security & Compliance
- [Authentication & Authorization](security/security.md)
- [Rate Limiting](security/security.md#rate-limiting)
- [GDPR Compliance Guide](security/gdpr-quick-start.md)
- [Audit Logging](security/security.md#audit-logging)

### Testing & Quality
- Unit Testing - See `tests/` directory
- Integration Testing - See `tests/` directory
- Load Testing - See `tests/test_load_stress_comprehensive.py`
- Chaos Engineering - See `tests/test_chaos_engineering.py`

---

## 🆘 Getting Help

### Documentation Issues
- Check the [Troubleshooting Guide](getting-started/troubleshooting.md)
- Review [Common Issues](getting-started/troubleshooting.md#common-issues)
- Search [closed issues](https://github.com/abxba0/autonomai/issues?q=is%3Aissue+is%3Aclosed)

### Feature Requests
- Check [existing issues](https://github.com/abxba0/autonomai/issues)
- Review the [Contributing Guide](contributing.md)
- Open a [new issue](https://github.com/abxba0/autonomai/issues/new)

### Community Support
- [GitHub Discussions](https://github.com/abxba0/autonomai/discussions)
- [Issue Tracker](https://github.com/abxba0/autonomai/issues)
- [Contributing Guidelines](contributing.md)

---

## 📋 System Requirements

### Minimum Requirements
- Python 3.8 or higher
- pip package manager
- 2GB RAM
- 1GB disk space

### Recommended for Production
- Python 3.10 or higher
- 8GB+ RAM
- PostgreSQL or MySQL
- Redis 6.0+
- Docker & Kubernetes

### Optional Dependencies
- **Web Features**: FastAPI, JWT, Redis
- **Local AI**: ChromaDB, sentence-transformers
- **Multi-Modal**: Pillow, OpenCV, PyDub
- **Security**: Passlib, python-jose

See [Setup Guide](getting-started/setup-guide.md) for detailed installation instructions.

---

## 🔗 External Resources

- [Main README](../README.md) - Project overview
- [CHANGELOG](../CHANGELOG.md) - Version history
- [GitHub Repository](https://github.com/abxba0/autonomai)
- [Issue Tracker](https://github.com/abxba0/autonomai/issues)
- [Examples Directory](../examples/README.md)

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](contributing.md) before submitting PRs.

### Quick Contribution Steps
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [Contributing Guide](contributing.md) for detailed instructions.

---

**Last Updated**: 2026-01-24

*This documentation is continuously improved. If you find any issues or have suggestions, please [open an issue](https://github.com/abxba0/autonomai/issues/new).*
