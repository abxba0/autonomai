# Regression Testing Suite

## Overview

The AutonomAI regression testing suite provides comprehensive automated testing for all major pipelines and critical edge cases. The suite is production-ready, uses real implementations (no mocks), and is fully integrated with CI/CD.

## Features

### ✅ Comprehensive Test Coverage
- **Core Pipeline Tests**: System initialization, instruction loading, validation pipeline, failure logging
- **Workflow Tests**: Workflow orchestration, step dependencies, execution
- **Caching Tests**: Cache initialization, hit rate, performance
- **Security Tests**: Input validation, rate limiting, authentication
- **Edge Case Tests**: Boundary conditions, error handling, concurrent access
- **Plugin System Tests**: Plugin loading, metadata, lifecycle

### 📊 Performance Benchmarking
- Automatic performance measurement for all tests
- Baseline comparison and regression detection
- 20% performance degradation threshold alerts
- Historical performance tracking

### 🔬 A/B Testing with Statistical Validation
- Welch's t-test for statistical significance
- 95% confidence interval calculation
- Automated comparison of implementation variants
- P-value reporting (α = 0.05)

### 🔧 Golden Dataset Self-Healing
- Automatic deviation detection
- Self-healing mechanism for failing tests
- Comprehensive deviation reporting
- Healing log export for audit

### 🚀 CI/CD Integration
- GitHub Actions workflow included
- Multi-version Python testing (3.8, 3.9, 3.10, 3.11)
- Automated PR comments with test results
- Daily scheduled runs for continuous monitoring
- Performance baseline tracking across commits

## Installation

The regression test suite uses standard Python dependencies already included in the project:

```bash
# Install base dependencies
pip install -r requirements.txt

# Optional: Install pytest for additional test features
pip install pytest pytest-cov pytest-xdist
```

## Running Tests Locally

### Run Complete Regression Suite

```bash
# Run all tests with performance benchmarks
python tests/test_regression_comprehensive.py
```

This will:
1. Run all test categories
2. Generate performance benchmarks
3. Execute A/B tests
4. Test golden dataset self-healing
5. Generate comprehensive report in `tests/regression_reports/`

### Run Specific Test Categories

```python
# Run only core pipeline tests
from tests.test_regression_comprehensive import CorePipelineTests, RegressionTestSuite

suite = RegressionTestSuite()
core_tests = CorePipelineTests(suite)
core_tests.run_all()
suite.generate_report()
```

### Run Performance Benchmarks

```python
from tests.regression_suite import PerformanceBenchmark

benchmark = PerformanceBenchmark()

# Benchmark a function
result = benchmark.benchmark(
    test_name="my_test",
    category="performance",
    test_func=lambda: my_function(),
    iterations=10,
    update_baseline=True  # Update baseline after run
)

print(f"Execution time: {result.execution_time_ms:.2f}ms")
```

### Run A/B Tests

```python
from tests.regression_suite import ABTester

ab_tester = ABTester()

# Compare two implementations
result = ab_tester.run_ab_test(
    test_name="optimization_comparison",
    variant_a=original_implementation,
    variant_b=optimized_implementation,
    iterations=30
)

print(f"Improvement: {result.improvement_percent:.1f}%")
print(f"Statistically significant: {result.statistically_significant}")
```

### Test Golden Dataset Self-Healing

```python
from src import SelfOptimizingSystem
from src.core.golden_dataset import GoldenDataset
from tests.regression_suite import GoldenDatasetSelfHealing

system = SelfOptimizingSystem()
dataset = GoldenDataset(storage_path=Path("golden_dataset.json"))

healer = GoldenDatasetSelfHealing(dataset, system)
report = healer.test_and_heal(auto_heal=True)

print(f"Passed: {report.passed}, Failed: {report.failed}, Healed: {report.healed}")
```

## CI/CD Integration

### GitHub Actions Workflow

