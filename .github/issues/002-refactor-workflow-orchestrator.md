# REFACTOR: Break up WorkflowOrchestrator God Object (1506 lines, 41 methods)

**Labels:** `refactor`, `tech-debt`, `priority-2`

## Summary

`src/core/workflow_orchestrator.py` is a 1506-line single-class file with 41 methods that handles at least 6 distinct responsibilities:

1. **Workflow planning** — generating execution plans from LLM
2. **Step execution** — running individual workflow steps
3. **Conditional logic** — evaluating if/else branching
4. **Loop execution** — for/foreach loop handling
5. **Subworkflow orchestration** — nested workflow delegation
6. **Instruction management** — a `WorkflowInstructionManager` embedded inside the same file
7. **Optimization** — critic-based step optimization

Multiple methods exceed 100 lines:
- `execute_step`: 139 lines
- `execute_workflow`: 114 lines
- `execute_subworkflow_step`: 110 lines
- `execute_loop_step`: 107 lines

## Specific Problems

### Thread-unsafe instruction swapping
The `_swap_instructions_temporarily` method directly mutates shared state:
```python
self.base_instruction_manager.base_instructions = new_instructions  # Direct mutation!
```
This will corrupt state under concurrent execution.

### Duplicated model creation
`_create_planner_version` and `_create_actor_version` are near-identical methods that should be one parameterized function.

### Naive JSON parsing
LLM response parsing (around line 360) uses string splitting to extract JSON. This will fail on any response with nested JSON or markdown code fences.

### Magic constants
`WORKFLOW_SAFETY_BUFFER = 10` (line 204) is undocumented.

## Proposed Refactor

Split into 5-6 focused classes:

```
src/core/workflow/
├── __init__.py              # Public API re-exports
├── orchestrator.py          # Top-level coordination only (~200 lines)
├── planner.py               # Plan generation from LLM
├── executor.py              # Step execution dispatch
├── control_flow.py          # Conditionals, loops, subworkflows
├── instruction_manager.py   # Workflow-specific instruction management
└── optimizer.py             # Critic-based optimization
```

Each class should be <300 lines. The orchestrator delegates to specialized components via dependency injection.

## Files

- `src/core/workflow_orchestrator.py` (all 1506 lines)
