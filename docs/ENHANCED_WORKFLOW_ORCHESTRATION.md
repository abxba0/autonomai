# Enhanced Workflow Orchestration Documentation

## Overview

The enhanced Workflow Orchestrator provides advanced capabilities for building sophisticated, production-grade workflows with:

- **Conditional Branching**: if/else and switch/case logic
- **Loop Constructs**: while, for, and foreach iteration
- **Nested Sub-Workflows**: Modular, reusable workflow components
- **Dynamic Modification**: Runtime workflow modification capabilities
- **End-to-End Observability**: Comprehensive logging and execution tracking

## Features

### 1. Conditional Branching

Execute different workflow paths based on runtime conditions.

#### If/Else Branching

```python
from src.models.workflow import WorkflowStep, StepType

conditional_step = WorkflowStep(
    id="quality_check",
    name="Quality Check",
    step_type=StepType.CONDITIONAL,
    condition="data_quality >= 80",  # Python expression
    branches={
        "true": ["high_quality_path"],  # Step IDs to execute if true
        "false": ["low_quality_path"],  # Step IDs to execute if false
    },
    dependencies=["previous_step"],
)
```

#### Features:
- Python expression evaluation in safe environment
- Access to previous step outputs via context
- Automatic skipping of non-taken branches
- Support for complex conditions with nested data

#### Examples:

```python
# Simple comparison
condition="value > 10"

# Checking step outputs
condition="step1['status'] == 'success'"

# Complex logic
condition="(quality >= 80 and count > 100) or force_process == True"

# Nested data access
condition="results['validation']['score'] >= threshold"
```

### 2. Loop Constructs

Process collections or repeat operations with built-in loop constructs.

#### Foreach Loop

Iterate over a collection of items:

```python
foreach_step = WorkflowStep(
    id="process_files",
    name="Process Files",
    step_type=StepType.LOOP,
    loop_type="foreach",
    loop_variable="file",  # Variable name for current item
    loop_collection=["file1.txt", "file2.txt", "file3.txt"],
    max_iterations=100,  # Safety limit
)
```

#### For Loop

Iterate over a numeric range:

```python
for_step = WorkflowStep(
    id="count_loop",
    name="Count Loop",
    step_type=StepType.LOOP,
    loop_type="for",
    loop_variable="i",
    inputs={
        "start": 0,
        "end": 10,
        "step": 1,
    },
    max_iterations=100,
)
```

#### While Loop

Continue while a condition is true:

```python
while_step = WorkflowStep(
    id="wait_ready",
    name="Wait Until Ready",
    step_type=StepType.LOOP,
    loop_type="while",
    condition="status != 'ready'",
    max_iterations=50,  # Prevent infinite loops
)
```

#### Features:
- Safe iteration with `max_iterations` limit
- Loop variable accessible in context
- Iteration tracking and logging
- Support for nested loops via sub-workflows

### 3. Nested Sub-Workflows

Create modular, reusable workflow components.

```python
from src.models.workflow import WorkflowPlan, WorkflowStep, StepType

# Create sub-workflow
sub_step1 = WorkflowStep(id="sub1", name="Subtask 1")
sub_step2 = WorkflowStep(id="sub2", name="Subtask 2", dependencies=["sub1"])

subworkflow = WorkflowPlan(
    name="Data Processing",
    description="Process data subset",
    goal="Process data",
    steps=[sub_step1, sub_step2],
)

# Use in main workflow
subwf_step = WorkflowStep(
    id="process_data",
    name="Process Data Sub-Workflow",
    step_type=StepType.SUBWORKFLOW,
    subworkflow_id=subworkflow.id,
    subworkflow_plan=subworkflow,
    dependencies=["extract_data"],
)
```

#### Features:
- Independent execution context
- Output aggregation from sub-workflow steps
- Support for nested sub-workflows (workflows within workflows)
- Failure propagation and handling

#### Benefits:
- **Modularity**: Reusable workflow components
- **Maintainability**: Easier to test and update
- **Clarity**: Better organization of complex workflows
- **Composition**: Build complex workflows from simple parts

### 4. Dynamic Workflow Modification

Modify workflows at runtime based on conditions or external events.

#### Add Step

