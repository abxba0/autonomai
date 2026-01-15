#!/usr/bin/env python3
"""
Test the web interface functionality
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_web_imports():
    """Test that web API imports work"""
    print("Testing web API imports...")

    try:
        # Test importing the API module
        from web import api

        print("✓ Web API module imported")

        # Check if FastAPI app is created
        if hasattr(api, "app"):
            print(f"✓ FastAPI app found: {api.app.title}")
        else:
            print("✗ No FastAPI app found")
            return False

        return True

    except Exception as e:
        print(f"✗ Web API import error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\nTesting API endpoints...")

    try:
        from web.api import app

        # Get all routes
        routes = []
        for route in app.routes:
            routes.append(
                {
                    "path": route.path,
                    "methods": list(route.methods) if hasattr(route, "methods") else [],
                    "name": route.name if hasattr(route, "name") else "N/A",
                }
            )

        print(f"✓ Found {len(routes)} API routes")

        # Check for essential endpoints
        essential_endpoints = [
            ("/execute", ["POST"]),
            ("/feedback", ["POST"]),
            ("/status", ["GET"]),
            ("/versions", ["GET"]),
        ]

        for path, methods in essential_endpoints:
            found = False
            for route in routes:
                if route["path"] == path and any(
                    m in route["methods"] for m in methods
                ):
                    found = True
                    break

            if found:
                print(f"✓ Found endpoint: {path} {methods}")
            else:
                print(f"✗ Missing endpoint: {path} {methods}")
                return False

        return True

    except Exception as e:
        print(f"✗ API endpoints error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_system_integration():
    """Test system integration with web API"""
    print("\nTesting system integration...")

    try:
        # Import the main system
        from src import SelfOptimizingSystem

        # Create system instance
        system = SelfOptimizingSystem()
        print("✓ SelfOptimizingSystem created")

        # Test getting instructions
        instructions = system.get_current_instructions()
        print(f"✓ Got instructions: {len(instructions)} chars")

        # Test execution
        test_query = "What is 2+2?"
        result = system.execute(test_query)
        print(f"✓ Executed query: {test_query}")
        print(f"  Result: {result[:50]}...")

        return True

    except Exception as e:
        print(f"✗ System integration error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all web tests"""
    print("=== Web Interface Tests ===\n")

    tests = [
        ("Web API Imports", test_web_imports),
        ("API Endpoints", test_api_endpoints),
        ("System Integration", test_system_integration),
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
        print("\n✅ All web tests passed!")
    else:
        print("\n❌ Some web tests failed")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
