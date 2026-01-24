# AutonomAI Documentation

Welcome to the AutonomAI documentation! This guide will help you understand, install, and use the self-optimizing AI system effectively.

## 📚 Quick Navigation

### 🚀 Getting Started (Start Here!)
| Document | Description |
|----------|-------------|
| [Setup Guide](setup-guide.md) | Installation, configuration, and initial setup |
| [Getting Started](../GETTING_STARTED.md) | Quick start guide in the main repo |
| [Usage Guide](usage-guide.md) | How to use the system with examples |
| [Examples](../examples/README.md) | Code examples and demos |

### 🏗️ Core Concepts
| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System design and component overview |
| [API Reference](api-reference.md) | Complete API documentation |
| [Provider Configuration](provider-configuration.md) | Configure AI providers (Anthropic, OpenAI, etc.) |
| [Feedback Features](feedback-features.md) | Implicit correction detection and context analysis |

### 🔄 Advanced Features
| Document | Description |
|----------|-------------|
| [Workflow Orchestration](ENHANCED_WORKFLOW_ORCHESTRATION.md) | Planner-Executor-Critic pattern, conditionals, loops |
| [Caching Guide](caching-guide.md) | Production-grade caching for performance |
| [Batch Processing](batch-processing.md) | Celery-based async job processing |
| [Plugin System](plugin-system.md) | Extensible plugin architecture |
| [Multi-Tenant Support](MULTI_TENANT.md) | Tenant isolation and management |

### 🌐 Distributed & Production
| Document | Description |
|----------|-------------|
| [Distributed Deployment](distributed-deployment.md) | Horizontal scaling, load balancing, Kubernetes |
| [API v2 Migration](api_v2_migration.md) | Migrate from v1 to v2 API |
| [Comprehensive Testing](COMPREHENSIVE_TESTING.md) | Unit, integration, load, and chaos testing |

### 🔒 Security & Compliance
| Document | Description |
|----------|-------------|
| [Security Guide](security.md) | Authentication, authorization, rate limiting |
| [UK GDPR Compliance](uk-gdpr-compliance.md) | Full GDPR compliance guide |
| [GDPR Quick Start](GDPR_QUICK_START.md) | Quick GDPR implementation guide |
| [GDPR API Integration](gdpr-api-integration.md) | User rights API |
| [UK GDPR Checklist](uk-gdpr-compliance-checklist.md) | Compliance verification checklist |
| [Privacy Policy](PRIVACY_POLICY.md) | User data handling policies |

### 🛠️ Development
| Document | Description |
|----------|-------------|
| [Contributing Guide](contributing.md) | Development and contribution guidelines |
| [Epic Implementation](epic-implementation.md) | Implementation details of major features |
| [Phases 5-7 Implementation](phases-5-7-implementation.md) | Multi-modal, knowledge graph, multi-tenant |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

---

## 🎯 Quick Start Paths

### For New Users
1. 📖 Read [Getting Started](../GETTING_STARTED.md)
2. ⚙️ Follow [Setup Guide](setup-guide.md)
3. 💡 Try [Basic Usage Example](../examples/basic_usage.py)
4. 📚 Review [Usage Guide](usage-guide.md)

### For Developers
1. 🏗️ Understand the [Architecture](architecture.md)
2. 🔌 Check [API Reference](api-reference.md)
3. 🧩 Explore [Plugin System](plugin-system.md)
4. 🤝 Read [Contributing Guide](contributing.md)

### For Production Deployment
1. 🌐 Review [Distributed Deployment](distributed-deployment.md)
2. 🔒 Implement [Security Guide](security.md)
3. 📊 Set up [Caching](caching-guide.md)
4. ⚡ Configure [Batch Processing](batch-processing.md)
5. ✅ Run [Comprehensive Testing](COMPREHENSIVE_TESTING.md)

### For Enterprise/SaaS
1. 🏢 Set up [Multi-Tenant Support](MULTI_TENANT.md)
2. ⚖️ Ensure [GDPR Compliance](uk-gdpr-compliance.md)
3. 🔐 Configure [Security](security.md)
4. 📈 Monitor with [Batch Processing](batch-processing.md)

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
- [Architecture Overview](architecture.md)
- [Usage Patterns](usage-guide.md)
- [Feedback & Learning](feedback-features.md)
- [Validation Pipeline](usage-guide.md#validation)

### Workflow Automation
- [Workflow Orchestration](ENHANCED_WORKFLOW_ORCHESTRATION.md)
- [Planner-Executor-Critic Pattern](ENHANCED_WORKFLOW_ORCHESTRATION.md#planner-executor-critic-pattern)
- [Conditional Branching](ENHANCED_WORKFLOW_ORCHESTRATION.md#conditional-branching)
- [Loop Constructs](ENHANCED_WORKFLOW_ORCHESTRATION.md#loop-constructs)

### Performance & Scalability
- [Caching Strategies](caching-guide.md)
- [Batch Processing](batch-processing.md)
- [Distributed Deployment](distributed-deployment.md)
- [Load Testing](COMPREHENSIVE_TESTING.md#load-stress-tests)

### Extensibility
- [Plugin Development](plugin-system.md)
- [Custom Validators](usage-guide.md#custom-validators)
- [Provider Integration](provider-configuration.md)
- [API Extensions](api-reference.md)

### Security & Compliance
- [Authentication & Authorization](security.md)
- [Rate Limiting](security.md#rate-limiting)
- [GDPR Compliance](uk-gdpr-compliance.md)
- [Audit Logging](security.md#audit-logging)

### Testing & Quality
- [Unit Testing](COMPREHENSIVE_TESTING.md#unit-tests)
- [Integration Testing](COMPREHENSIVE_TESTING.md#integration-tests)
- [Load Testing](COMPREHENSIVE_TESTING.md#load-stress-tests)
- [Chaos Engineering](COMPREHENSIVE_TESTING.md#chaos-engineering-tests)

---

## 🆘 Getting Help

### Documentation Issues
- Check the [Troubleshooting Guide](troubleshooting.md)
- Review [Common Issues](troubleshooting.md#common-issues)
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

See [Setup Guide](setup-guide.md) for detailed installation instructions.

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