The regression test suite automatically runs on:
- **Push** to main, develop, or copilot/** branches
- **Pull requests** to main or develop
- **Daily schedule** at 2 AM UTC
- **Manual trigger** via workflow_dispatch

### Workflow Jobs

1. **regression-tests**: Runs full test suite on multiple Python versions
2. **golden-dataset-validation**: Validates golden dataset integrity
3. **benchmark-comparison**: Compares performance between PR and base branch
4. **test-summary**: Aggregates results and creates summary

### Artifacts

The workflow produces the following artifacts:
- `regression-reports-py{version}`: Detailed test reports per Python version
- `performance-baseline`: Performance baseline data (main branch only)

Reports are retained for:
- Test reports: 30 days
- Performance baselines: 90 days

### PR Comments

On pull requests, the workflow automatically comments with:
- Pass/fail counts
- Pass rate percentage
- Performance regression alerts
- Link to detailed reports

## Test Reports

### Report Structure

Test reports are saved as JSON in `tests/regression_reports/regression_report.json`:

```json
{
  "timestamp": "2024-01-16T10:30:00",
  "summary": {
    "total_tests": 25,
    "passed": 24,
    "failed": 1,
    "pass_rate": 96.0
  },
  "results": [
    {
      "test_name": "core_system_initialization",
      "category": "core_pipeline",
      "passed": true,
      "execution_time_ms": 125.5,
      "benchmark": {
        "execution_time_ms": 123.2,
        "metadata": {
          "iterations": 3,
          "min_time_ms": 120.1,
          "max_time_ms": 127.3,
          "std_dev_ms": 2.9
        }
      }
    }
  ],
  "performance_regressions": []
}
```

### Performance Baseline

Performance baselines are stored in `tests/data/performance_baseline.json`:

```json
{
  "perf_system_init": {
    "test_name": "perf_system_init",
    "category": "performance",
    "execution_time_ms": 125.5,
    "timestamp": "2024-01-16T10:30:00",
    "metadata": {
      "iterations": 5,
      "min_time_ms": 122.0,
      "max_time_ms": 130.0
    }
  }
}
```

## Writing New Tests

### Basic Test Structure

```python
from tests.regression_suite import RegressionTestSuite, TestCategory

suite = RegressionTestSuite()

def test_my_feature():
    """Test description"""
    def test():
        # Test implementation
        result = my_function()
        assert result == expected_value
    
    suite.run_test(
        "test_my_feature",
        TestCategory.CORE_PIPELINE,
        test,
        enable_benchmark=True  # Optional performance benchmarking
    )
```

### Test with Performance Benchmark

```python
def test_with_benchmark():
    """Test with performance benchmarking"""
    def test():
        # This will be benchmarked automatically
        result = expensive_operation()
        assert result is not None
    
    suite.run_test(
        "expensive_operation_test",
        TestCategory.CORE_PIPELINE,
        test,
        enable_benchmark=True
    )
```

### A/B Test

```python
from tests.regression_suite import ABTester

ab_tester = ABTester()

def test_ab_comparison():
    """Compare two implementations"""
    
    def variant_a():
        # Original implementation
        return old_algorithm()
    
    def variant_b():
        # New implementation
        return new_algorithm()
    
    result = ab_tester.run_ab_test(
        "algorithm_comparison",
        variant_a,
        variant_b,
        iterations=30
    )
    
    # Only proceed if improvement is statistically significant
    if result.statistically_significant and result.improvement_percent > 10:
        print("✅ New implementation is significantly better!")
```

## Best Practices

### 1. Use Real Implementations
- ❌ Don't mock system components
- ✅ Use actual system instances
- ✅ Use temporary directories for file operations

### 2. Ensure Reproducibility
- ✅ Use fixed random seeds when needed
- ✅ Clean up resources in teardown
- ✅ Avoid dependencies on external services

### 3. Performance Testing
- ✅ Run benchmarks with sufficient iterations (≥3)
- ✅ Update baselines after intentional changes
- ✅ Set appropriate regression thresholds

### 4. Edge Case Coverage
- ✅ Test boundary conditions
- ✅ Test error handling
- ✅ Test concurrent access
- ✅ Test large inputs

### 5. Statistical Validation
- ✅ Use adequate sample sizes (≥30 for t-tests)
- ✅ Report confidence intervals
- ✅ Check for statistical significance before claiming improvements

## Troubleshooting

### Tests Fail Locally But Pass in CI
- Check Python version differences
- Verify all dependencies are installed
- Check for environment-specific configurations

### Performance Regressions Detected
1. Review the specific test that regressed
2. Check if changes were intentional
3. Update baseline if acceptable: `update_baseline=True`
4. Investigate and optimize if unintentional

### Golden Dataset Self-Healing Issues
- Check dataset file permissions
- Verify system can execute queries
- Review healing log for details
- Manually inspect failing interactions

### CI Workflow Failures
- Check GitHub Actions logs for details
- Verify all required files are committed
- Check for Python version compatibility
- Review artifact uploads

## Performance Targets

### Baseline Performance Goals
- System initialization: < 200ms
- Validation pipeline: < 50ms
- Instruction loading: < 100ms
- Cache operations: < 10ms

### Regression Thresholds
- Performance degradation: > 20% slower
- Pass rate: < 90%
- Statistical significance: p < 0.05

## Continuous Improvement

### Updating Baselines
When intentional performance improvements or changes are made:

```python
# Update baseline after optimization
benchmark = PerformanceBenchmark()
benchmark.benchmark(
    test_name="optimized_function",
    category="performance",
    test_func=optimized_function,
    update_baseline=True  # ← Update baseline
)
```

### Adding New Test Categories
1. Add new category to `TestCategory` enum
2. Create test class following existing patterns
3. Add to main test runner
4. Update documentation

### Monitoring Test Health
- Review daily CI runs
- Track pass rate trends
- Monitor performance baselines
- Investigate flaky tests

## Support

For issues or questions about the regression test suite:
1. Check this documentation
2. Review test implementation in `tests/test_regression_comprehensive.py`
3. Check CI logs in GitHub Actions
4. Open an issue on GitHub

## License

This test suite is part of AutonomAI and follows the same MIT license.
