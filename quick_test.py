#!/usr/bin/env python3
"""
Quick test of the system
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("Quick test of SelfOptimizingSystem...")

try:
    from src import SelfOptimizingSystem

    # Create system
    system = SelfOptimizingSystem()
    print("✓ System created")

    # Execute a query
    result = system.execute("Hello, world!")
    print("✓ Execution completed")
    print(f"  Validation passed: {result['validation_passed']}")
    print(f"  Output: {result['output'][:50]}...")

    # Test validation
    is_valid = system.validate_output(result["output"])
    print(f"✓ Validation test: {is_valid}")

    # Get status
    status = system.get_status()
    print(f"✓ System status: {status['status']}")

    print("\n✅ Quick test passed!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback

    traceback.print_exc()
