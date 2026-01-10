#!/usr/bin/env python3
"""
Simple test for the Self-Optimizing Instruction Library
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Now imports should work
try:
    print("Testing imports from src directory...")

    from models.config import SystemConfig

    print("✓ SystemConfig imported")

    from models.critic_response import CriticResponse

    print("✓ CriticResponse imported")

    from models.version import VersionMetadata

    print("✓ VersionMetadata imported")

    from core.validator import ValidationPipeline, JSONValidator, LengthValidator

    print("✓ Validator classes imported")

    # Test creating a failure entry (using the config model)
    from models.config import FailureEntry

    failure = FailureEntry(
        trigger_type="auto_validation",
        failure_description="Test failure",
        user_query="Test query",
        last_model_output="Test output",
    )
    print(f"✓ Created FailureEntry: {failure.id}")

    # Test validators
    pipeline = ValidationPipeline()
    pipeline.add_validator(JSONValidator(required_fields=["status"]))
    pipeline.add_validator(LengthValidator(min_length=5))

    test_json = '{"status": "ok"}'
    passed, results = pipeline.validate(test_json)
    print(f"✓ JSON validation test: {passed}")

    # Test CriticResponse
    critic_response = CriticResponse(
        impact_analysis="This is a detailed impact analysis that explains why this change is needed for the system to work properly.",
        conflict_analysis="No conflicts with existing rules.",
        safety_declaration=True,
        safety_reasoning="This change is safe because it only adds validation without affecting existing functionality.",
        change_type="append",
        proposed_appendix_update="**New Rule**: Always validate JSON output before returning it.",
    )
    print(f"✓ Created CriticResponse: {critic_response.change_type}")

    # Test SystemConfig
    config = SystemConfig(
        main_model="test-model",
        critic_model="test-critic",
        enable_auto_optimization=True,
    )
    print(f"✓ Created SystemConfig: {config.main_model}")

    print("\n✅ All basic tests passed!")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
