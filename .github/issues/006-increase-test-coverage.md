# TESTING: Increase test coverage and fix test quality

**Labels:** `testing`, `quality`, `priority-2`

## Summary

Current state:
- **Source**: 56 files, ~17,800 lines
- **Tests**: 41 files, ~11,880 lines
- **Ratio**: 0.67 (industry target: 1.0+)
- **Pytest collected**: only ~33 actual test cases
- **Orphan test files**: `test_basic.py`, `minimal_test.py`, `final_test.py`, `quick_test.py` — leftover debugging, not real tests

The test count is misleadingly low relative to the test LOC, suggesting many test files contain helpers, setup code, or incomplete tests rather than actual assertions.

## Specific Gaps

### 1. No unit tests for critical paths
- `WorkflowOrchestrator` (1506 lines) — no dedicated unit tests for conditional execution, loop handling, or subworkflows
- `DistributedStateManager` — no tests verifying distributed lock behavior
- `InstructionManager` version control — no tests for rollback edge cases
- Security modules (auth, rate limiting) — minimal coverage

### 2. Integration tests depend on external services
- LLM provider tests require API keys (skip without them)
- Redis tests require a running Redis instance
- No CI-friendly mocking strategy for these dependencies

### 3. No property-based testing
- Validator pipeline is a perfect candidate for property-based tests (arbitrary JSON, arbitrary strings)
- No `hypothesis` usage anywhere

### 4. Orphan/debug test files
These files appear to be leftovers from debugging sessions, not systematic test suites:
- `tests/test_basic.py`
- `tests/minimal_test.py`
- `tests/final_test.py`
- `tests/quick_test.py`
- `tests/test_simple_test.py`
- `tests/test_mock_system.py`

## Proposed Fix

### Phase 1: Cleanup (1-2 days)
1. Delete or consolidate orphan test files
2. Run `pytest --collect-only` and document actual test count
3. Set up `pytest-cov` in CI with a minimum threshold (start at 60%, target 85%)

### Phase 2: Critical path coverage (3-5 days)
4. Add unit tests for `WorkflowOrchestrator` — at minimum:
   - Plan generation with mocked LLM
   - Step execution for each step type
   - Conditional branching (true/false paths)
   - Loop execution (including max iteration safety)
   - Error recovery and partial workflow results
5. Add unit tests for security modules:
   - JWT token creation/validation/expiry
   - Rate limiter behavior at boundary conditions
   - Input sanitization for each attack vector

### Phase 3: Quality improvements (ongoing)
6. Add `hypothesis` for property-based testing of validators
7. Create `tests/conftest.py` with shared fixtures (mock LLM, mock Redis, test configs)
8. Add integration test suite that runs in CI with Docker Compose (Redis, API)
9. Target: 85%+ line coverage, 100% for validators and security

## Files

- `tests/` (entire directory)
- `pytest.ini` or `pyproject.toml` [tool.pytest] section
- `.github/workflows/` (CI configuration)
