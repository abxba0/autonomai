#!/usr/bin/env python3
"""
Multi-Provider AI Inference Examples
Demonstrates how to use different AI providers with the Self-Optimizing System
"""

import sys
import os

# Add parent directory to path to import src package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, SystemConfig


def example_anthropic_claude():
    """Example using Anthropic Claude"""
    print("\n=== Anthropic Claude Example ===")
    
    config = SystemConfig(
        main_model="claude-3-5-sonnet-20241022",
        critic_model="claude-3-haiku-20240307",
        main_model_provider="anthropic",
        critic_model_provider="anthropic",
        temperature_main=0.7,
        temperature_critic=0.3,
    )
    
    system = SelfOptimizingSystem(config)
    
    # Execute a query
    result = system.execute("Explain the concept of self-optimization in AI systems.")
    print(f"Output: {result['output'][:200]}...")
    print(f"Validation passed: {result['validation_passed']}")


def example_openai_gpt():
    """Example using OpenAI GPT"""
    print("\n=== OpenAI GPT Example ===")
    
    config = SystemConfig(
        main_model="gpt-4-turbo-preview",
        critic_model="gpt-3.5-turbo",
        main_model_provider="openai",
        critic_model_provider="openai",
        temperature_main=0.7,
        temperature_critic=0.3,
    )
    
    system = SelfOptimizingSystem(config)
    
    # Execute a query
    result = system.execute("What are the benefits of automated instruction optimization?")
    print(f"Output: {result['output'][:200]}...")
    print(f"Validation passed: {result['validation_passed']}")


def example_google_gemini():
    """Example using Google Gemini"""
    print("\n=== Google Gemini Example ===")
    
    config = SystemConfig(
        main_model="gemini-pro",
        critic_model="gemini-pro",
        main_model_provider="google",
        critic_model_provider="google",
        temperature_main=0.7,
        temperature_critic=0.3,
    )
    
    system = SelfOptimizingSystem(config)
    
    # Execute a query
    result = system.execute("Describe how machine learning models can learn from failures.")
    print(f"Output: {result['output'][:200]}...")
    print(f"Validation passed: {result['validation_passed']}")


def example_deepseek():
    """Example using Deepseek"""
    print("\n=== Deepseek Example ===")
    
    config = SystemConfig(
        main_model="deepseek-chat",
        critic_model="deepseek-chat",
        main_model_provider="deepseek",
        critic_model_provider="deepseek",
        temperature_main=0.7,
        temperature_critic=0.3,
    )
    
    system = SelfOptimizingSystem(config)
    
    # Execute a query
    result = system.execute("What are key principles of building reliable AI systems?")
    print(f"Output: {result['output'][:200]}...")
    print(f"Validation passed: {result['validation_passed']}")


def example_openrouter():
    """Example using Openrouter"""
    print("\n=== Openrouter Example ===")
    
    # Openrouter allows using any model from various providers
    config = SystemConfig(
        main_model="anthropic/claude-3-opus",
        critic_model="openai/gpt-4-turbo",
        main_model_provider="openrouter",
        critic_model_provider="openrouter",
        temperature_main=0.7,
        temperature_critic=0.3,
    )
    
    system = SelfOptimizingSystem(config)
    
    # Execute a query
    result = system.execute("Compare different approaches to AI model optimization.")
    print(f"Output: {result['output'][:200]}...")
    print(f"Validation passed: {result['validation_passed']}")


def example_mixed_providers():
    """Example using different providers for main and critic models"""
    print("\n=== Mixed Providers Example ===")
    
    config = SystemConfig(
        main_model="claude-3-5-sonnet-20241022",
        critic_model="gpt-4-turbo-preview",
        main_model_provider="anthropic",
        critic_model_provider="openai",
        temperature_main=0.7,
        temperature_critic=0.3,
    )
    
    system = SelfOptimizingSystem(config)
    
    # Execute a query
    result = system.execute("Explain the advantages of using multiple AI providers.")
    print(f"Output: {result['output'][:200]}...")
    print(f"Validation passed: {result['validation_passed']}")


def main():
    """Main function to run examples"""
    print("=== Multi-Provider AI Inference Examples ===\n")
    print("These examples demonstrate how to use different AI providers.")
    print("Make sure to set the appropriate API keys in your .env file.\n")
    
    # Check which API keys are available
    providers_available = []
    if os.getenv("ANTHROPIC_API_KEY"):
        providers_available.append("Anthropic")
    if os.getenv("OPENAI_API_KEY"):
        providers_available.append("OpenAI")
    if os.getenv("GOOGLE_API_KEY"):
        providers_available.append("Google")
    if os.getenv("DEEPSEEK_API_KEY"):
        providers_available.append("Deepseek")
    if os.getenv("OPENROUTER_API_KEY"):
        providers_available.append("Openrouter")
    
    if providers_available:
        print(f"Available providers: {', '.join(providers_available)}\n")
    else:
        print("Warning: No API keys found. Examples will use mock models.\n")
    
    # Run examples
    examples = [
        ("Anthropic Claude", example_anthropic_claude, "ANTHROPIC_API_KEY"),
        ("OpenAI GPT", example_openai_gpt, "OPENAI_API_KEY"),
        ("Google Gemini", example_google_gemini, "GOOGLE_API_KEY"),
        ("Deepseek", example_deepseek, "DEEPSEEK_API_KEY"),
        ("Openrouter", example_openrouter, "OPENROUTER_API_KEY"),
        ("Mixed Providers", example_mixed_providers, None),
    ]
    
    for name, func, key_name in examples:
        if key_name and not os.getenv(key_name):
            print(f"\n=== {name} Example ===")
            print(f"Skipped: {key_name} not set")
            continue
        
        try:
            func()
        except Exception as e:
            print(f"Error running {name} example: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Examples Complete ===")


if __name__ == "__main__":
    main()
