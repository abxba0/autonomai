#!/usr/bin/env bash
#
# Quick Start Script for Regression Testing Suite
# 
# This script runs the comprehensive regression test suite and generates reports.
#

set -e  # Exit on error

echo "=================================================="
echo "AutonomAI Regression Testing Suite"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

cd "$PROJECT_ROOT"

# Create necessary directories
echo "Creating test directories..."
mkdir -p tests/data
mkdir -p tests/regression_reports

# Parse command line arguments
MODE="full"
UPDATE_BASELINE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            MODE="quick"
            shift
            ;;
        --benchmark)
            MODE="benchmark"
            shift
            ;;
        --update-baseline)
            UPDATE_BASELINE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick              Run quick test suite (core tests only)"
            echo "  --benchmark          Run performance benchmarks only"
            echo "  --update-baseline    Update performance baselines"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check dependencies
echo ""
echo "Checking dependencies..."
if ! python3 -c "import sys; sys.path.insert(0, 'src'); from src import SelfOptimizingSystem" 2>/dev/null; then
    echo -e "${YELLOW}Warning: Some dependencies might be missing${NC}"
    echo "Install with: pip install -r requirements.txt"
fi

# Run tests based on mode
echo ""
if [ "$MODE" == "full" ]; then
    echo "Running FULL regression test suite..."
    echo "This includes:"
    echo "  - All test categories"
    echo "  - Performance benchmarks"
    echo "  - A/B tests"
    echo "  - Golden dataset validation"
    echo ""
    
    python3 tests/test_regression_comprehensive.py
    EXIT_CODE=$?
    
elif [ "$MODE" == "quick" ]; then
    echo "Running QUICK regression tests (core tests only)..."
    echo ""
    
    python3 -c "
import sys
sys.path.insert(0, 'tests')
from test_regression_comprehensive import CorePipelineTests, RegressionTestSuite

suite = RegressionTestSuite()
core_tests = CorePipelineTests(suite)
core_tests.run_all()
suite.generate_report('quick_report.json')
"
    EXIT_CODE=$?
    
elif [ "$MODE" == "benchmark" ]; then
    echo "Running performance benchmarks..."
    echo ""
    
    python3 -c "
import sys
sys.path.insert(0, 'tests')
from test_regression_comprehensive import run_performance_benchmarks, RegressionTestSuite

suite = RegressionTestSuite()
run_performance_benchmarks(suite)
suite.generate_report('benchmark_report.json')
"
    EXIT_CODE=$?
fi

# Check exit code
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=================================================="
    echo "✅ Tests completed successfully!"
    echo -e "==================================================${NC}"
else
    echo -e "${RED}=================================================="
    echo "❌ Tests failed with exit code $EXIT_CODE"
    echo -e "==================================================${NC}"
fi

# Show report location
echo ""
echo "Reports saved to: tests/regression_reports/"
if [ -f "tests/regression_reports/regression_report.json" ]; then
    echo ""
    echo "Test Summary:"
    python3 -c "
import json
try:
    with open('tests/regression_reports/regression_report.json', 'r') as f:
        report = json.load(f)
        summary = report['summary']
        print(f\"  Total Tests:  {summary['total_tests']}\")
        print(f\"  Passed:       {summary['passed']}\")
        print(f\"  Failed:       {summary['failed']}\")
        print(f\"  Pass Rate:    {summary['pass_rate']:.1f}%\")
        
        if report.get('performance_regressions'):
            print(f\"  ⚠️  Performance Regressions: {len(report['performance_regressions'])}\")
except Exception as e:
    print(f\"  Error reading report: {e}\")
"
fi

# Update baseline if requested
if [ "$UPDATE_BASELINE" = true ]; then
    echo ""
    echo "Updating performance baseline..."
    if [ -f "tests/data/performance_baseline.json" ]; then
        echo -e "${GREEN}✅ Performance baseline updated${NC}"
    else
        echo -e "${YELLOW}⚠️  No baseline file found${NC}"
    fi
fi

echo ""
echo "For more information, see: tests/REGRESSION_TESTING_README.md"

exit $EXIT_CODE
