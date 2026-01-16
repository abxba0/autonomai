"""
Tests for Enhanced Workflow Orchestrator Features

Tests conditional branching, loops, subworkflows, and dynamic modifications
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src directory to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.workflow import (
    WorkflowPlan,
    WorkflowStep,
    StepStatus,
    StepType,
)
from src.models.config import SystemConfig
from src.core.workflow_orchestrator import WorkflowOrchestrator


def test_step_type_enum():
    """Test StepType enum"""
    print("Testing StepType enum...")
    
    assert StepType.STANDARD.value == "standard"
    assert StepType.CONDITIONAL.value == "conditional"
    assert StepType.LOOP.value == "loop"
    assert StepType.SUBWORKFLOW.value == "subworkflow"
    
    print("✓ StepType enum values correct")
    return True


def test_conditional_step_creation():
    """Test creating conditional steps"""
    print("\nTesting conditional step creation...")
    
    # Test if/else conditional
    cond_step = WorkflowStep(
        id="cond_1",
        name="Check Status",
        description="Check if value > 10",
        step_type=StepType.CONDITIONAL,
        condition="value > 10",
        branches={
            "true": ["step_2", "step_3"],
            "false": ["step_4"],
        },
    )
    
    assert cond_step.step_type == StepType.CONDITIONAL
    assert cond_step.condition == "value > 10"
    assert len(cond_step.branches) == 2
    assert "true" in cond_step.branches
    assert "false" in cond_step.branches
    
    print("✓ Conditional step created successfully")
    
    # Test serialization
    cond_dict = cond_step.to_dict()
    assert cond_dict["step_type"] == "conditional"
    assert cond_dict["condition"] == "value > 10"
    assert "branches" in cond_dict
    
    print("✓ Conditional step serialization")
    
    # Test deserialization
    cond_step2 = WorkflowStep.from_dict(cond_dict)
    assert cond_step2.step_type == StepType.CONDITIONAL
    assert cond_step2.condition == cond_step.condition
    assert cond_step2.branches == cond_step.branches
    
    print("✓ Conditional step deserialization")
    
    return True


def test_loop_step_creation():
    """Test creating loop steps"""
    print("\nTesting loop step creation...")
    
    # Test foreach loop
    foreach_step = WorkflowStep(
        id="loop_1",
        name="Process Items",
        description="Process each item in collection",
        step_type=StepType.LOOP,
        loop_type="foreach",
        loop_variable="item",
        loop_collection=["a", "b", "c"],
        max_iterations=10,
    )
    
    assert foreach_step.step_type == StepType.LOOP
    assert foreach_step.loop_type == "foreach"
    assert foreach_step.loop_variable == "item"
    assert len(foreach_step.loop_collection) == 3
    
    print("✓ Foreach loop step created")
    
    # Test while loop
    while_step = WorkflowStep(
        id="loop_2",
        name="Wait Until Ready",
        description="Wait until condition is met",
        step_type=StepType.LOOP,
        loop_type="while",
        condition="ready == False",
        max_iterations=5,
    )
    
    assert while_step.step_type == StepType.LOOP
    assert while_step.loop_type == "while"
    assert while_step.condition == "ready == False"
    
    print("✓ While loop step created")
    
    # Test for loop
    for_step = WorkflowStep(
        id="loop_3",
        name="Count to Ten",
        description="Count from 0 to 10",
        step_type=StepType.LOOP,
        loop_type="for",
        loop_variable="i",
        inputs={"start": 0, "end": 10, "step": 1},
        max_iterations=10,
    )
    
    assert for_step.step_type == StepType.LOOP
    assert for_step.loop_type == "for"
    assert for_step.loop_variable == "i"
    
    print("✓ For loop step created")
    
    # Test serialization
    loop_dict = foreach_step.to_dict()
    assert loop_dict["step_type"] == "loop"
    assert loop_dict["loop_type"] == "foreach"
    assert "loop_variable" in loop_dict
    assert "loop_collection" in loop_dict
    
    print("✓ Loop step serialization")
    
    return True


def test_subworkflow_step_creation():
    """Test creating subworkflow steps"""
    print("\nTesting subworkflow step creation...")
    
    # Create a subworkflow plan
    sub_step1 = WorkflowStep(
        id="sub_1",
        name="Sub Task 1",
        description="First subtask",
    )
    sub_step2 = WorkflowStep(
        id="sub_2",
        name="Sub Task 2",
        description="Second subtask",
        dependencies=["sub_1"],
    )
    
    subworkflow = WorkflowPlan(
        name="Subworkflow",
        description="A nested workflow",
        goal="Complete subtasks",
        steps=[sub_step1, sub_step2],
    )
    
    # Create subworkflow step
    subwf_step = WorkflowStep(
        id="subwf_1",
        name="Execute Subworkflow",
        description="Run nested workflow",
        step_type=StepType.SUBWORKFLOW,
        subworkflow_id=subworkflow.id,
        subworkflow_plan=subworkflow,
    )
    
    assert subwf_step.step_type == StepType.SUBWORKFLOW
    assert subwf_step.subworkflow_id == subworkflow.id
    assert subwf_step.subworkflow_plan is not None
    assert len(subwf_step.subworkflow_plan.steps) == 2
    
    print("✓ Subworkflow step created")
    
    # Test serialization
    subwf_dict = subwf_step.to_dict()
    assert subwf_dict["step_type"] == "subworkflow"
    assert "subworkflow_id" in subwf_dict
    assert "subworkflow_plan" in subwf_dict
    
    print("✓ Subworkflow step serialization")
    
    # Test deserialization
    subwf_step2 = WorkflowStep.from_dict(subwf_dict)
    assert subwf_step2.step_type == StepType.SUBWORKFLOW
    assert subwf_step2.subworkflow_plan is not None
    assert len(subwf_step2.subworkflow_plan.steps) == 2
    
    print("✓ Subworkflow step deserialization")
    
    return True


def test_dynamic_workflow_modification():
    """Test dynamic workflow modification operations"""
    print("\nTesting dynamic workflow modification...")
    
    # Create initial workflow
    step1 = WorkflowStep(id="s1", name="Step 1")
    step2 = WorkflowStep(id="s2", name="Step 2", dependencies=["s1"])
    
    plan = WorkflowPlan(
        name="Dynamic Workflow",
        description="Test dynamic modifications",
        goal="Test",
        steps=[step1, step2],
    )
    
    assert len(plan.steps) == 2
    
    # Test inserting a step
    step3 = WorkflowStep(id="s3", name="Step 3")
    success = plan.insert_step(step3, after_step_id="s1")
    
    assert success
    assert len(plan.steps) == 3
    assert plan.steps[1].id == "s3"
    
    print("✓ Step insertion")
    
    # Test appending a step
    step4 = WorkflowStep(id="s4", name="Step 4")
    success = plan.insert_step(step4)
    
    assert success
    assert len(plan.steps) == 4
    assert plan.steps[-1].id == "s4"
    
    print("✓ Step appending")
    
    # Test removing a step
    success = plan.remove_step("s3")
    
    assert success
    assert len(plan.steps) == 3
    assert plan.get_step_by_id("s3") is None
    
    print("✓ Step removal")
    
    # Test updating a step
    success = plan.update_step("s1", {"description": "Updated description"})
    
    assert success
    assert plan.get_step_by_id("s1").description == "Updated description"
    
    print("✓ Step update")
    
    return True


def test_conditional_execution():
    """Test conditional step execution"""
    print("\nTesting conditional step execution...")
    
    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create instruction files
        (instructions_dir / "planner.md").write_text("# Planner")
        (instructions_dir / "actor.md").write_text("# Actor")
        (instructions_dir / "instructions.md").write_text("# Instructions")
        
        config = SystemConfig(instructions_dir=instructions_dir)
        orchestrator = WorkflowOrchestrator(config)
        
        # Create workflow with conditional
        step1 = WorkflowStep(
            id="s1",
            name="Setup",
            description="Setup test",
            status=StepStatus.COMPLETED,
            outputs={"value": 15},
        )
        
        cond_step = WorkflowStep(
            id="cond",
            name="Check Value",
            description="Branch based on value",
            step_type=StepType.CONDITIONAL,
            condition="s1['value'] > 10",
            branches={
                "true": ["s2"],
                "false": ["s3"],
            },
            dependencies=["s1"],
        )
        
        step2 = WorkflowStep(id="s2", name="High Value", dependencies=["cond"])
        step3 = WorkflowStep(id="s3", name="Low Value", dependencies=["cond"])
        
        plan = WorkflowPlan(
            name="Conditional Test",
            description="Test conditional branching",
            goal="Test",
            steps=[step1, cond_step, step2, step3],
        )
        
        orchestrator.active_workflows[plan.id] = plan
        
        # Execute conditional with context
        context = {"s1": {"value": 15}}
        result = orchestrator.execute_conditional_step(plan.id, "cond", context)
        
        assert result["success"]
        assert result["outputs"]["condition_result"] == True
        assert result["outputs"]["branch_taken"] == "true"
        
        # Check that false branch was skipped
        assert plan.get_step_by_id("s3").status == StepStatus.SKIPPED
        
        print("✓ Conditional execution (true branch)")
        
        # Test false condition
        cond_step2 = WorkflowStep(
            id="cond2",
            name="Check Value 2",
            step_type=StepType.CONDITIONAL,
            condition="s1['value'] < 10",
            branches={
                "true": ["s4"],
                "false": ["s5"],
            },
        )
        
        step4 = WorkflowStep(id="s4", name="Branch A")
        step5 = WorkflowStep(id="s5", name="Branch B")
        
        plan.steps.extend([cond_step2, step4, step5])
        
        result = orchestrator.execute_conditional_step(plan.id, "cond2", context)
        
        assert result["success"]
        assert result["outputs"]["condition_result"] == False
        assert result["outputs"]["branch_taken"] == "false"
        
        print("✓ Conditional execution (false branch)")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_loop_execution():
    """Test loop step execution"""
    print("\nTesting loop step execution...")
    
    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create instruction files
        (instructions_dir / "planner.md").write_text("# Planner")
        (instructions_dir / "actor.md").write_text("# Actor")
        (instructions_dir / "instructions.md").write_text("# Instructions")
        
        config = SystemConfig(instructions_dir=instructions_dir)
        orchestrator = WorkflowOrchestrator(config)
        
        # Test foreach loop
        foreach_step = WorkflowStep(
            id="loop1",
            name="Process Items",
            step_type=StepType.LOOP,
            loop_type="foreach",
            loop_variable="item",
            loop_collection=[1, 2, 3, 4, 5],
            max_iterations=10,
        )
        
        plan = WorkflowPlan(
            name="Loop Test",
            description="Test loop execution",
            goal="Test",
            steps=[foreach_step],
        )
        
        orchestrator.active_workflows[plan.id] = plan
        
        result = orchestrator.execute_loop_step(plan.id, "loop1")
        
        assert result["success"]
        assert result["outputs"]["iterations_performed"] == 5
        assert result["outputs"]["loop_type"] == "foreach"
        assert foreach_step.status == StepStatus.COMPLETED
        
        print("✓ Foreach loop execution")
        
        # Test for loop
        for_step = WorkflowStep(
            id="loop2",
            name="Count",
            step_type=StepType.LOOP,
            loop_type="for",
            loop_variable="i",
            inputs={"start": 0, "end": 5, "step": 1},
            max_iterations=10,
        )
        
        plan.steps.append(for_step)
        
        result = orchestrator.execute_loop_step(plan.id, "loop2")
        
        assert result["success"]
        assert result["outputs"]["iterations_performed"] == 5
        assert result["outputs"]["loop_type"] == "for"
        
        print("✓ For loop execution")
        
        # Test while loop with max iterations
        while_step = WorkflowStep(
            id="loop3",
            name="While Test",
            step_type=StepType.LOOP,
            loop_type="while",
            condition="True",  # Would be infinite without max_iterations
            max_iterations=3,
        )
        
        plan.steps.append(while_step)
        
        result = orchestrator.execute_loop_step(plan.id, "loop3")
        
        assert result["success"]
        assert result["outputs"]["iterations_performed"] == 3
        assert while_step.iteration_count == 3
        
        print("✓ While loop with max iterations")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_subworkflow_execution():
    """Test subworkflow step execution"""
    print("\nTesting subworkflow step execution...")
    
    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create instruction files
        (instructions_dir / "planner.md").write_text("# Planner")
        (instructions_dir / "actor.md").write_text("# Actor")
        (instructions_dir / "instructions.md").write_text("# Instructions")
        
        config = SystemConfig(instructions_dir=instructions_dir)
        orchestrator = WorkflowOrchestrator(config)
        
        # Create subworkflow with pre-completed steps (for testing)
        sub_step1 = WorkflowStep(
            id="sub1",
            name="Subtask 1",
            status=StepStatus.COMPLETED,
            outputs={"result": "sub1 done"},
        )
        sub_step2 = WorkflowStep(
            id="sub2",
            name="Subtask 2",
            status=StepStatus.COMPLETED,
            outputs={"result": "sub2 done"},
            dependencies=["sub1"],
        )
        
        subworkflow = WorkflowPlan(
            name="Subworkflow",
            description="Nested workflow",
            goal="Complete subtasks",
            steps=[sub_step1, sub_step2],
        )
        
        # Create main workflow with subworkflow step
        subwf_step = WorkflowStep(
            id="subwf",
            name="Execute Subworkflow",
            step_type=StepType.SUBWORKFLOW,
            subworkflow_id=subworkflow.id,
            subworkflow_plan=subworkflow,
        )
        
        plan = WorkflowPlan(
            name="Main Workflow",
            description="Workflow with subworkflow",
            goal="Test",
            steps=[subwf_step],
        )
        
        orchestrator.active_workflows[plan.id] = plan
        
        result = orchestrator.execute_subworkflow_step(plan.id, "subwf")
        
        assert result["success"]
        assert subwf_step.status == StepStatus.COMPLETED
        assert "subworkflow_outputs" in result["outputs"]
        assert len(result["outputs"]["subworkflow_outputs"]) == 2
        
        print("✓ Subworkflow execution")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_orchestrator_dynamic_modification():
    """Test orchestrator's dynamic modification methods"""
    print("\nTesting orchestrator dynamic modification methods...")
    
    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create instruction files
        (instructions_dir / "planner.md").write_text("# Planner")
        (instructions_dir / "actor.md").write_text("# Actor")
        (instructions_dir / "instructions.md").write_text("# Instructions")
        
        config = SystemConfig(instructions_dir=instructions_dir)
        orchestrator = WorkflowOrchestrator(config)
        
        # Create workflow
        step1 = WorkflowStep(id="s1", name="Step 1")
        step2 = WorkflowStep(id="s2", name="Step 2", dependencies=["s1"])
        
        plan = WorkflowPlan(
            name="Test Workflow",
            description="Test",
            goal="Test",
            steps=[step1, step2],
        )
        
        orchestrator.active_workflows[plan.id] = plan
        
        # Test adding a step
        step3 = WorkflowStep(id="s3", name="Step 3")
        result = orchestrator.add_step_to_workflow(plan.id, step3, after_step_id="s1")
        
        assert result["success"]
        assert len(plan.steps) == 3
        
        print("✓ Add step via orchestrator")
        
        # Test modifying a step
        result = orchestrator.modify_step_in_workflow(
            plan.id, "s3", {"description": "New description"}
        )
        
        assert result["success"]
        assert plan.get_step_by_id("s3").description == "New description"
        
        print("✓ Modify step via orchestrator")
        
        # Test removing a step
        result = orchestrator.remove_step_from_workflow(plan.id, "s3")
        
        assert result["success"]
        assert len(plan.steps) == 2
        assert plan.get_step_by_id("s3") is None
        
        print("✓ Remove step via orchestrator")
        
        # Test that we can't remove a completed step
        step1.status = StepStatus.COMPLETED
        result = orchestrator.remove_step_from_workflow(plan.id, "s1")
        
        assert not result["success"]
        assert "Cannot remove" in result["error"]
        
        print("✓ Protection against removing completed steps")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_backward_compatibility():
    """Test that existing workflows still work"""
    print("\nTesting backward compatibility...")
    
    # Create old-style step (without step_type)
    step_dict = {
        "id": "old_step",
        "name": "Old Step",
        "description": "Legacy step",
        "dependencies": [],
        "status": "pending",
        "inputs": {},
        "outputs": {},
    }
    
    # Should default to STANDARD type
    step = WorkflowStep.from_dict(step_dict)
    
    assert step.step_type == StepType.STANDARD
    assert step.id == "old_step"
    assert step.name == "Old Step"
    
    print("✓ Old-style steps default to STANDARD type")
    
    # Test old-style workflow
    plan_dict = {
        "id": "old_plan",
        "name": "Old Workflow",
        "description": "Legacy workflow",
        "goal": "Test",
        "steps": [step_dict],
    }
    
    plan = WorkflowPlan.from_dict(plan_dict)
    
    assert len(plan.steps) == 1
    assert plan.steps[0].step_type == StepType.STANDARD
    
    print("✓ Old-style workflows still work")
    
    return True


