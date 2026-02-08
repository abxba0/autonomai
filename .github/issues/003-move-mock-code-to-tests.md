# CLEANUP: Move mock/demo classes out of production source code

**Labels:** `tech-debt`, `cleanup`, `priority-2`

## Summary

Multiple `Mock*` classes and demo data are defined inside production source files in `src/core/`. These should live in `tests/` as fixtures, not ship with the production package.

### Mock classes in production code

| File | Class | Line |
|------|-------|------|
| `src/core/main_model.py` | `MockModel` | 497 |
| `src/core/main_model.py` | `MockResponse` (nested) | 589 |
| `src/core/critic_model.py` | `MockCriticModel` | 795 |
| `src/core/critic_model.py` | `MockResponse` (nested) | 805 |
| `src/core/judge_model.py` | `MockJudgeModel` | 440 |
| `src/core/judge_model.py` | `MockResponse` (nested) | 450 |
| `src/core/rule_graph.py` | `MockRuleGraph` | 632 |
| `src/core/multimodal_validator.py` | `MockMultiModalValidator` | 474 |
| `src/core/tenant_manager.py` | `MockTenantManager` | 352 |

That's **9 mock classes** embedded in production modules.

### Demo data in production code

`MockModel` in `main_model.py` contains hardcoded invoice data, Python code examples, and JSON response templates (~90 lines of demo content). This is test fixture data that shouldn't be in the deployed package.

## Impact

- Inflates production package size unnecessarily
- Blurs the line between production and test code
- Makes it unclear whether mocks are meant to be used at runtime (they are — as fallbacks when API keys aren't set, which is a separate design problem)

## Proposed Fix

1. Create `tests/mocks/` directory with:
   - `tests/mocks/__init__.py`
   - `tests/mocks/models.py` — all Mock* classes
   - `tests/mocks/fixtures.py` — demo data (invoices, code examples)

2. In production code, replace inline mock fallbacks with explicit error messages:
   ```python
   # Before (current):
   if not api_key:
       return MockModel()

   # After:
   if not api_key:
       raise ConfigurationError(
           "No API key configured. Set ANTHROPIC_API_KEY or another provider key."
       )
   ```

3. For testing without API keys, use `pytest` fixtures and `conftest.py` to inject mocks.

## Files

- `src/core/main_model.py`
- `src/core/critic_model.py`
- `src/core/judge_model.py`
- `src/core/rule_graph.py`
- `src/core/multimodal_validator.py`
- `src/core/tenant_manager.py`
