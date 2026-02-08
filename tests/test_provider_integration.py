#!/usr/bin/env python3
"""
Simple integration test for multi-provider AI inference
Tests that the new provider detection and initialization works correctly
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_provider_imports():
    """Test that all provider-related classes can be imported"""
    print("Testing provider imports...")

    try:
        from models.config import SystemConfig
        from core.main_model import MainModel
        from core.critic_model import CriticModel
        from tests.mocks.models import MockModel, MockCriticModel

        print("✓ All classes imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_provider_detection():
    """Test that provider detection works correctly"""
    print("\nTesting provider detection...")

    from models.config import SystemConfig
    from core.main_model import MainModel
    from core.instruction_manager import InstructionManager
    from pathlib import Path
    import tempfile

    temp_dir = tempfile.mkdtemp()
    config = SystemConfig(instructions_dir=Path(temp_dir) / "instructions")
    instruction_manager = InstructionManager(config)
    main_model = MainModel(config, instruction_manager)

    test_cases = [
        ("claude-3-opus", "anthropic"),
        ("claude-3-5-sonnet-20241022", "anthropic"),
        ("gpt-4-turbo", "openai"),
        ("gpt-3.5-turbo", "openai"),
        ("gemini-pro", "google"),
        ("deepseek-chat", "deepseek"),
        ("openrouter/model", "openrouter"),
        ("unknown-model", "unknown"),
    ]

    all_passed = True
    for model_name, expected_provider in test_cases:
        detected = main_model._detect_provider(model_name)
        if detected == expected_provider:
            print(f"✓ {model_name} -> {detected}")
        else:
            print(f"✗ {model_name} -> {detected} (expected {expected_provider})")
            all_passed = False

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)

    return all_passed


def test_config_with_providers():
    """Test that SystemConfig accepts provider configuration"""
    print("\nTesting SystemConfig with provider options...")

    from models.config import SystemConfig

    # Test with explicit provider configuration
    config = SystemConfig(
        main_model="claude-3-5-sonnet-20241022",
        critic_model="gpt-4-turbo",
        main_model_provider="anthropic",
        critic_model_provider="openai",
    )

    assert config.main_model_provider == "anthropic"
    assert config.critic_model_provider == "openai"
    print("✓ SystemConfig accepts provider configuration")

    # Test with None (auto-detection)
    config2 = SystemConfig(
        main_model="gemini-pro",
    )
    assert config2.main_model_provider is None
    print("✓ SystemConfig works with auto-detection (None)")

    return True


def test_mock_fallback():
    """Test that system falls back to mock models when API keys are missing"""
    print("\nTesting mock model fallback...")

    from models.config import SystemConfig
    from core.main_model import MainModel, MockModel
    from core.instruction_manager import InstructionManager
    from pathlib import Path
    import tempfile

    temp_dir = tempfile.mkdtemp()

    # Clear environment to ensure no API keys
    old_env = {}
    for key in [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENROUTER_API_KEY",
    ]:
        if key in os.environ:
            old_env[key] = os.environ[key]
            del os.environ[key]

    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="claude-3-5-sonnet-20241022",
        )
        instruction_manager = InstructionManager(config)
        main_model = MainModel(config, instruction_manager)

        # Should have initialized a mock model
        assert main_model.model is not None
        assert isinstance(main_model.model, MockModel)
        print("✓ Falls back to MockModel when API key is missing")

        return True
    finally:
        # Restore environment
        for key, value in old_env.items():
            os.environ[key] = value

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)


def test_mock_execution():
    """Test that mock models can execute queries"""
    print("\nTesting mock model execution...")

    from models.config import SystemConfig
    from core.main_model import MainModel
    from core.instruction_manager import InstructionManager
    from pathlib import Path
    import tempfile

    temp_dir = tempfile.mkdtemp()

    try:
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="test-model",
            enable_auto_validation=False,
        )
        instruction_manager = InstructionManager(config)
        main_model = MainModel(config, instruction_manager)

        # Execute a test query
        result = main_model.execute("Test query")

        assert "output" in result
        assert "validation_passed" in result
        assert result["output"] is not None
        assert len(result["output"]) > 0
        print(f"✓ Mock model executed successfully")
        print(f"  Output: {result['output'][:100]}...")

        return True
    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)


def main():
    """Run all integration tests"""
    print("=== Multi-Provider AI Inference Integration Tests ===\n")

    tests = [
        ("Provider Imports", test_provider_imports),
        ("Provider Detection", test_provider_detection),
        ("Config with Providers", test_config_with_providers),
        ("Mock Fallback", test_mock_fallback),
        ("Mock Execution", test_mock_execution),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ Test error: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n=== Test Summary ===")
    all_passed = True
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False

    if all_passed:
        print("\n✅ All integration tests passed!")
        print("\nThe multi-provider AI inference system is working correctly.")
        print("\nSupported providers:")
        print("  - Anthropic (Claude)")
        print("  - OpenAI (GPT)")
        print("  - Google (Gemini)")
        print("  - Deepseek")
        print("  - Openrouter")
        print("\nTo use real models, set the appropriate API keys in your .env file.")
    else:
        print("\n❌ Some integration tests failed")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
