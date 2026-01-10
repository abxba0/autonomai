#!/usr/bin/env python3
"""
Basic usage example for the Self-Optimizing Instruction Library
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem, JSONValidator, LengthValidator


def main():
    """Demonstrate basic usage of the self-optimizing system"""

    print("=== Self-Optimizing Instruction Library Demo ===\n")

    # Initialize the system
    print("1. Initializing system...")
    system = SelfOptimizingSystem()

    # Add validators
    print("2. Adding validators...")
    system.add_validator(JSONValidator(required_fields=["status", "result"]))
    system.add_validator(LengthValidator(min_length=10, max_length=500))

    # Show initial instructions
    print("\n3. Initial instructions:")
    print("-" * 50)
    print(system.get_current_instructions()[:500] + "...")
    print("-" * 50)

    # Execute a query that should fail validation
    print("\n4. Executing query that should fail validation...")
    result = system.execute("Generate a JSON status report")

    print(f"Output: {result['output'][:100]}...")
    print(f"Validation passed: {result['validation_passed']}")

    if not result["validation_passed"]:
        print(f"Validation errors: {result['validation_results']}")

        if result.get("optimization_attempted"):
            opt_result = result["optimization_result"]
            print(f"Optimization attempted: {opt_result['success']}")
            if opt_result["success"]:
                print("System learned from failure and updated instructions!")

    # Show updated instructions
    print("\n5. Updated instructions:")
    print("-" * 50)
    print(system.get_current_instructions()[:500] + "...")
    print("-" * 50)

    # Test with manual feedback
    print("\n6. Testing manual feedback...")
    feedback_result = system.request_instruction_update(
        "The responses are too technical. Please use simpler language.",
        severity="moderate",
    )

    print(f"Manual optimization: {feedback_result.get('success', False)}")

    # Show version history
    print("\n7. Version history:")
    history = system.get_version_history()
    for version in history[-3:]:  # Show last 3 versions
        print(
            f"  - {version['version_id']}: {version['trigger_type']} - {version['diff_summary']}"
        )

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
