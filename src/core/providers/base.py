"""
Base provider utilities for detecting and initializing LLM providers.
"""

import os
from typing import Optional

from ...models.config import SystemConfig
from ...models.exceptions import ConfigurationError


def detect_provider(model_name: str) -> str:
    """Auto-detect provider from model name"""
    if "claude" in model_name or "anthropic" in model_name:
        return "anthropic"
    elif "gpt" in model_name or "openai" in model_name:
        return "openai"
    elif "gemini" in model_name or "google" in model_name:
        return "google"
    elif "deepseek" in model_name:
        return "deepseek"
    elif "openrouter" in model_name:
        return "openrouter"
    return "unknown"


def initialize_provider(config: SystemConfig):
    """Initialize the language model based on provider detection.

    Args:
        config: System configuration with model and provider settings.

    Returns:
        Initialized LangChain chat model instance.

    Raises:
        ConfigurationError: If no valid provider/API key is configured.
    """
    model_name = config.main_model.lower()
    provider = (
        config.main_model_provider.lower()
        if config.main_model_provider
        else None
    )

    # Detect provider from model name if not explicitly set
    if not provider:
        provider = detect_provider(model_name)

    # Initialize based on provider
    if provider == "anthropic":
        return _init_anthropic(config)
    elif provider == "openai":
        return _init_openai(config)
    elif provider == "google":
        return _init_google(config)
    elif provider == "deepseek":
        return _init_deepseek(config)
    elif provider == "openrouter":
        return _init_openrouter(config)
    else:
        raise ConfigurationError(
            f"No API key configured for model '{config.main_model}'. "
            "Set ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, "
            "DEEPSEEK_API_KEY, or OPENROUTER_API_KEY. "
            "For testing without API keys, use the mock fixtures from tests/mocks/"
        )


def _init_anthropic(config: SystemConfig):
    """Initialize Anthropic Claude model"""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ConfigurationError(
            "langchain-anthropic not installed. Install with: pip install langchain-anthropic"
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "ANTHROPIC_API_KEY not found. Set it in your environment or .env file. "
            "For testing without API keys, use the mock fixtures from tests/mocks/"
        )

    return ChatAnthropic(
        model=config.main_model,
        temperature=config.temperature_main,
        api_key=api_key,
    )


def _init_openai(config: SystemConfig):
    """Initialize OpenAI GPT model"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ConfigurationError(
            "langchain-openai not installed. Install with: pip install langchain-openai"
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY not found. Set it in your environment or .env file. "
            "For testing without API keys, use the mock fixtures from tests/mocks/"
        )

    return ChatOpenAI(
        model=config.main_model,
        temperature=config.temperature_main,
        api_key=api_key,
    )


def _init_google(config: SystemConfig):
    """Initialize Google Gemini model"""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ConfigurationError(
            "langchain-google-genai not installed. Install with: pip install langchain-google-genai"
        )

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "GOOGLE_API_KEY not found. Set it in your environment or .env file. "
            "For testing without API keys, use the mock fixtures from tests/mocks/"
        )

    return ChatGoogleGenerativeAI(
        model=config.main_model,
        temperature=config.temperature_main,
        google_api_key=api_key,
    )


def _init_deepseek(config: SystemConfig):
    """Initialize Deepseek model (via OpenAI-compatible API)"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ConfigurationError(
            "langchain-openai not installed. Install with: pip install langchain-openai"
        )

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    if not api_key:
        raise ConfigurationError(
            "DEEPSEEK_API_KEY not found. Set it in your environment or .env file. "
            "For testing without API keys, use the mock fixtures from tests/mocks/"
        )

    return ChatOpenAI(
        model=config.main_model,
        temperature=config.temperature_main,
        api_key=api_key,
        base_url=base_url,
    )


def _init_openrouter(config: SystemConfig):
    """Initialize Openrouter model (via OpenAI-compatible API)"""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ConfigurationError(
            "langchain-openai not installed. Install with: pip install langchain-openai"
        )

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ConfigurationError(
            "OPENROUTER_API_KEY not found. Set it in your environment or .env file. "
            "For testing without API keys, use the mock fixtures from tests/mocks/"
        )

    return ChatOpenAI(
        model=config.main_model,
        temperature=config.temperature_main,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/abxba0/autonomai",
            "X-Title": "AutonomAI Self-Optimizing System",
        },
    )
