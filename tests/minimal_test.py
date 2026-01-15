#!/usr/bin/env python3
"""
Minimal test for the Self-Optimizing Instruction Library
Tests core functionality without external dependencies
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_core_models():
    """Test core data models"""
    print("Testing core models...")

    try:
        # Test SystemConfig
        from models.config import SystemConfig

        config = SystemConfig(
            main_model="mock-model",
            critic_model="mock-critic",
            enable_auto_optimization=True,
        )
        print(f"✓ SystemConfig created: {config.main_model}")

        # Test CriticResponse
        from models.critic_response import CriticResponse

        critic_response = CriticResponse(
            impact_analysis="This is a detailed impact analysis that explains why this change is needed for the system to work properly.",
            conflict_analysis="No conflicts with existing rules.",
            safety_declaration=True,
            safety_reasoning="This change is safe because it only adds validation without affecting existing functionality.",
            change_type="append",
            proposed_appendix_update="**New Rule**: Always validate JSON output before returning it.",
        )
        print(f"✓ CriticResponse created: {critic_response.change_type}")

        # Test VersionMetadata
        from models.version import VersionMetadata

        version = VersionMetadata(
            version_id="v1.0.0",
            timestamp="2025-01-10T13:51:51",
            trigger_type="auto_validation",
            critic_justification="Initial version",
            diff_summary="Initial version",
        )
        print(f"✓ VersionMetadata created: {version.version_id}")

        return True

    except Exception as e:
        print(f"✗ Core models error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_validators():
    """Test validator functionality"""
    print("\nTesting validators...")

    try:
        from core.validator import JSONValidator, LengthValidator, ValidationPipeline

        # Test JSONValidator
        json_validator = JSONValidator(required_fields=["status"])
        result = json_validator.validate('{"status": "ok"}')
        print(f"✓ JSONValidator test: {result.passed}")

        # Test LengthValidator
        length_validator = LengthValidator(min_length=5)
        result = length_validator.validate("hello world")
        print(f"✓ LengthValidator test: {result.passed}")

        # Test ValidationPipeline
        pipeline = ValidationPipeline()
        pipeline.add_validator(json_validator)
        pipeline.add_validator(length_validator)

        passed, results = pipeline.validate('{"status": "ok"}')
        print(f"✓ ValidationPipeline test: {passed}")

        return True

    except Exception as e:
        print(f"✗ Validators error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_storage():
    """Test storage functionality"""
    print("\nTesting storage...")

    try:
        # Test MarkdownHandler
        from src.storage.markdown_handler import MarkdownHandler

        handler = MarkdownHandler()
        print("✓ MarkdownHandler created")

        # Test reading/writing
        test_content = "# Test Instructions\n\nThis is a test."
        handler.write_instructions(test_content)
        read_content = handler.read_instructions()
        print(f"✓ Markdown read/write test: {len(read_content)} chars")

        return True

    except Exception as e:
        print(f"✗ Storage error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_instruction_manager():
    """Test instruction manager"""
    print("\nTesting instruction manager...")

    try:
        from src.core.instruction_manager import InstructionManager

        manager = InstructionManager()
        print("✓ InstructionManager created")

        # Test getting instructions
        instructions = manager.get_current_instructions()
        print(f"✓ Got instructions: {len(instructions)} chars")

        # Test version control
        versions = manager.get_version_history()
        print(f"✓ Got version history: {len(versions)} versions")

        return True

    except Exception as e:
        print(f"✗ Instruction manager error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=== Minimal Self-Optimizing System Tests ===\n")

    tests = [
        ("Core Models", test_core_models),
        ("Validators", test_validators),
        ("Storage", test_storage),
        ("Instruction Manager", test_instruction_manager),
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
