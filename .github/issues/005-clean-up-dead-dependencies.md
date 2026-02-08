# CLEANUP: Remove unused dependencies from requirements

**Labels:** `tech-debt`, `cleanup`, `priority-3`

## Summary

Several packages listed in `requirements/base.txt` are either unused or only used indirectly through LangChain wrappers. This bloats install time, increases attack surface, and confuses contributors.

### Confirmed unused (0 direct imports in `src/`)

| Package | Listed In | Status |
|---------|-----------|--------|
| `tiktoken` | requirements | **Never imported anywhere** in source code |
| `anthropic` | requirements | Not directly imported — LangChain wraps it |
| `openai` | requirements | Not directly imported — LangChain wraps it |
| `langchain-anthropic` | requirements | Only used transitively |
| `langchain-openai` | requirements | Only used transitively |

### Underutilized

| Package | Listed In | Actual Usage |
|---------|-----------|-------------|
| `langchain` | requirements | Only 4 files out of 56 import it |
| `redis` | requirements | Only 3 files use it |
| `celery` | requirements | Only 4 files use it |

### Structure issue

`requirements.txt` just references `requirements/base.txt`. This indirection adds no value for a single base file — flatten it or properly split into `base.txt`, `dev.txt`, `prod.txt`.

## Proposed Fix

1. **Audit imports** — run `pipreqs src/ --print` to generate actual requirements from imports
2. **Remove packages** that are only transitive dependencies (let LangChain pull them in via its own deps)
3. **Pin versions properly** — current pins use `>=` minimum only, which allows breaking upgrades
4. **Flatten or restructure** the requirements directory:
   ```
   requirements/
   ├── base.txt       # Core runtime deps only
   ├── dev.txt        # pytest, black, mypy, etc.
   ├── web.txt        # FastAPI, uvicorn, JWT
   └── distributed.txt # Redis, Celery
   ```

## Files

- `requirements.txt`
- `requirements/base.txt`
- `setup.py` or `pyproject.toml` (extras_require)
