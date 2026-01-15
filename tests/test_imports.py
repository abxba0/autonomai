#!/usr/bin/env python3
"""
Test imports without triggering langchain dependencies
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

print("Testing imports...")

# Test individual modules directly (avoid importing src.__init__)
try:
    from src.models.config import SystemConfig

    print("✓ SystemConfig imported")

    config = SystemConfig(main_model="test")
    print(f"✓ SystemConfig created: {config.main_model}")
except Exception as e:
    print(f"✗ SystemConfig failed: {e}")

try:
    from src.models.critic_response import CriticResponse

    print("✓ CriticResponse imported")

    response = CriticResponse(
        impact_analysis="Test impact analysis with more than 50 characters to meet validation requirements.",
        conflict_analysis="No conflicts detected",
        safety_declaration=True,
        safety_reasoning="This change is safe because it only adds clarification",
        change_type="append",
        proposed_appendix_update="Add test rule",
    )
    print(f"✓ CriticResponse created: {response.change_type}")
except Exception as e:
    print(f"✗ CriticResponse failed: {e}")

try:
    from src.models.version import VersionMetadata

    print("✓ VersionMetadata imported")

    version = VersionMetadata(
        trigger_type="test", critic_justification="test", diff_summary="test"
    )
    print(f"✓ VersionMetadata created: {version.version_id}")
except Exception as e:
    print(f"✗ VersionMetadata failed: {e}")

try:
    from src.core.validator import JSONValidator, LengthValidator

    print("✓ Validators imported")

    json_validator = JSONValidator(required_fields=["status"])
    result = json_validator.validate('{"status": "ok"}')
    print(f"✓ JSONValidator test: {result.passed}")

    length_validator = LengthValidator(min_length=5)
    result = length_validator.validate("hello world")
    print(f"✓ LengthValidator test: {result.passed}")
except Exception as e:
    print(f"✗ Validators failed: {e}")

print("\n✅ Import test completed!")
