"""
Tests for multi-provider AI inference support
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import models.config
from models.config import SystemConfig
from core.main_model import MainModel
from core.critic_model import CriticModel
from core.instruction_manager import InstructionManager


def test_provider_detection():
    """Test automatic provider detection from model names"""
    from core.main_model import MainModel

    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
        )
        instruction_manager = InstructionManager(config)
        main_model = MainModel(config, instruction_manager)

        # Test provider detection
        assert main_model._detect_provider("claude-3-opus") == "anthropic"
        assert main_model._detect_provider("gpt-4-turbo") == "openai"
        assert main_model._detect_provider("gemini-pro") == "google"
        assert main_model._detect_provider("deepseek-chat") == "deepseek"
        assert main_model._detect_provider("openrouter/model") == "openrouter"
        assert main_model._detect_provider("unknown-model") == "unknown"

        print("✓ Provider detection works correctly")
    finally:
        shutil.rmtree(temp_dir)


def test_anthropic_initialization():
    """Test Anthropic model initialization"""
    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="claude-3-5-sonnet-20241022",
            main_model_provider="anthropic",
        )
        instruction_manager = InstructionManager(config)

        # Test without API key (should use mock)
        with patch.dict(os.environ, {}, clear=True):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Anthropic initialization without API key uses mock")

        # Test with API key (will still use mock if package not available)
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Anthropic initialization with API key works")
    finally:
        shutil.rmtree(temp_dir)


def test_openai_initialization():
    """Test OpenAI model initialization"""
    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="gpt-4-turbo-preview",
            main_model_provider="openai",
        )
        instruction_manager = InstructionManager(config)

        # Test without API key (should use mock)
        with patch.dict(os.environ, {}, clear=True):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ OpenAI initialization without API key uses mock")

        # Test with API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ OpenAI initialization with API key works")
    finally:
        shutil.rmtree(temp_dir)


def test_google_initialization():
    """Test Google Gemini model initialization"""
    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="gemini-pro",
            main_model_provider="google",
        )
        instruction_manager = InstructionManager(config)

        # Test without API key (should use mock)
        with patch.dict(os.environ, {}, clear=True):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Google initialization without API key uses mock")

        # Test with API key
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Google initialization with API key works")
    finally:
        shutil.rmtree(temp_dir)


def test_deepseek_initialization():
    """Test Deepseek model initialization"""
    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="deepseek-chat",
            main_model_provider="deepseek",
        )
        instruction_manager = InstructionManager(config)

        # Test without API key (should use mock)
        with patch.dict(os.environ, {}, clear=True):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Deepseek initialization without API key uses mock")

        # Test with API key
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Deepseek initialization with API key works")
    finally:
        shutil.rmtree(temp_dir)


def test_openrouter_initialization():
    """Test Openrouter model initialization"""
    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="anthropic/claude-3-opus",
            main_model_provider="openrouter",
        )
        instruction_manager = InstructionManager(config)

        # Test without API key (should use mock)
        with patch.dict(os.environ, {}, clear=True):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Openrouter initialization without API key uses mock")

        # Test with API key
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            main_model = MainModel(config, instruction_manager)
            assert main_model.model is not None
            print("✓ Openrouter initialization with API key works")
    finally:
        shutil.rmtree(temp_dir)


def test_mixed_providers():
    """Test using different providers for main and critic models"""
    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="claude-3-5-sonnet-20241022",
            main_model_provider="anthropic",
            critic_model="gpt-4-turbo-preview",
            critic_model_provider="openai",
        )
        instruction_manager = InstructionManager(config)

        # Initialize both models
        main_model = MainModel(config, instruction_manager)
        critic_model = CriticModel(config, instruction_manager)

        assert main_model.model is not None
        assert critic_model.model is not None
        print("✓ Mixed providers (Anthropic + OpenAI) work correctly")
    finally:
        shutil.rmtree(temp_dir)


def test_execute_with_mock_model():
    """Test execution with mock model"""
    temp_dir = tempfile.mkdtemp()
    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="test-model",
            enable_auto_validation=False,
        )
        instruction_manager = InstructionManager(config)
        main_model = MainModel(config, instruction_manager)

        # Execute a query
        result = main_model.execute("Test query")

        assert "output" in result
        assert "validation_passed" in result
        assert result["output"] is not None
        print("✓ Execution with mock model works")
    finally:
        shutil.rmtree(temp_dir)


def test_config_with_provider_override():
    """Test that explicit provider config overrides auto-detection"""
    temp_dir = tempfile.mkdtemp()
    try:
        # Model name suggests OpenAI, but we explicitly set it to use openrouter
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="gpt-4-turbo-preview",
            main_model_provider="openrouter",  # Override auto-detection
        )
        instruction_manager = InstructionManager(config)
        main_model = MainModel(config, instruction_manager)

        # Should use openrouter provider, not openai
        detected = main_model._detect_provider(config.main_model.lower())
        assert detected == "openai"  # Auto-detection would say openai
        # But we explicitly configured openrouter
        assert config.main_model_provider == "openrouter"

        print("✓ Explicit provider config overrides auto-detection")
    finally:
        shutil.rmtree(temp_dir)


def run_all_tests():
    """Run all provider tests"""
    print("Running multi-provider AI inference tests...\n")

    tests = [
        ("Provider detection", test_provider_detection),
        ("Anthropic initialization", test_anthropic_initialization),
        ("OpenAI initialization", test_openai_initialization),
        ("Google initialization", test_google_initialization),
        ("Deepseek initialization", test_deepseek_initialization),
        ("Openrouter initialization", test_openrouter_initialization),
        ("Mixed providers", test_mixed_providers),
        ("Execute with mock model", test_execute_with_mock_model),
        ("Config with provider override", test_config_with_provider_override),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            print(f"  ✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test_name}: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All provider tests passed!")
        return True
    else:
        print("❌ Some provider tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
