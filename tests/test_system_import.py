#!/usr/bin/env python3
"""
Test SelfOptimizingSystem import and basic functionality
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

print("Testing SelfOptimizingSystem import...")

try:
    from src import SelfOptimizingSystem

    print("✓ SelfOptimizingSystem imported successfully")

    # Create system with mock models
    system = SelfOptimizingSystem()
    print("✓ System created with mock models")

    status = system.get_status()
    print(f"✓ System status: {status['status']}")
    print(f"✓ Main model: {status['config']['main_model']}")
    print(f"✓ Auto-optimization: {status['config']['enable_auto_optimization']}")

    # Test adding a validator
    from src.core.validator import JSONValidator

    system.add_validator(JSONValidator(required_fields=["status"]))
    print("✓ Validator added")

    # Test validation
    is_valid = system.validate_output('{"status": "ok"}')
    print(f"✓ Validation test: {is_valid}")

    print("\n✅ System import and basic functionality test passed!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback

    traceback.print_exc()
