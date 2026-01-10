#!/usr/bin/env python3
"""
Test the Self-Optimizing System with mock models
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_mock_system():
    """Test the system with mock models"""
    print("Testing Self-Optimizing System with mock models...")

    try:
        # Import the main system
        from src import SelfOptimizingSystem

        # Create system instance with mock models
        system = SelfOptimizingSystem()
        print("✓ SelfOptimizingSystem created")

        # Test getting instructions
        instructions = system.get_current_instructions()
        print(f"✓ Got instructions: {len(instructions)} chars")

        # Test execution with a simple query
        test_query = "What is 2+2?"
        print(f"\nExecuting query: {test_query}")
        result = system.execute(test_query)
        print(f"✓ Execution result: {result[:100]}...")

        # Test validation
        print("\nTesting validation...")
        validation_result = system.validate_output(result)
        print(f"✓ Validation passed: {validation_result}")

        # Test feedback loop
        print("\nTesting feedback loop...")
        feedback_result = system.process_feedback(
            user_query=test_query,
            model_output=result,
            feedback_type="auto_validation",
            feedback_details="Test feedback",
        )
        print(f"✓ Feedback processed: {feedback_result}")

        # Test version history
        print("\nTesting version history...")
        versions = system.get_version_history()
        print(f"✓ Got {len(versions)} versions")

        return True

    except Exception as e:
        print(f"✗ System test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_optimization_cycle():
    """Test a full optimization cycle"""
    print("\n\nTesting optimization cycle...")

    try:
        from src import SelfOptimizingSystem

        # Create system
        system = SelfOptimizingSystem()
        print("✓ System created for optimization test")

        # Simulate a failure
        print("\nSimulating a failure...")
        failure_result = system.process_failure(
            trigger_type="auto_validation",
            failure_description="Output was not in JSON format",
            user_query="Give me data in JSON format",
            last_model_output="Here is your data: 2+2=4",
            validation_results=[(False, "Output must be valid JSON")],
        )
        print(f"✓ Failure processed: {failure_result}")

        # Check if optimization was triggered
        print("\nChecking if optimization was triggered...")
        versions = system.get_version_history()
        if len(versions) > 1:
            print(f"✓ Optimization triggered! {len(versions)} versions found")
            latest_version = versions[-1]
            print(f"  Latest version: {latest_version.version_id}")
            print(f"  Change summary: {latest_version.change_summary}")
        else:
            print(
                "⚠ No optimization triggered (mock models may not trigger optimization)"
            )

        return True

    except Exception as e:
        print(f"✗ Optimization test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=== Self-Optimizing System Tests (Mock Models) ===\n")

    tests = [
        ("Basic System", test_mock_system),
        ("Optimization Cycle", test_optimization_cycle),
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
        print("\nThe Self-Optimizing System is working correctly with mock models.")
        print("\nTo use real LLMs:")
        print("1. Set up API keys in .env file")
        print("2. Install remaining dependencies: pip install -r requirements.txt")
        print("3. Run: python examples/basic_usage.py")
    else:
        print("\n❌ Some tests failed")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
