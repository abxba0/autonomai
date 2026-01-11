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
3. **Try `terminal_chatbot/`** - See a complete application

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
