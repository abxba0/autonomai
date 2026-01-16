# AutonomAI Testing Suite

Comprehensive testing infrastructure for AutonomAI with >90% code coverage target.

## Quick Start

### Run All Critical Tests
```bash
./tests/run_comprehensive_tests.sh
```

### Run Specific Test Suites

**Unit Tests:**
```bash
pytest tests/test_unit_core_comprehensive.py -v
```

**Integration Tests:**
```bash
pytest tests/test_llm_providers_comprehensive.py -v
```

**Load & Stress Tests:**
```bash
pytest tests/test_load_stress_comprehensive.py -v
```

**Chaos Engineering Tests:**
```bash
pytest tests/test_chaos_engineering.py -v
```

### With Coverage
```bash
pytest tests/test_unit_core_comprehensive.py \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:coverage_html
```

## Test Suites

### 🧪 Unit Tests (`test_unit_core_comprehensive.py`)
**36 tests** covering core components:
- Validators (JSON, Regex, Length, Custom)
- ValidationPipeline
- FailureEntry model
- CriticResponse validation
- SystemConfig
- Edge cases (unicode, empty, None, special chars)

**Target:** >90% coverage of core components

### 🔌 Integration Tests (`test_llm_providers_comprehensive.py`)
**80+ tests** for all LLM providers:
- OpenAI (GPT-4, GPT-3.5-turbo, GPT-4o)
- Anthropic (Claude-3 family)
- Google (Gemini Pro, Gemini 1.5)
- DeepSeek
- OpenRouter

**Coverage:**
- Provider detection and initialization
- Multi-provider scenarios
- Error handling (timeouts, rate limits)
- Configuration management
- Concurrent requests

### 📊 Load & Stress Tests (`test_load_stress_comprehensive.py`)
**60+ tests** for performance and scalability:

**Multi-Tenant:**
- Concurrent tenant requests
- Tenant isolation
- Resource limits

**Batch Processing:**
- Large batches (100+ items)
- Concurrent submissions
- Queue saturation

**Database:**
- Connection pool stress (50+ connections)
- Concurrent writes

**Cache:**
- Concurrent access (50+ readers)
- Hit rate under load
- Memory pressure

**Resources:**
- Memory exhaustion
- Thread pool saturation
- Disk I/O stress

**Benchmarks:**
- Request latency
- Throughput
- Scalability

### 💥 Chaos Engineering Tests (`test_chaos_engineering.py`)
**80+ tests** for fault simulation:

**Network Failures:**
- API timeouts
- Network partitions
- Intermittent connectivity
- DNS failures
- Packet loss

**Service Failures:**
- Redis unavailable
- Database failures
- LLM API down
- Cascading failures

**Resource Exhaustion:**
- Memory exhaustion
- Disk space exhaustion
- File descriptor limits
- CPU saturation

**Byzantine Failures:**
- Corrupted data
- Inconsistent state
- Split-brain scenarios

**Fallback & Recovery:**
- Circuit breakers
- Bulkhead isolation
- Graceful degradation
- Self-healing
- Exponential backoff

### 🚀 Continuous Load Testing (`locustfile.py`)
Locust-based load testing with three user types:

**TenantUser** - Typical usage:
- Execute queries
- Health checks
- Batch submission
- Wait: 1-3 seconds

**BatchProcessingUser** - Batch workloads:
- Large batch submission (50 items)
- Status checking
- Batch listing
- Wait: 2-5 seconds

**StressTestUser** - High intensity:
- Rapid-fire requests
- Concurrent requests
- Wait: 0.1-0.5 seconds

**Run Locust:**
```bash
# Web UI
locust -f tests/locustfile.py --host=http://localhost:8000

# Headless
locust -f tests/locustfile.py --host=http://localhost:8000 \
  --headless -u 50 -r 5 -t 300

# Distributed
locust -f tests/locustfile.py --master --host=http://localhost:8000
locust -f tests/locustfile.py --worker --master-host=<master-ip>
```

## Test Runner Script

The `run_comprehensive_tests.sh` script provides a unified interface:

