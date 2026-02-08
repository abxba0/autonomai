"""
LLM Provider implementations for the MainModel.

Each provider handles initialization and configuration of a specific
LLM backend (Anthropic, OpenAI, Google, DeepSeek, OpenRouter).
"""

from .base import detect_provider, initialize_provider

__all__ = [
    "detect_provider",
    "initialize_provider",
]
