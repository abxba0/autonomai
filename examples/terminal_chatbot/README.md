# Terminal Chatbot Example

A simple terminal-based chatbot demonstrating the features of `@abxba0/autonomai` using the DeepSeek API.

## Overview

This example showcases how to build an interactive terminal chatbot using the self-optimizing instruction library. The chatbot demonstrates key features including:

- 🤖 **Interactive Conversation**: Real-time Q&A with DeepSeek AI
- ✅ **Automatic Validation**: Output validation with configurable validators
- 🔄 **Self-Optimization**: Automatic instruction updates based on failures
- 📦 **Version Control**: Track and manage instruction versions
- 💬 **Conversation Context**: Maintains conversation history for context-aware responses
- 💭 **Manual Feedback**: Submit feedback to improve the system

## Features Demonstrated

### 1. DeepSeek API Integration
The chatbot uses DeepSeek's chat model for both the main model and the critic model, demonstrating multi-provider support in autonomai.

### 2. Interactive Commands
- `/help` - Display available commands and features
- `/status` - Show system configuration and statistics
- `/history` - View conversation history
- `/versions` - Display instruction version history
- `/feedback` - Submit manual feedback for optimization
- `/clear` - Clear conversation history
- `/quit` - Exit the chatbot

### 3. Validation Pipeline
The example includes a `LengthValidator` to ensure responses meet minimum and maximum length requirements. When validation fails, the system automatically learns and optimizes.

### 4. Self-Optimization
When the model's output fails validation, the critic model analyzes the failure and proposes instruction updates to prevent similar issues in the future.

### 5. Conversation Management
The chatbot maintains conversation history and provides context from the last 5 messages to enable coherent, context-aware responses.

## Prerequisites

1. **Python 3.8+** installed
2. **Required packages** (installed via `requirements.txt` in project root)
3. **DeepSeek API Key** (optional - will use mock model if not provided)

## Setup

### 1. Install Dependencies

From the project root directory:

```bash
pip install -r requirements.txt
```

### 2. Configure API Key (Optional)

Create a `.env` file in the project root (or use the existing one):

```bash
# .env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

**Note:** If you don't have a DeepSeek API key, the chatbot will use a mock model for demonstration purposes.

### 3. Get DeepSeek API Key

If you don't have a DeepSeek API key:
1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

## Running the Chatbot

### From the terminal_chatbot directory:

```bash
cd examples/terminal_chatbot
python chatbot.py
```

### From the project root:

```bash
python examples/terminal_chatbot/chatbot.py
```

### Make it executable (Unix/Linux/Mac):

```bash
chmod +x examples/terminal_chatbot/chatbot.py
./examples/terminal_chatbot/chatbot.py
```

## Usage Examples

### Basic Conversation

```
You: What is machine learning?
🤔 Thinking...

🤖 Bot: Machine learning is a subset of artificial intelligence...
```

### Check System Status

```
You: /status

📊 System Status:
  Status: operational
  Main Model: deepseek-chat (DeepSeek)
  Critic Model: deepseek-chat (DeepSeek)
  Auto-Optimization: True
  Total Versions: 1
  Latest Version: v20250111_123000
  Active Validators: 1
  Conversation Length: 4 messages
```

### View Conversation History

```
You: /history

📝 Conversation History (4 messages):

  1. You: What is machine learning?
  2. Bot: Machine learning is a subset of artificial intelligence...
  3. You: Can you give me an example?
  4. Bot: Sure! A common example is email spam detection...
```

### Submit Feedback

```
You: /feedback

💭 Manual Feedback Submission
Enter your feedback (press Enter twice to finish):
Please provide more concise answers


Processing feedback...
✅ Feedback processed and instructions updated!
   New version: v20250111_123045
```

### View Version History

```
You: /versions

📦 Instruction Version History (2 versions):

  • v20250111_123000
    Trigger: initialization
    Summary: Initial instruction set
    
  • v20250111_123045
    Trigger: human_feedback
    Summary: Updated to provide more concise answers
```

## Code Structure

```
terminal_chatbot/
├── chatbot.py          # Main chatbot application
└── README.md           # This file
```

### Key Components

**`TerminalChatbot` class:**
- `__init__()` - Initializes the system with DeepSeek configuration
- `show_banner()` - Displays welcome banner
- `show_help()` - Shows available commands
- `show_status()` - Displays system status
- `show_history()` - Shows conversation history
- `show_versions()` - Displays version history
- `submit_feedback()` - Processes manual feedback
- `clear_history()` - Clears conversation history
- `process_command()` - Handles special commands
- `chat()` - Processes chat messages
- `run()` - Main chatbot loop

## Customization

### Change AI Model

Edit the configuration in `chatbot.py`:

```python
self.config = SystemConfig(
    main_model="deepseek-chat",           # Change model name
    critic_model="deepseek-chat",         # Change critic model
    main_model_provider="deepseek",       # Change provider
    critic_model_provider="deepseek",
    temperature_main=0.7,                 # Adjust creativity
    temperature_critic=0.3,               # Adjust critic temperature
    enable_auto_optimization=True,
)
```

### Add More Validators

```python
# Add JSON validator
from src import JSONValidator
self.system.add_validator(JSONValidator(required_fields=["key1", "key2"]))

# Add regex validator
from src import RegexValidator
self.system.add_validator(RegexValidator(pattern=r'\[.*\]'))

# Add custom validator
from src import CustomValidator

def my_validator(output: str, context) -> bool:
    return "important_word" in output.lower()

self.system.add_validator(CustomValidator("MyValidator", my_validator))
```

### Modify Context Window

Change the number of messages included in context:

```python
result = self.system.execute(
    user_input,
    conversation_context=self.conversation_history[-10:]  # Last 10 messages
)
```

## Troubleshooting

### Issue: "DEEPSEEK_API_KEY not found"

**Solution:** Either add your API key to `.env` file or continue with the mock model for testing.

### Issue: "Module not found" errors

**Solution:** Make sure you're running from the correct directory and have installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Slow responses

**Solution:** This is normal when using real API calls. The DeepSeek API needs time to generate responses. You can:
- Reduce the `temperature_main` value for faster, more deterministic responses
- Use a faster model if available
- Check your internet connection

### Issue: Validation failures

**Solution:** This is expected behavior! The system is designed to learn from validation failures. Check:
- The validation rules in the code
- Use `/versions` to see how the system adapted
- Submit feedback with `/feedback` to guide improvements

## Learning More

### Autonomai Documentation

- [Main README](../../README.md) - Overview of the autonomai system
- [Usage Guide](../../docs/usage-guide.md) - Comprehensive usage instructions
- [API Reference](../../docs/api-reference.md) - Detailed API documentation
- [Provider Configuration](../../docs/provider-configuration.md) - Multi-provider setup

### Related Examples

- [basic_usage.py](../basic_usage.py) - Basic system usage
- [multi_provider_usage.py](../multi_provider_usage.py) - Multi-provider examples

## Contributing

If you'd like to improve this example:

1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/abxba0/autonomai/issues)
- Check the [documentation](../../docs/)
- Review other [examples](../)

## License

This example is part of the autonomai project and is licensed under the MIT License.