```bash
# Run all critical tests (unit + integration)
./tests/run_comprehensive_tests.sh

# Run all tests including load and chaos
./tests/run_comprehensive_tests.sh --all

# Run specific categories
./tests/run_comprehensive_tests.sh --unit-only
./tests/run_comprehensive_tests.sh --integration-only
./tests/run_comprehensive_tests.sh --load
./tests/run_comprehensive_tests.sh --chaos

# Without coverage
./tests/run_comprehensive_tests.sh --no-coverage
```

**Output:**
- Coverage reports (HTML, JSON, XML)
- JUnit XML test results
- Summary statistics
- Reports in `tests/reports/`

## CI/CD Integration

### GitHub Actions Workflow
Located at `.github/workflows/comprehensive-testing.yml`

**Jobs:**
1. **unit-tests** - Python 3.8-3.11 matrix
2. **integration-tests** - All LLM providers
3. **load-tests** - Scheduled/manual
4. **chaos-tests** - Scheduled/manual
5. **test-summary** - Aggregated results
6. **coverage-report** - Coverage tracking

**Triggers:**
- Push to main, develop, copilot/** branches
- Pull requests to main or develop
- Daily schedule (3 AM UTC)
- Manual workflow dispatch

**Manual Trigger:**
```bash
gh workflow run comprehensive-testing.yml \
  -f run_chaos=true \
  -f run_load=true
```

## Coverage Goals

| Component | Target | Status |
|-----------|--------|--------|
| Core components | >90% | ✅ |
| Validators | >95% | ✅ |
| Models | >90% | ✅ |
| LLM Providers | 100% | ✅ |
| Cache | >85% | ✅ |
| Security | >85% | ✅ |

## Best Practices

### Writing Tests
1. **Independence**: Each test runs independently
2. **Clear Names**: Descriptive test function names
3. **AAA Pattern**: Arrange-Act-Assert
4. **Mock External**: Use mocks for external APIs
5. **Edge Cases**: Include boundary conditions
6. **Documentation**: Docstrings for complex tests

### Running Tests Locally
```bash
# Fast feedback during development
pytest tests/test_unit_core_comprehensive.py -v -k "test_json"

# With coverage
pytest tests/test_unit_core_comprehensive.py --cov=src --cov-report=term-missing

# Parallel execution
pytest tests/ -n auto

# Show output
pytest tests/test_unit_core_comprehensive.py -v -s

# Debug mode
pytest tests/test_unit_core_comprehensive.py --pdb
```

### Debugging
```bash
# Show local variables on failure
pytest tests/test_unit_core_comprehensive.py -l

# Full output
pytest tests/test_unit_core_comprehensive.py -v -s

# Stop on first failure
pytest tests/test_unit_core_comprehensive.py -x
```

## Metrics

### Test Metrics
- Code Coverage: Line and branch
- Test Count: Total and per category
- Pass Rate: Percentage passing
- Execution Time: Per test and total
- Flakiness: Intermittent failures

### Performance Metrics
- Request Latency: P50, P95, P99
- Throughput: Requests/second
- Error Rate: Failed requests %
- Resource Usage: CPU, memory, disk

### Chaos Metrics
- MTTR: Mean time to recovery
- Failure Impact: Requests affected %
- Fallback Success: Rate of successful fallbacks
- Circuit Breaker: State transitions

## Troubleshooting

### Tests Hanging
- Check for blocking I/O
- Use appropriate timeouts
- Run with `-s` flag

### Low Coverage
- Check untested branches
- Review HTML coverage report
- Add edge case tests

### Flaky Tests
- Look for race conditions
- Check time-dependent assertions
- Use fixtures for consistent state

### Resource Exhaustion
- Use cleanup fixtures
- Implement proper teardown
- Limit concurrent execution

## Documentation

Full documentation: [`docs/COMPREHENSIVE_TESTING.md`](../docs/COMPREHENSIVE_TESTING.md)

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Maintain >90% coverage
3. Add integration tests for new providers
4. Consider edge cases
5. Update documentation
6. Run full test suite before PR

## References

- [pytest documentation](https://docs.pytest.org/)
- [Locust documentation](https://docs.locust.io/)
- [Chaos Engineering principles](https://principlesofchaos.org/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