```python
from src.core.workflow_orchestrator import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()

# Create and register workflow
workflow = orchestrator.create_workflow_plan("Process data", context)

# Add step dynamically
new_step = WorkflowStep(
    id="validation",
    name="Validate Results",
    description="Validate processed data",
    dependencies=["process"],
)

result = orchestrator.add_step_to_workflow(
    workflow.id,
    new_step,
    after_step_id="process"  # Optional: insert after specific step
)
```

#### Remove Step

```python
# Remove step (must be PENDING status)
result = orchestrator.remove_step_from_workflow(
    workflow.id,
    "optional_step"
)

# Dependencies are automatically updated
```

#### Modify Step

```python
# Update step attributes
updates = {
    "description": "Updated description",
    "inputs": {"new_param": "value"},
    "max_iterations": 200,  # For loop steps
}

result = orchestrator.modify_step_in_workflow(
    workflow.id,
    "step_id",
    updates
)
```

#### Features:
- Safe modification with status checks
- Automatic dependency management
- Execution log tracking
- Validation of modifications

#### Restrictions:
- Cannot remove/modify RUNNING or COMPLETED steps
- Cannot create circular dependencies
- Must maintain workflow integrity

### 5. Observability and Testability

#### Execution Logging

Every workflow and step maintains detailed execution logs:

```python
# Workflow-level logs
workflow.execution_log = [
    {
        "timestamp": "2024-01-16T...",
        "event": "step_added",
        "step_id": "validation",
        "step_name": "Validate Data",
    },
    # ... more events
]

# Step-level logs
step.execution_log = [
    {
        "timestamp": "2024-01-16T...",
        "status": "running",
        "iteration": 1,
    },
    # ... more events
]
```

#### Status Tracking

```python
from src.models.workflow import StepStatus

# Check step status
if step.status == StepStatus.COMPLETED:
    process_outputs(step.outputs)
elif step.status == StepStatus.FAILED:
    handle_error(step.error_message)
elif step.status == StepStatus.SKIPPED:
    # Step was skipped (e.g., conditional branch not taken)
    pass

# Track workflow progress
status = orchestrator.get_workflow_status(workflow.id)
print(f"Progress: {status['completed_steps']}/{status['total_steps']}")
```

#### Testing Support

The architecture supports comprehensive testing:

```python
def test_conditional_workflow():
    config = SystemConfig()
    orchestrator = WorkflowOrchestrator(config)
    
    # Create workflow with conditional
    workflow = create_test_workflow()
    orchestrator.active_workflows[workflow.id] = workflow
    
    # Execute with test context
    context = {"quality_score": 85}
    result = orchestrator.execute_conditional_step(
        workflow.id,
        "quality_check",
        context
    )
    
    # Assert behavior
    assert result["success"]
    assert result["outputs"]["branch_taken"] == "true"
```

## Step Types

### StepType.STANDARD
Regular execution step (default behavior).

### StepType.CONDITIONAL
Branching step with condition evaluation.

### StepType.LOOP
Iteration step (foreach, for, while).

### StepType.SUBWORKFLOW
Nested workflow execution.

## Best Practices

### 1. Design Modular Workflows

```python
# ✓ Good: Modular sub-workflows
payment_workflow = create_payment_workflow()
inventory_workflow = create_inventory_workflow()

main_workflow = WorkflowPlan(
    steps=[
        ...,
        subworkflow_step(payment_workflow),
        subworkflow_step(inventory_workflow),
        ...
    ]
)

# ✗ Avoid: Monolithic workflows with too many steps
# (Break into sub-workflows instead)
```

### 2. Use Descriptive Conditions

```python
# ✓ Good: Clear, descriptive conditions
condition="data_validation['error_count'] == 0"
condition="user_role in ['admin', 'manager']"

# ✗ Avoid: Cryptic conditions
condition="x > 5 and y == z"
```

### 3. Set Reasonable Iteration Limits

```python
# ✓ Good: Conservative limits
foreach_step = WorkflowStep(
    loop_type="foreach",
    loop_collection=items,
    max_iterations=1000,  # Reasonable safety limit
)

# ✗ Avoid: No limit or unreasonably high limits
max_iterations=999999  # Too high
```

### 4. Handle Errors Gracefully