def test_condition_evaluation():
    """Test condition evaluation safety"""
    print("\nTesting condition evaluation...")
    
    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        (instructions_dir / "planner.md").write_text("# Planner")
        (instructions_dir / "actor.md").write_text("# Actor")
        (instructions_dir / "instructions.md").write_text("# Instructions")
        
        config = SystemConfig(instructions_dir=instructions_dir)
        orchestrator = WorkflowOrchestrator(config)
        
        # Test simple conditions
        context = {"x": 10, "y": 5}
        
        assert orchestrator._evaluate_condition("x > y", context) == True
        assert orchestrator._evaluate_condition("x < y", context) == False
        assert orchestrator._evaluate_condition("x == 10", context) == True
        assert orchestrator._evaluate_condition("y != 10", context) == True
        
        print("✓ Basic condition evaluation")
        
        # Test with step outputs
        context = {
            "step1": {"value": 15, "status": "ok"},
            "step2": {"count": 3},
        }
        
        assert orchestrator._evaluate_condition("step1['value'] > 10", context) == True
        assert orchestrator._evaluate_condition("step2['count'] == 3", context) == True
        
        print("✓ Condition evaluation with nested data")
        
        # Test invalid condition (should return False safely)
        result = orchestrator._evaluate_condition("invalid python code $$", context)
        assert result == False
        
        print("✓ Invalid conditions handled safely")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def run_all_tests():
    """Run all enhanced workflow tests"""
    print("=" * 70)
    print("Running Enhanced Workflow Orchestrator Tests")
    print("=" * 70)
    
    tests = [
        ("StepType Enum", test_step_type_enum),
        ("Conditional Step Creation", test_conditional_step_creation),
        ("Loop Step Creation", test_loop_step_creation),
        ("Subworkflow Step Creation", test_subworkflow_step_creation),
        ("Dynamic Workflow Modification", test_dynamic_workflow_modification),
        ("Conditional Execution", test_conditional_execution),
        ("Loop Execution", test_loop_execution),
        ("Subworkflow Execution", test_subworkflow_execution),
        ("Orchestrator Dynamic Modification", test_orchestrator_dynamic_modification),
        ("Backward Compatibility", test_backward_compatibility),
        ("Condition Evaluation", test_condition_evaluation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n✓ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
