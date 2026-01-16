#!/usr/bin/env python3
"""
Coverage report utility for test runner
Reads and displays coverage information
"""

import json
import sys


def display_coverage(coverage_file):
    """Display coverage information from JSON file"""
    try:
        with open(coverage_file, "r") as f:
            cov = json.load(f)
            total_coverage = cov["totals"]["percent_covered"]
            print(f"📊 Code Coverage: {total_coverage:.2f}%")

            if total_coverage >= 90:
                print("✅ Coverage target met (>90%)")
                return 0
            elif total_coverage >= 80:
                print("⚠️  Coverage approaching target (80-90%)")
                return 0
            else:
                print("❌ Coverage below target (<80%)")
                return 1
    except FileNotFoundError:
        print(f"Could not read coverage report: {coverage_file} not found")
        return 2
    except Exception as e:
        print(f"Could not read coverage report: {e}")
        return 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: display_coverage.py <coverage.json>")
        sys.exit(1)

    sys.exit(display_coverage(sys.argv[1]))
