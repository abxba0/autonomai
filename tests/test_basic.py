"""
Basic tests for the Self-Optimizing Instruction Library
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_imports():
    """Test that basic imports work"""
    from models.config import SystemConfig, FailureEntry
    from models.critic_response import CriticResponse
    from core.validator import ValidationPipeline, JSONValidator

    assert SystemConfig is not None
    assert FailureEntry is not None
    assert CriticResponse is not None
    assert ValidationPipeline is not None
    assert JSONValidator is not None

    print("✓ Basic imports work")


def test_system_config():
    """Test SystemConfig creation"""
    from models.config import SystemConfig

    config = SystemConfig(
        main_model="test-model",
        critic_model="test-critic",
        enable_auto_optimization=True,
    )

    assert config.main_model == "test-model"
    assert config.critic_model == "test-critic"
    assert config.enable_auto_optimization is True

    print("✓ SystemConfig creation works")


def test_failure_entry():
    """Test FailureEntry creation"""
    from models.config import FailureEntry

    failure = FailureEntry(
        trigger_type="auto_validation",
        failure_description="Test failure description",
        user_query="Test query",
        last_model_output="Test output",
    )

    assert failure.trigger_type == "auto_validation"
    assert failure.failure_description == "Test failure description"
    assert failure.user_query == "Test query"
    assert failure.last_model_output == "Test output"
    assert failure.failure_signature is not None

    print("✓ FailureEntry creation works")


def test_critic_response():
    """Test CriticResponse creation and validation"""
    from models.critic_response import CriticResponse

    # Valid response
    response = CriticResponse(
        impact_analysis="This is a detailed impact analysis that explains why this change is needed.",
        conflict_analysis="No conflicts with existing rules.",
        safety_declaration=True,
        safety_reasoning="This change is safe because it only adds validation.",
        change_type="append",
        proposed_appendix_update="**New Rule**: Test rule for validation.",
    )

    assert response.impact_analysis is not None
    assert response.safety_declaration is True
    assert response.change_type == "append"

    # Test validation
    is_valid, error = response.is_valid()
    assert is_valid is True
    assert error is None

    print("✓ CriticResponse creation and validation work")


def test_validators():
    """Test validator functionality"""
    from core.validator import ValidationPipeline, JSONValidator, LengthValidator

    pipeline = ValidationPipeline()
    pipeline.add_validator(JSONValidator(required_fields=["status"]))
    pipeline.add_validator(LengthValidator(min_length=5))

    # Test valid JSON
    valid_json = '{"status": "ok", "message": "test"}'
    passed, results = pipeline.validate(valid_json)
    assert passed is True

    # Test invalid JSON
    invalid_json = "not json"
    passed, results = pipeline.validate(invalid_json)
    assert passed is False

    # Test short output
    short_output = "hi"
    passed, results = pipeline.validate(short_output)
    assert passed is False

    print("✓ Validators work correctly")


def test_system_in_temp_dir():
    """Test system functionality in temporary directory"""
    from models.config import SystemConfig
    from src import SelfOptimizingSystem

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Configure system to use temp directory
        config = SystemConfig(
            instructions_dir=Path(temp_dir) / "instructions",
            main_model="mock-model",
            critic_model="mock-critic",
            enable_auto_optimization=True,
        )

        # Create system
        system = SelfOptimizingSystem(config)

        # Test getting instructions
        instructions = system.get_current_instructions()
        assert instructions is not None
        assert len(instructions) > 0

        # Test executing query (will use mock models)
        result = system.execute("Test query")
        assert "output" in result
        assert "validation_passed" in result

        print("✓ System works in temporary directory")

    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def run_all_tests():
    """Run all tests"""
    print("Running tests for Self-Optimizing Instruction Library...\n")

    tests = [
        ("Basic imports", test_imports),
        ("SystemConfig", test_system_config),
        ("FailureEntry", test_failure_entry),
        ("CriticResponse", test_critic_response),
        ("Validators", test_validators),
        ("System in temp dir", test_system_in_temp_dir),
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
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
