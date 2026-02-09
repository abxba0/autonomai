# AI Provider Configuration Guide

This guide explains how to configure and use different AI providers with the Self-Optimizing Instruction Library.

## Supported Providers

The system now supports the following AI providers:

1. **Anthropic Claude** - Advanced reasoning and analysis
2. **OpenAI GPT** - General-purpose language models
3. **Google Gemini** - Multi-modal AI capabilities
4. **Deepseek** - Efficient and cost-effective models
5. **Openrouter** - Access to multiple providers through one API

## Configuration

### Environment Variables

Set up your API keys in a `.env` file:

```bash
# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI GPT
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# Deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### SystemConfig Setup

Configure your system to use specific providers:

```python
from src.models.config import SystemConfig

config = SystemConfig(
    main_model="claude-3-5-sonnet-20241022",
    critic_model="claude-3-haiku-20240307",
    main_model_provider="anthropic",  # Optional: auto-detected from model name
    critic_model_provider="anthropic",
    temperature_main=0.7,
    temperature_critic=0.3,
)
```

## Provider-Specific Details

### Anthropic Claude

**Models:**
- `claude-3-opus-20240229` - Most capable model
- `claude-3-5-sonnet-20241022` - Best balance of performance and cost
- `claude-3-haiku-20240307` - Fastest and most cost-effective

**Setup:**
```python
config = SystemConfig(
    main_model="claude-3-5-sonnet-20241022",
    critic_model="claude-3-haiku-20240307",
    main_model_provider="anthropic",
)
```

**API Key:** Get from https://console.anthropic.com/

### OpenAI GPT

**Models:**
- `gpt-4-turbo-preview` - Most capable
- `gpt-4` - High quality
- `gpt-3.5-turbo` - Fast and cost-effective

**Setup:**
```python
config = SystemConfig(
    main_model="gpt-4-turbo-preview",
    critic_model="gpt-3.5-turbo",
    main_model_provider="openai",
)
```

**API Key:** Get from https://platform.openai.com/

### Google Gemini

**Models:**
- `gemini-pro` - Optimized for text
- `gemini-pro-vision` - Multi-modal capabilities

**Setup:**
```python
config = SystemConfig(
    main_model="gemini-pro",
    critic_model="gemini-pro",
    main_model_provider="google",
)
```

**API Key:** Get from https://makersuite.google.com/

### Deepseek

**Models:**
- `deepseek-chat` - General chat model
- `deepseek-coder` - Optimized for code

**Setup:**
```python
config = SystemConfig(
    main_model="deepseek-chat",
    critic_model="deepseek-chat",
    main_model_provider="deepseek",
)
```

**API Key:** Get from https://platform.deepseek.com/

**Note:** Deepseek uses an OpenAI-compatible API, so the integration uses `langchain-openai` with a custom base URL.

### Openrouter

**Models:** Supports hundreds of models from various providers
- Format: `provider/model-name`
- Examples:
  - `anthropic/claude-3-opus`
  - `openai/gpt-4-turbo`
  - `google/gemini-pro`
  - `meta-llama/llama-2-70b-chat`

**Setup:**
```python
config = SystemConfig(
    main_model="anthropic/claude-3-opus",
    critic_model="openai/gpt-4-turbo",
    main_model_provider="openrouter",
)
```

**API Key:** Get from https://openrouter.ai/

**Benefits:**
- Single API key for multiple providers
- Automatic failover
- Usage tracking across providers
- Cost optimization

## Usage Examples

### Basic Usage

```python
from src import SelfOptimizingSystem
from src.models.config import SystemConfig

# Create configuration
config = SystemConfig(
    main_model="claude-3-5-sonnet-20241022",
    main_model_provider="anthropic",
)

# Initialize system
system = SelfOptimizingSystem(config)