```python
# ✓ Good: Error handling branches
error_check = WorkflowStep(
    step_type=StepType.CONDITIONAL,
    condition="step1['status'] == 'success'",
    branches={
        "true": ["continue_processing"],
        "false": ["error_handler", "cleanup"],
    }
)
```

### 5. Log Important Events

```python
# Dynamic modifications are automatically logged
result = orchestrator.add_step_to_workflow(workflow.id, step)

# Workflow execution log will contain:
# - step_added
# - step_removed
# - step_modified
# - retry_attempt
# - etc.
```

## Examples

See `examples/enhanced_workflow_demo.py` for comprehensive examples including:

1. **Conditional Branching**: Data quality-based processing
2. **Loop Constructs**: Batch file processing
3. **Nested Sub-Workflows**: E-commerce order processing
4. **Dynamic Modification**: Runtime workflow adaptation
5. **Complex Workflows**: ETL pipeline with all features

## Migration Guide

### Upgrading from Basic Workflows

Existing workflows continue to work without changes:

```python
# Old code (still works)
step = WorkflowStep(
    id="process",
    name="Process Data",
    # step_type defaults to STANDARD
)
```

To use new features, simply specify the step type:

```python
# New code (with enhanced features)
conditional_step = WorkflowStep(
    id="check",
    name="Quality Check",
    step_type=StepType.CONDITIONAL,  # Specify type
    condition="quality >= 80",
    branches={"true": [...], "false": [...]},
)
```

### Backward Compatibility

- All existing WorkflowStep instances default to `StepType.STANDARD`
- Existing workflows deserialize correctly
- No breaking changes to existing APIs
- New features are opt-in

## API Reference

### WorkflowOrchestrator Methods

#### Conditional Execution
```python
execute_conditional_step(
    workflow_id: str,
    step_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

#### Loop Execution
```python
execute_loop_step(
    workflow_id: str,
    step_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

#### Subworkflow Execution
```python
execute_subworkflow_step(
    workflow_id: str,
    step_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

#### Dynamic Modification
```python
add_step_to_workflow(
    workflow_id: str,
    step: WorkflowStep,
    after_step_id: Optional[str] = None
) -> Dict[str, Any]

remove_step_from_workflow(
    workflow_id: str,
    step_id: str
) -> Dict[str, Any]

modify_step_in_workflow(
    workflow_id: str,
    step_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]
```

### WorkflowPlan Methods

```python
insert_step(
    step: WorkflowStep,
    after_step_id: Optional[str] = None
) -> bool

remove_step(step_id: str) -> bool

update_step(step_id: str, updates: Dict[str, Any]) -> bool
```

## Testing

Run the test suite:

```bash
# Test enhanced features
python tests/test_workflow_enhanced.py

# Test backward compatibility
python tests/test_workflow.py

# Run all tests
pytest tests/test_workflow*.py
```

## Performance Considerations

- **Loop Limits**: Always set `max_iterations` to prevent runaway loops
- **Sub-Workflows**: Consider memory usage with deeply nested workflows
- **Conditions**: Keep condition expressions simple for faster evaluation
- **Context Size**: Large contexts can slow down condition evaluation

## Security

- **Condition Evaluation**: Uses restricted `eval()` with limited builtins
- **No File Access**: Conditions cannot access filesystem
- **No Network**: Conditions cannot make network calls
- **Safe Builtins**: Only safe operations allowed in conditions

## Troubleshooting

### Condition Not Evaluating Correctly

```python
# Debug condition evaluation
result = orchestrator._evaluate_condition(condition, context)
print(f"Condition '{condition}' evaluated to: {result}")
```

### Loop Not Terminating

Check `max_iterations` and condition logic:

```python
while_step.max_iterations = 10  # Reduce for testing
```

### Subworkflow Failing

Check subworkflow step statuses:

```python
for step in subworkflow.steps:
    if step.status == StepStatus.FAILED:
        print(f"Failed: {step.name} - {step.error_message}")
```

## Support

For issues, feature requests, or questions:
- See examples in `examples/enhanced_workflow_demo.py`
- Run tests in `tests/test_workflow_enhanced.py`
- Check existing issues in the repository

## Future Enhancements

Potential future additions:
- Parallel step execution
- Workflow templates and presets
- Advanced error recovery strategies
- Workflow visualization
- Performance optimization for large workflows
