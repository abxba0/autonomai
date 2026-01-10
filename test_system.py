#!/usr/bin/env python3
"""
Test script for the Self-Optimizing Instruction Library
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_imports():
    """Test that all imports work"""
    print("Testing imports...")

    try:
        # Test direct imports from src directory
        import sys

        sys.path.insert(0, "src")

        from models.config import SystemConfig

        print("✓ SystemConfig imported")

        from models.failure import FailureEntry

        print("✓ FailureEntry imported")

        from models.critic_response import CriticResponse

        print("✓ CriticResponse imported")

        from models.version import VersionMetadata

        print("✓ VersionMetadata imported")

        from core.validator import ValidationPipeline, JSONValidator

        print("✓ Validator classes imported")

        print("\nAll imports successful!")
        return True

    except Exception as e:
        print(f"\n✗ Import error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_system_creation():
    """Test creating the main system"""
    print("\nTesting system creation...")

    try:
        # This will test the full import chain
        import sys

        sys.path.insert(0, "src")
        from src import SelfOptimizingSystem

        system = SelfOptimizingSystem()
        print("✓ SelfOptimizingSystem created successfully")

        # Test getting instructions
        instructions = system.get_current_instructions()
        print(f"✓ Got instructions (length: {len(instructions)})")

        return True

    except Exception as e:
        print(f"\n✗ System creation error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_validators():
    """Test validator functionality"""
    print("\nTesting validators...")

    try:
        import sys

        sys.path.insert(0, "src")
        from core.validator import JSONValidator, LengthValidator, ValidationPipeline

        pipeline = ValidationPipeline()
        pipeline.add_validator(JSONValidator(required_fields=["status"]))
        pipeline.add_validator(LengthValidator(min_length=5))

        # Test valid JSON
        valid_json = '{"status": "ok", "message": "test"}'
        passed, results = pipeline.validate(valid_json)
        print(f"✓ Valid JSON test: {passed}")

        # Test invalid JSON
        invalid_json = "not json"
        passed, results = pipeline.validate(invalid_json)
        print(f"✓ Invalid JSON test: {not passed}")

        # Test short output
        short_output = "hi"
        passed, results = pipeline.validate(short_output)
        print(f"✓ Short output test: {not passed}")

        return True

    except Exception as e:
        print(f"\n✗ Validator test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=== Self-Optimizing Instruction Library Tests ===\n")

    tests = [
        ("Imports", test_imports),
        ("System Creation", test_system_creation),
        ("Validators", test_validators),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Test crashed: {e}")
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
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
