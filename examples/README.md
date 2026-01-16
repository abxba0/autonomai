# Examples

This directory contains practical examples demonstrating the features of the autonomai library.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)
Demonstrates fundamental features of the self-optimizing system:
- System initialization
- Adding validators
- Executing queries
- Automatic optimization
- Manual feedback
- Version control

**Run it:**
```bash
python examples/basic_usage.py
```

### 2. Multi-Provider Usage (`multi_provider_usage.py`)
Shows how to use different AI providers with autonomai:
- Anthropic Claude
- OpenAI GPT
- Google Gemini
- DeepSeek
- Openrouter
- Mixed provider configurations

**Run it:**
```bash
python examples/multi_provider_usage.py
```

### 3. Terminal Chatbot (`terminal_chatbot/`)
A full-featured terminal-based chatbot using DeepSeek API:
- Interactive conversation interface
- Command system (/help, /status, /history, etc.)
- Real-time validation and optimization
- Conversation context management
- Manual feedback submission

**Run it:**
```bash
python examples/terminal_chatbot/chatbot.py
# or
cd examples/terminal_chatbot
python chatbot.py
```

**Features:**
- 🤖 Interactive Q&A with DeepSeek API
- ✅ Automatic output validation
- 🔄 Self-optimizing instructions
- 📦 Version control tracking
- 💬 Conversation history
- 💭 Manual feedback system

See [terminal_chatbot/README.md](terminal_chatbot/README.md) for detailed documentation.

### 4. Hallucination-Proof Data Extractor (`hallucination_proof_extractor.py`)
Demonstrates preventing LLM hallucinations in data extraction tasks:
- Extract structured data from messy, unstructured documents
- Custom validator that checks extracted values against source text
- Automatic learning when hallucinations are detected
- Shows the fail → analyze → optimize cycle

**Run it:**
```bash
python examples/hallucination_proof_extractor.py
```

**Features:**
- 📄 Data extraction from messy documents
- 🔍 Grounding validation (verifies all extracted values exist in source)
- 🚫 Hallucination detection and prevention
- 🔄 Self-optimization for literal fidelity
- 💡 Real-world application patterns (invoices, receipts, medical records)

**Why this is valuable:**
- Tackles a common LLM weakness: inventing incorrect details
- Enforces "grounding" of outputs for reliability
- Demonstrates learning cycle for improving accuracy
- Practical for invoice processing, document analysis, and data extraction tasks

### 5. Adversarial Prompt Hardener (`adversarial_prompt_hardener.py`)
Demonstrates a "Red Team" security scenario where the system defends against jailbreak attempts:
- Detect prompt injection and instruction leakage attempts
- Validate that system prompts remain hidden
- Automatic hardening when security vulnerabilities are found
- Iterative defense: each cycle blocks broader attack classes

**Run it:**
```bash
python examples/adversarial_prompt_hardener.py
```

**Features:**
- 🛡️ Jailbreak attempt detection
- 🔒 System prompt protection
- 🔄 Self-hardening security defenses
- 🎯 Red team attack simulation
- 📊 Security assessment reporting

**Why this is valuable:**
- Demonstrates security-readiness for enterprise deployment
- Protects proprietary prompts and business logic
- Continually strengthens defenses against adversarial users
- Useful for prompt engineers, security teams, and AI safety researchers
- Essential for customer-facing AI systems with sensitive instructions

See [ADVERSARIAL_PROMPT_README.md](ADVERSARIAL_PROMPT_README.md) for detailed documentation.

### 6. Self-Healing Code Assistant (`self_healing_code_assistant.py`)
Demonstrates an AI-powered code assistant that generates Python scripts and automatically improves code quality:
- Generate Python code from natural language requests
- Validate syntax using Python's AST parser
- Check for style issues (indentation, docstrings, line length, etc.)
- Automatic learning when code fails validation
- Iterative improvement cycle for better code generation

**Run it:**
```bash
python examples/self_healing_code_assistant.py
```

**Features:**
- 🧑‍💻 Python code generation from descriptions
- ✅ Syntax validation using AST parser
- 🎨 Style checking (tabs, docstrings, line length, except clauses)
- 🔄 Self-optimization for code quality improvement
- 📈 Learning from mistakes to write better code

**Why this is valuable:**
- Real-world need: users want code that actually runs
- Automated validation catches errors before execution
- Enforces coding best practices and style guidelines
- Demonstrates LLMOps patterns for code generation
- Practical for AI-powered development tools, code completion, and rapid prototyping

See [SELF_HEALING_CODE_README.md](SELF_HEALING_CODE_README.md) for detailed documentation.

## Getting Started

### Prerequisites

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root with your API keys:

```env
# Choose one or more providers
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

**Note:** Examples will use mock models if API keys are not configured.

## Running Examples

All examples can be run from the project root:

```bash
# Run from project root
python examples/basic_usage.py
python examples/multi_provider_usage.py
python examples/terminal_chatbot/chatbot.py

# Or navigate to specific directory
cd examples/terminal_chatbot
python chatbot.py
```

## Learning Path

If you're new to autonomai, we recommend following this order:

1. **Start with `basic_usage.py`** - Learn the fundamentals
2. **Explore `multi_provider_usage.py`** - Understand provider options
3. **Try `self_healing_code_assistant.py`** - See practical code generation with validation
4. **Try `hallucination_proof_extractor.py`** - See advanced validation patterns
5. **Check out `adversarial_prompt_hardener.py`** - Learn security best practices
6. **Experiment with `terminal_chatbot/`** - See a complete application

## Creating Your Own Examples

Want to create your own example? Here's a template:

```python
#!/usr/bin/env python3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Configure your system
    config = SystemConfig(
        main_model="your-model-here",
        main_model_provider="your-provider",
        enable_auto_optimization=True,
    )
    
    # Create system
    system = SelfOptimizingSystem(config)
    
    # Your code here
    result = system.execute("Your query")
    print(result["output"])

if __name__ == "__main__":
    main()
```

## Documentation

For more information:

- [Main README](../README.md) - Project overview
- [Usage Guide](../docs/usage-guide.md) - Comprehensive usage instructions
- [API Reference](../docs/api-reference.md) - API documentation
- [Provider Configuration](../docs/provider-configuration.md) - Provider setup guide

## Contributing

Have an interesting example to share? We'd love to see it!

1. Fork the repository
2. Create your example in the `examples/` directory
3. Add documentation (README.md)
4. Test thoroughly
5. Submit a pull request

## Support

For questions or issues:
- Open an issue on [GitHub](https://github.com/abxba0/autonomai/issues)
- Check the [documentation](../docs/)
- Review existing examples

## License

All examples are part of the autonomai project and licensed under the MIT License.

## 7. Caching Layer Demo (`caching_demo.py`) ⭐ NEW

**Production-grade caching demonstration**

Demonstrates the new caching layer for performance optimization:
- LLM response caching (1000x+ speedup)
- Embeddings caching
- Cache warming strategies
- Performance benchmarks
- Different cache strategies (TTL, LRU, LFU, manual)

**Run it:**
```bash
python examples/caching_demo.py
```

**Features:**
- 🚀 Instant responses for repeated queries
- 💰 Reduced API costs
- 📊 Performance metrics and monitoring
- 🔄 Multiple invalidation strategies
- 🌐 Redis support (with automatic fallback to memory)

**Why this is valuable:**
- Production-ready performance optimization
- Reduces latency by 99%+ for cached queries
- Lowers operational costs significantly
- Essential for high-traffic applications
- No Redis required for development/testing

See [docs/caching-guide.md](../docs/caching-guide.md) for detailed documentation.