# Execute query
result = system.execute("Your query here")
print(result['output'])
```

### Mixed Provider Usage

Use different providers for main and critic models:

```python
config = SystemConfig(
    main_model="claude-3-5-sonnet-20241022",
    critic_model="gpt-4-turbo-preview",
    main_model_provider="anthropic",
    critic_model_provider="openai",
)
```

### Auto-Detection

Provider can be auto-detected from model name:

```python
config = SystemConfig(
    main_model="claude-3-5-sonnet-20241022",  # Auto-detects "anthropic"
    critic_model="gpt-4-turbo-preview",       # Auto-detects "openai"
    # No need to specify providers
)
```

## Best Practices

### 1. Provider Selection

- **Anthropic Claude**: Best for reasoning, analysis, and long-context tasks
- **OpenAI GPT**: Great general-purpose models with wide ecosystem support
- **Google Gemini**: Good for multi-modal tasks and cost-effective inference
- **Deepseek**: Excellent for code-related tasks and budget-conscious projects
- **Openrouter**: Best when you need flexibility across multiple providers

### 2. Model Pairing

For optimal performance:
- **Main Model**: Use more capable models (e.g., GPT-4, Claude Opus, Gemini Pro)
- **Critic Model**: Can use faster/cheaper models (e.g., GPT-3.5, Claude Haiku)

### 3. Error Handling

The system automatically falls back to mock models if:
- API keys are missing
- Required packages are not installed
- API calls fail

### 4. Cost Optimization

- Use faster models for the critic (it runs more frequently)
- Consider Deepseek or Gemini for cost-sensitive applications
- Use Openrouter for automatic cost optimization across providers

## Installation

Install required packages:

```bash
# Base requirements
pip install langchain langchain-core

# Provider-specific packages
pip install langchain-anthropic  # For Anthropic
pip install langchain-openai     # For OpenAI, Deepseek, Openrouter
pip install langchain-google-genai  # For Google Gemini

# Or install all at once
pip install -r requirements.txt
```

## Troubleshooting

### ImportError: No module named 'langchain_xxx'

Install the missing provider package:
```bash
pip install langchain-anthropic
pip install langchain-openai
pip install langchain-google-genai
```

### API Key Not Found

Ensure your `.env` file is in the project root and contains the correct key:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### Using Mock Models

If you see "Using mock model" warnings, it means:
1. API key is not set
2. Provider package is not installed
3. Model name doesn't match any known provider

Mock models return placeholder responses and are only for testing.

## Advanced Configuration

### Custom Base URLs

For providers with custom endpoints:

```python
import os
os.environ["DEEPSEEK_BASE_URL"] = "https://custom-endpoint.com/v1"
```

### Temperature Settings

Adjust creativity vs. determinism:

```python
config = SystemConfig(
    temperature_main=0.9,   # More creative
    temperature_critic=0.1,  # More deterministic
)
```

### Provider-Specific Headers

Some providers require custom headers (handled automatically):

```python
# Openrouter automatically includes:
# - HTTP-Referer
# - X-Title
```

## Security Considerations

1. **Never commit API keys** to version control
2. **Use environment variables** or secure secret management
3. **Rotate keys regularly**
4. **Monitor usage** to detect anomalies
5. **Set rate limits** in provider dashboards

## Support and Resources

- **Documentation**: See README.md for general system documentation
- **Examples**: Check `examples/multi_provider_usage.py` for working examples
- **Provider Docs**:
  - [Anthropic Docs](https://docs.anthropic.com/)
  - [OpenAI Docs](https://platform.openai.com/docs/)
  - [Google AI Docs](https://ai.google.dev/)
  - [Deepseek Docs](https://platform.deepseek.com/docs)
  - [Openrouter Docs](https://openrouter.ai/docs)

## Contributing

To add support for a new provider:

1. Add provider detection in `_detect_provider()`
2. Implement `_init_<provider>()` method
3. Add API key to `.env.example`
4. Update this documentation
5. Add examples to `multi_provider_usage.py`
