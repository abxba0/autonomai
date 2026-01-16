#!/usr/bin/env bash
#
# Comprehensive Test Runner
# Runs all test categories with coverage reporting
#

set -e

echo "=================================================="
echo "AutonomAI Comprehensive Test Suite"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

cd "$PROJECT_ROOT"

# Parse arguments
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_LOAD=false
RUN_CHAOS=false
RUN_ALL=false
COVERAGE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            RUN_LOAD=true
            RUN_CHAOS=true
            shift
            ;;
        --unit-only)
            RUN_INTEGRATION=false
            RUN_LOAD=false
            RUN_CHAOS=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            RUN_LOAD=false
            RUN_CHAOS=false
            shift
            ;;
        --load)
            RUN_LOAD=true
            shift
            ;;
        --chaos)
            RUN_CHAOS=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all              Run all test categories including load and chaos"
            echo "  --unit-only        Run only unit tests"
            echo "  --integration-only Run only integration tests"
            echo "  --load             Include load tests"
            echo "  --chaos            Include chaos engineering tests"
            echo "  --no-coverage      Disable coverage reporting"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Create reports directory
mkdir -p tests/reports

echo -e "${BLUE}Installing test dependencies...${NC}"
pip install pytest pytest-cov pytest-asyncio pytest-xdist locust -q

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Run unit tests
if [ "$RUN_UNIT" = true ]; then
    echo -e "\n${BLUE}=== Running Unit Tests ===${NC}"
    
    if [ "$COVERAGE" = true ]; then
        pytest tests/test_unit_core_comprehensive.py \
            -v \
            --cov=src \
            --cov-report=term-missing \
            --cov-report=html:tests/reports/coverage_html \
            --cov-report=json:tests/reports/coverage.json \
            --junit-xml=tests/reports/unit_tests.xml \
            -n auto || UNIT_EXIT=$?
    else
        pytest tests/test_unit_core_comprehensive.py \
            -v \
            --junit-xml=tests/reports/unit_tests.xml \
            -n auto || UNIT_EXIT=$?
    fi
    
    if [ "${UNIT_EXIT:-0}" -eq 0 ]; then
        echo -e "${GREEN}✅ Unit tests passed${NC}"
    else
        echo -e "${RED}❌ Unit tests failed${NC}"
    fi
fi

# Run integration tests
if [ "$RUN_INTEGRATION" = true ]; then
    echo -e "\n${BLUE}=== Running Integration Tests ===${NC}"
    
    pytest tests/test_llm_providers_comprehensive.py \
        -v \
        --junit-xml=tests/reports/integration_tests.xml \
        -n auto || INTEGRATION_EXIT=$?
    
    if [ "${INTEGRATION_EXIT:-0}" -eq 0 ]; then
        echo -e "${GREEN}✅ Integration tests passed${NC}"
    else
        echo -e "${RED}❌ Integration tests failed${NC}"
    fi
fi

# Run load tests
if [ "$RUN_LOAD" = true ]; then
    echo -e "\n${BLUE}=== Running Load & Stress Tests ===${NC}"
    
    pytest tests/test_load_stress_comprehensive.py \
        -v \
        --junit-xml=tests/reports/load_tests.xml \
        -s || LOAD_EXIT=$?
    
    if [ "${LOAD_EXIT:-0}" -eq 0 ]; then
        echo -e "${GREEN}✅ Load tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Load tests completed with issues${NC}"
    fi
fi

# Run chaos engineering tests
if [ "$RUN_CHAOS" = true ]; then
    echo -e "\n${BLUE}=== Running Chaos Engineering Tests ===${NC}"
    
    pytest tests/test_chaos_engineering.py \
        -v \
        --junit-xml=tests/reports/chaos_tests.xml \
        -s || CHAOS_EXIT=$?
    
    if [ "${CHAOS_EXIT:-0}" -eq 0 ]; then
        echo -e "${GREEN}✅ Chaos tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Chaos tests completed with issues${NC}"
    fi
fi

# Generate summary
echo -e "\n${BLUE}=== Test Summary ===${NC}"

if [ "$COVERAGE" = true ] && [ -f "tests/reports/coverage.json" ]; then
    echo ""
    python3 tests/display_coverage.py tests/reports/coverage.json
fi

echo ""
echo "Test Results:"
echo "  Unit Tests:        ${UNIT_EXIT:-0} exit code"
echo "  Integration Tests: ${INTEGRATION_EXIT:-0} exit code"
if [ "$RUN_LOAD" = true ]; then
    echo "  Load Tests:        ${LOAD_EXIT:-0} exit code"
fi
if [ "$RUN_CHAOS" = true ]; then
    echo "  Chaos Tests:       ${CHAOS_EXIT:-0} exit code"
fi

echo ""
echo "Reports saved to: tests/reports/"
if [ "$COVERAGE" = true ]; then
    echo "  Coverage HTML: tests/reports/coverage_html/index.html"
    echo "  Coverage JSON: tests/reports/coverage.json"
fi

# Exit with appropriate code
FINAL_EXIT=0
[ "${UNIT_EXIT:-0}" -ne 0 ] && FINAL_EXIT=1
[ "${INTEGRATION_EXIT:-0}" -ne 0 ] && FINAL_EXIT=1

echo ""
if [ $FINAL_EXIT -eq 0 ]; then
    echo -e "${GREEN}=================================================="
    echo "✅ All critical tests passed!"
    echo -e "==================================================${NC}"
else
    echo -e "${RED}=================================================="
    echo "❌ Some tests failed!"
    echo -e "==================================================${NC}"
fi

exit $FINAL_EXIT
