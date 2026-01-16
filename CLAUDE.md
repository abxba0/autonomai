# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutonomAI is a LangChain-based self-optimizing AI system that learns from failures and automatically improves its own instructions through a critic-actor architecture. The system implements a Planner-Executor-Critic pattern for workflow orchestration with automatic optimization.

## Build & Development Commands

```bash
# Install dependencies (core only)
pip install -r requirements.txt

# Install with optional features
pip install -e ".[web]"       # FastAPI, JWT, Redis
pip install -e ".[local]"     # ChromaDB, sentence-transformers
pip install -e ".[multimodal]" # Vision/audio processing
pip install -e ".[all]"       # Everything

# Run tests
pytest tests/ -v                                    # All tests
pytest tests/test_unit_core_comprehensive.py -v    # Unit tests only
pytest tests/test_unit_core_comprehensive.py -v -k "test_json"  # Run specific test

# Run with coverage
pytest tests/test_unit_core_comprehensive.py --cov=src --cov-report=term-missing

# Run comprehensive test suite
./tests/run_comprehensive_tests.sh           # Unit + integration
./tests/run_comprehensive_tests.sh --all     # All including load/chaos
./tests/run_comprehensive_tests.sh --chaos   # Chaos engineering only

# Run regression tests
python tests/test_regression_comprehensive.py
bash tests/run_regression_tests.sh

# Start web API
python web/api.py             # Basic API
python web/api_secure.py      # Secure API with auth
python web/api_batch.py       # Batch processing API

# Start Celery worker (for batch processing)
celery -A src.batch.celery_config worker --loglevel=info

# Linting/formatting
black src/ tests/ --line-length 88
mypy src/ --ignore-missing-imports
```

## Searching & Navigation

**IMPORTANT: Use fzf and ripgrep for efficient codebase navigation**

```bash
# Search for files by name with fzf (interactive fuzzy finder)
fzf                           # Search all files interactively
find src -name "*.py" | fzf   # Search Python files in src/

# Search file contents with ripgrep (fast code search)
rg "MainModel"                # Find all occurrences of MainModel
rg "class.*Model" src/        # Find class definitions in src/
rg -t py "def execute"        # Search only Python files for function definitions
rg -i "validation" --stats    # Case-insensitive search with statistics
rg "TODO|FIXME"               # Search for multiple patterns

# Combine ripgrep with fzf for powerful searching
rg --files | fzf              # Find files with fuzzy search
rg --files -g "*.py" | fzf    # Find Python files only
rg -l "WorkflowOrchestrator" | fzf  # Find files containing pattern, then fuzzy select

# Common search patterns
rg "class \w+\(.*Plugin\)" src/plugins/  # Find all plugin classes
rg "def test_" tests/                    # Find all test functions
rg "@pytest.fixture" tests/              # Find pytest fixtures
rg "raise.*Error" src/                   # Find error handling
```

**When to use what:**
- **fzf**: Finding files by name when you know part of the filename
- **ripgrep (rg)**: Searching code content, function/class definitions, imports
- **Glob tool**: When you need exact glob patterns for automated workflows
- **Grep tool**: When ripgrep is not available or you need specific grep features

## Architecture

### Core Components (src/)

- **SelfOptimizingSystem** (`src/__init__.py`): Main entry point that orchestrates all components
- **MainModel** (`src/core/main_model.py`): Actor that executes user queries using current instructions
- **CriticModel** (`src/core/critic_model.py`): Analyzes failures and proposes instruction updates
- **InstructionManager** (`src/core/instruction_manager.py`): Manages instruction files and version control
- **WorkflowOrchestrator** (`src/core/workflow_orchestrator.py`): Planner-Executor-Critic pattern for multi-step workflows with conditionals, loops, and sub-workflows
- **ValidationPipeline** (`src/core/validator.py`): Validates model outputs (JSON, Length, Regex, Custom validators)
- **CorrectionDetector** (`src/core/correction_detector.py`): Detects implicit user corrections
- **ContextAnalyzer** (`src/core/context_analyzer.py`): Extracts rules from conversation patterns

### Plugin System (src/plugins/)

Extensible plugin architecture with three plugin types:
- **ValidatorPlugin**: Custom validation logic
- **OptimizerPlugin**: Custom failure analysis
- **WorkflowStepPlugin**: Custom workflow step executors

Plugins are discovered via entry points, directory scanning, or config files.

### Storage Layer (src/storage/)

- **DistributedStateManager**: Redis-based cross-instance coordination with distributed locks
- **VersionControl**: Git-style instruction versioning with rollback
- **TenantManager**: Multi-tenant isolation with usage tracking

### Security (src/security/)

- **auth.py**: JWT authentication with role-based access control
- **rate_limit.py**: Multiple strategies (fixed window, sliding window, token bucket)
- **validation.py**: Input sanitization (XSS, SQL injection, command injection prevention)
- **gdpr.py**: UK GDPR compliance with user rights API
- **audit.py**: Comprehensive audit logging

### Caching (src/cache/)

- **LLMCache**: Response caching with TTL/LRU/LFU strategies
- **EmbeddingsCache**: Semantic search optimization
- Supports Redis backend for distributed caching

### Batch Processing (src/batch/)

- Celery-based async job queue with progress monitoring
- Supports parallel workflow execution and failure optimization

## LLM Provider Configuration

Supports Anthropic, OpenAI, Google Gemini, DeepSeek, and OpenRouter. Configure via environment variables:

```bash
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...
OPENROUTER_API_KEY=...
```

Provider is auto-detected from model name or explicitly set via `main_model_provider`/`critic_model_provider` in SystemConfig.

## Testing Structure

- `tests/test_unit_core_comprehensive.py`: Unit tests for core components (36 tests)
- `tests/test_llm_providers_comprehensive.py`: Integration tests for all LLM providers (80+ tests)
- `tests/test_load_stress_comprehensive.py`: Performance and scalability tests (60+ tests)
- `tests/test_chaos_engineering.py`: Fault simulation and recovery tests (80+ tests)
- `tests/test_regression_comprehensive.py`: Regression suite with A/B testing and golden datasets

Coverage targets: >90% for core, >95% for validators, 100% for LLM providers.

## Key Patterns

- **Critic-Actor Optimization**: Failures trigger CriticModel analysis which proposes instruction updates
- **Planner-Executor-Critic Workflow**: Dynamic planning, specialized execution, targeted optimization
- **Circuit Breaker**: Prevents optimization loops via configurable thresholds
- **Tenant Isolation**: Complete separation at database, file, and log levels for multi-tenant deployments
