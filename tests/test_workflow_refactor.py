"""
Tests for Refactored Workflow Package

Tests the modular subcomponents of the workflow orchestration system:
- WorkflowInstructionManager
- WorkflowPlanner
- WorkflowExecutor
- ControlFlowEngine
- StepOptimizer
- WorkflowOrchestrator (integration)
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
    FailureSource,
)
from src.models.config import SystemConfig


def test_instruction_manager_standalone():
    """Test WorkflowInstructionManager from the new package"""
    print("Testing WorkflowInstructionManager from new package...")

    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)

    try:
        (instructions_dir / "planner.md").write_text("# Planner\n\nPlan steps")
        (instructions_dir / "actor.md").write_text("# Actor\n\nExecute steps")

        config = SystemConfig(instructions_dir=instructions_dir)

        from src.core.workflow.instruction_manager import WorkflowInstructionManager

        manager = WorkflowInstructionManager(config, instructions_dir)

        # Test reading
        assert "Planner" in manager.get_planner_instructions()
        assert "Actor" in manager.get_actor_instructions()
        print("✓ Reading instructions from new package")

        # Test versioning
        assert manager.current_planner_version is not None
        assert manager.current_actor_version is not None
        print("✓ Version tracking")

        # Test updating
        new_content = manager.get_planner_instructions() + "\n\nNew rule added"
        version = manager.update_planner_instructions(
            new_content, "test", "Added new rule"
        )
        assert version is not None
        assert "New rule added" in manager.get_planner_instructions()
        print("✓ Updating planner instructions")

        # Test actor update
        new_actor = manager.get_actor_instructions() + "\n\nActor update"
        version = manager.update_actor_instructions(
            new_actor, "test", "Updated actor"
        )
        assert version is not None
        assert "Actor update" in manager.get_actor_instructions()
        print("✓ Updating actor instructions")

        return True
    finally:
        shutil.rmtree(temp_dir)


def test_swap_instructions_helper():
    """Test swap_instructions_temporarily helper function"""
    print("\nTesting swap_instructions_temporarily helper...")

    from src.core.workflow.instruction_manager import swap_instructions_temporarily

    # Use a simple mock to test the swap logic precisely
    class MockInstructionManager:
        def __init__(self):
            self.base_instructions = "Base content here"
            self.dynamic_appendix = ""

        def get_full_instructions(self):
            if self.dynamic_appendix:
                return self.base_instructions + "\n\n" + self.dynamic_appendix
            return self.base_instructions

    # Test basic swap without dynamic appendix
    mgr = MockInstructionManager()
    original_base = mgr.base_instructions

    def callback():
        return mgr.base_instructions

    result = swap_instructions_temporarily(mgr, "Temporary instructions", callback)
    assert result == "Temporary instructions"
    assert mgr.base_instructions == original_base
    assert mgr.dynamic_appendix == ""
    print("✓ Basic swap and restore (no appendix)")

    # Test swap with dynamic appendix
    mgr2 = MockInstructionManager()
    mgr2.base_instructions = "Base content"
    mgr2.dynamic_appendix = "# Dynamic Appendix\nExtra rules"

    def callback2():
        # During swap, should see temporary instructions with no appendix
        assert mgr2.base_instructions == "Temp"
        assert mgr2.dynamic_appendix == ""
        return "ok"

    swap_instructions_temporarily(mgr2, "Temp", callback2)
    assert mgr2.base_instructions == "Base content"
    assert "# Dynamic Appendix" in mgr2.dynamic_appendix
    print("✓ Dynamic appendix preserved through swap")

    return True


def test_control_flow_engine_conditions():
    """Test ControlFlowEngine condition evaluation"""
    print("\nTesting ControlFlowEngine condition evaluation...")

    from src.core.workflow.control_flow import ControlFlowEngine

    active_workflows = {}
    engine = ControlFlowEngine(active_workflows, lambda *a: None)

    # Basic conditions
    ctx = {"x": 10, "y": 5}
    assert engine._evaluate_condition("x > y", ctx) is True
    assert engine._evaluate_condition("x < y", ctx) is False
    assert engine._evaluate_condition("x == 10", ctx) is True
    print("✓ Basic condition evaluation")

    # Nested data
    ctx2 = {"step1": {"value": 15}}
    assert engine._evaluate_condition("step1['value'] > 10", ctx2) is True
    assert engine._evaluate_condition("step1['value'] < 10", ctx2) is False
    print("✓ Nested data condition evaluation")

    # Invalid condition returns False
    assert engine._evaluate_condition("invalid syntax $$", {}) is False
    print("✓ Invalid condition handled safely")

    # Boolean literals
    assert engine._evaluate_condition("True", {}) is True
    assert engine._evaluate_condition("False", {}) is False
    assert engine._evaluate_condition("true", {}) is True
    assert engine._evaluate_condition("false", {}) is False
    print("✓ Boolean literal evaluation")

    return True


def test_control_flow_conditional_step():
    """Test ControlFlowEngine conditional step execution"""
    print("\nTesting ControlFlowEngine conditional step...")

    from src.core.workflow.control_flow import ControlFlowEngine

    active_workflows = {}
    engine = ControlFlowEngine(active_workflows, lambda *a: None)

    # Create workflow with conditional
    step1 = WorkflowStep(
        id="s1", name="Setup",
        status=StepStatus.COMPLETED,
        outputs={"value": 15},
    )
    cond_step = WorkflowStep(
        id="cond", name="Check",
        step_type=StepType.CONDITIONAL,
        condition="value > 10",
        branches={"true": ["s2"], "false": ["s3"]},
    )
    step2 = WorkflowStep(id="s2", name="High")
    step3 = WorkflowStep(id="s3", name="Low")

    plan = WorkflowPlan(
        name="Test", description="", goal="Test",
        steps=[step1, cond_step, step2, step3],
    )
    active_workflows[plan.id] = plan

    result = engine.execute_conditional_step(plan.id, "cond", {"value": 15})
    assert result["success"]
    assert result["outputs"]["condition_result"] is True
    assert result["outputs"]["branch_taken"] == "true"
    assert step3.status == StepStatus.SKIPPED
    print("✓ Conditional step true branch")

    return True


def test_control_flow_loop_step():
    """Test ControlFlowEngine loop step execution"""
    print("\nTesting ControlFlowEngine loop step...")

    from src.core.workflow.control_flow import ControlFlowEngine

    active_workflows = {}
    engine = ControlFlowEngine(active_workflows, lambda *a: None)

    # foreach loop
    foreach_step = WorkflowStep(
        id="loop1", name="Process",
        step_type=StepType.LOOP,
        loop_type="foreach",
        loop_variable="item",
        loop_collection=["a", "b", "c"],
        max_iterations=10,
    )

    plan = WorkflowPlan(
        name="Loop Test", description="", goal="Test",
        steps=[foreach_step],
    )
    active_workflows[plan.id] = plan

    result = engine.execute_loop_step(plan.id, "loop1")
    assert result["success"]
    assert result["outputs"]["iterations_performed"] == 3
    assert result["outputs"]["loop_type"] == "foreach"
    print("✓ Foreach loop execution")

    # for loop
    for_step = WorkflowStep(
        id="loop2", name="Count",
        step_type=StepType.LOOP,
        loop_type="for",
        loop_variable="i",
        inputs={"start": 0, "end": 5, "step": 1},
        max_iterations=10,
    )
    plan.steps.append(for_step)

    result = engine.execute_loop_step(plan.id, "loop2")
    assert result["success"]
    assert result["outputs"]["iterations_performed"] == 5
    print("✓ For loop execution")

    # while loop with max iterations
    while_step = WorkflowStep(
        id="loop3", name="While",
        step_type=StepType.LOOP,
        loop_type="while",
        condition="True",
        max_iterations=3,
    )
    plan.steps.append(while_step)

    result = engine.execute_loop_step(plan.id, "loop3")
    assert result["success"]
    assert result["outputs"]["iterations_performed"] == 3
    print("✓ While loop with max iterations")

    return True


def test_control_flow_subworkflow():
    """Test ControlFlowEngine subworkflow execution"""
    print("\nTesting ControlFlowEngine subworkflow step...")

    from src.core.workflow.control_flow import ControlFlowEngine

    active_workflows = {}

    def mock_execute(wf_id, step_id, ctx):
        wf = active_workflows.get(wf_id)
        step = wf.get_step_by_id(step_id) if wf else None
        if step:
            step.status = StepStatus.COMPLETED
            step.outputs = {"result": "done"}
        return {"success": True, "step_id": step_id}

    engine = ControlFlowEngine(active_workflows, mock_execute)

    sub_step1 = WorkflowStep(
        id="sub1", name="Subtask 1",
        status=StepStatus.COMPLETED,
        outputs={"result": "sub1 done"},
    )
    sub_step2 = WorkflowStep(
        id="sub2", name="Subtask 2",
        status=StepStatus.COMPLETED,
        outputs={"result": "sub2 done"},
        dependencies=["sub1"],
    )

    subworkflow = WorkflowPlan(
        name="Sub", description="", goal="Subtasks",
        steps=[sub_step1, sub_step2],
    )

    subwf_step = WorkflowStep(
        id="subwf", name="Run Sub",
        step_type=StepType.SUBWORKFLOW,
        subworkflow_id=subworkflow.id,
        subworkflow_plan=subworkflow,
    )

    plan = WorkflowPlan(
        name="Main", description="", goal="Test",
        steps=[subwf_step],
    )
    active_workflows[plan.id] = plan

    result = engine.execute_subworkflow_step(plan.id, "subwf")
    assert result["success"]
    assert subwf_step.status == StepStatus.COMPLETED
    assert "subworkflow_outputs" in result["outputs"]
    print("✓ Subworkflow execution")

    return True


def test_control_flow_error_handling():
    """Test ControlFlowEngine error handling for missing workflows/steps"""
    print("\nTesting ControlFlowEngine error handling...")

    from src.core.workflow.control_flow import ControlFlowEngine

    active_workflows = {}
    engine = ControlFlowEngine(active_workflows, lambda *a: None)

    # Missing workflow
    result = engine.execute_conditional_step("nonexistent", "s1")
    assert not result["success"]
    assert "not found" in result["error"]
    print("✓ Missing workflow handled")

    # Missing step
    plan = WorkflowPlan(
        name="Test", description="", goal="Test", steps=[]
    )
    active_workflows[plan.id] = plan
    result = engine.execute_loop_step(plan.id, "nonexistent")
    assert not result["success"]
    assert "not found" in result["error"]
    print("✓ Missing step handled")

    # Missing subworkflow plan
    step = WorkflowStep(
        id="sub", name="Sub",
        step_type=StepType.SUBWORKFLOW,
    )
    plan.steps.append(step)
    result = engine.execute_subworkflow_step(plan.id, "sub")
    assert not result["success"]
    assert "No subworkflow plan" in result["error"]
    print("✓ Missing subworkflow plan handled")

    return True


def test_optimizer_failure_source_detection():
    """Test StepOptimizer failure source detection"""
    print("\nTesting StepOptimizer failure source detection...")

    from src.core.workflow.optimizer import StepOptimizer

    # Create a mock critic
    class MockCritic:
        def optimize(self, entry):
            return {"success": False}

    optimizer = StepOptimizer(
        critic_model=MockCritic(),
        workflow_instruction_manager=None,
    )

    plan = WorkflowPlan(
        name="Test", description="", goal="Test",
        steps=[WorkflowStep(id="s1", name="Step 1")],
    )

    # Planning failure indicators
    step_planning = WorkflowStep(id="t1", name="Test")
    step_planning.error_message = "missing dependency for step"
    assert optimizer._determine_failure_source(plan, step_planning) == FailureSource.PLANNING
    print("✓ Planning failure detected: dependency")

    step_planning2 = WorkflowStep(id="t2", name="Test")
    step_planning2.error_message = "precondition not met"
    assert optimizer._determine_failure_source(plan, step_planning2) == FailureSource.PLANNING
    print("✓ Planning failure detected: precondition")

    # Execution failure (default)
    step_exec = WorkflowStep(id="t3", name="Test")
    step_exec.error_message = "runtime error occurred"
    assert optimizer._determine_failure_source(plan, step_exec) == FailureSource.EXECUTION
    print("✓ Execution failure detected: runtime error")

    # Empty error message defaults to execution
    step_empty = WorkflowStep(id="t4", name="Test")
    step_empty.error_message = ""
    assert optimizer._determine_failure_source(plan, step_empty) == FailureSource.EXECUTION
    print("✓ Empty error defaults to execution failure")

    return True


def test_backward_compatibility_imports():
    """Test backward compatibility of imports"""
    print("\nTesting backward compatibility imports...")

    # Old import path should still work
    from src.core.workflow_orchestrator import WorkflowOrchestrator as OldImport
    from src.core.workflow_orchestrator import WorkflowInstructionManager as OldInstrImport

    # New import path
    from src.core.workflow import WorkflowOrchestrator as NewImport
    from src.core.workflow import WorkflowInstructionManager as NewInstrImport

    # Top-level import
    from src import WorkflowOrchestrator as TopImport

    # All should be the same class
    assert OldImport is NewImport, "Old and new WorkflowOrchestrator imports should be the same class"
    assert TopImport is NewImport, "Top-level and new WorkflowOrchestrator imports should be the same class"
    assert OldInstrImport is NewInstrImport, "Old and new WorkflowInstructionManager imports should be the same class"
    print("✓ All import paths resolve to the same class")

    # New subcomponents should be importable
    from src.core.workflow import WorkflowPlanner, WorkflowExecutor, ControlFlowEngine, StepOptimizer
    assert WorkflowPlanner is not None
    assert WorkflowExecutor is not None
    assert ControlFlowEngine is not None
    assert StepOptimizer is not None
    print("✓ New subcomponent classes are importable")

    return True


def test_planner_json_extraction():
    """Test WorkflowPlanner JSON extraction"""
    print("\nTesting WorkflowPlanner JSON extraction...")

    from src.core.workflow.planner import WorkflowPlanner

    # Create a minimal planner for JSON extraction testing
    planner = WorkflowPlanner.__new__(WorkflowPlanner)

    # Plain JSON
    result = planner._extract_json_from_response('{"steps": []}')
    assert result == {"steps": []}
    print("✓ Plain JSON parsing")

    # JSON with markdown code block
    result = planner._extract_json_from_response('```json\n{"steps": []}\n```')
    assert result == {"steps": []}
    print("✓ Markdown code block JSON parsing")

    # Generic code block
    result = planner._extract_json_from_response('```\n{"steps": []}\n```')
    assert result == {"steps": []}
    print("✓ Generic code block JSON parsing")

    # Invalid JSON returns None
    result = planner._extract_json_from_response("not json at all")
    assert result is None
    print("✓ Invalid JSON returns None")

    return True


def test_planner_plan_from_json():
    """Test WorkflowPlanner plan creation from JSON"""
    print("\nTesting WorkflowPlanner plan creation from JSON...")

    from src.core.workflow.planner import WorkflowPlanner

    planner = WorkflowPlanner.__new__(WorkflowPlanner)

    plan_data = {
        "name": "Test Workflow",
        "description": "A test",
        "steps": [
            {"id": "s1", "name": "Step 1", "description": "Do first thing", "dependencies": []},
            {"id": "s2", "name": "Step 2", "description": "Do second thing", "dependencies": ["s1"]},
        ],
    }

    plan = planner._create_plan_from_json(plan_data, "Test goal")

    assert plan.name == "Test Workflow"
    assert plan.goal == "Test goal"
    assert len(plan.steps) == 2
    assert plan.steps[0].id == "s1"
    assert plan.steps[1].dependencies == ["s1"]
    print("✓ Plan created from JSON correctly")

    # Test with minimal data
    minimal_data = {"steps": [{"id": "s1", "name": "Only Step"}]}
    plan2 = planner._create_plan_from_json(minimal_data, "Minimal goal")
    assert plan2.name == "Unnamed Workflow"
    assert len(plan2.steps) == 1
    print("✓ Plan with minimal data created correctly")

    return True


def run_all_tests():
    """Run all workflow package tests"""
    print("=" * 70)
    print("Running Workflow Package Refactor Tests")
    print("=" * 70)

    tests = [
        ("InstructionManager Standalone", test_instruction_manager_standalone),
        ("Swap Instructions Helper", test_swap_instructions_helper),
        ("ControlFlow Conditions", test_control_flow_engine_conditions),
        ("ControlFlow Conditional Step", test_control_flow_conditional_step),
        ("ControlFlow Loop Step", test_control_flow_loop_step),
        ("ControlFlow Subworkflow", test_control_flow_subworkflow),
        ("ControlFlow Error Handling", test_control_flow_error_handling),
        ("Optimizer Failure Source", test_optimizer_failure_source_detection),
        ("Backward Compat Imports", test_backward_compatibility_imports),
        ("Planner JSON Extraction", test_planner_json_extraction),
        ("Planner Plan from JSON", test_planner_plan_from_json),
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
