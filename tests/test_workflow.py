"""
Tests for Workflow Orchestrator

Tests the Planner-Executor-Critic workflow orchestration system
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src directory to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.workflow import WorkflowPlan, WorkflowStep, StepStatus, FailureSource
from src.models.config import SystemConfig
from src.core.workflow_orchestrator import WorkflowOrchestrator


def test_workflow_models():
    """Test workflow data models"""
    print("Testing workflow models...")
    
    # Test WorkflowStep creation
    step = WorkflowStep(
        id="step_1",
        name="Test Step",
        description="A test step",
        dependencies=[],
    )
    
    assert step.id == "step_1"
    assert step.name == "Test Step"
    assert step.status == StepStatus.PENDING
    
    # Test step serialization
    step_dict = step.to_dict()
    assert step_dict["id"] == "step_1"
    assert step_dict["status"] == "pending"
    
    # Test step deserialization
    step2 = WorkflowStep.from_dict(step_dict)
    assert step2.id == step.id
    assert step2.name == step.name
    
    print("✓ WorkflowStep creation and serialization")
    
    # Test WorkflowPlan
    step1 = WorkflowStep(id="s1", name="Step 1", dependencies=[])
    step2 = WorkflowStep(id="s2", name="Step 2", dependencies=["s1"])
    step3 = WorkflowStep(id="s3", name="Step 3", dependencies=["s1"])
    
    plan = WorkflowPlan(
        name="Test Workflow",
        description="A test workflow",
        goal="Test goal",
        steps=[step1, step2, step3],
    )
    
    assert len(plan.steps) == 3
    assert plan.get_step_by_id("s1") == step1
    assert plan.get_step_by_id("invalid") is None
    
    print("✓ WorkflowPlan creation and step lookup")
    
    # Test dependency resolution
    ready_steps = plan.get_ready_steps()
    assert len(ready_steps) == 1
    assert ready_steps[0].id == "s1"
    
    # Mark step 1 as completed
    step1.status = StepStatus.COMPLETED
    ready_steps = plan.get_ready_steps()
    assert len(ready_steps) == 2
    assert all(s.id in ["s2", "s3"] for s in ready_steps)
    
    print("✓ Dependency resolution")
    
    # Test completion status
    assert not plan.is_complete()
    step2.status = StepStatus.COMPLETED
    step3.status = StepStatus.COMPLETED
    assert plan.is_complete()
    
    print("✓ Workflow completion tracking")
    
    # Test serialization
    plan_dict = plan.to_dict()
    plan2 = WorkflowPlan.from_dict(plan_dict)
    assert plan2.name == plan.name
    assert len(plan2.steps) == len(plan.steps)
    
    print("✓ WorkflowPlan serialization and deserialization")
    
    return True


def test_workflow_instruction_manager():
    """Test workflow instruction manager"""
    print("\nTesting workflow instruction manager...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create instruction files
        (instructions_dir / "planner.md").write_text("# Planner Instructions\n\nTest content")
        (instructions_dir / "actor.md").write_text("# Actor Instructions\n\nTest content")
        
        config = SystemConfig(instructions_dir=instructions_dir)
        
        from src.core.workflow_orchestrator import WorkflowInstructionManager
        
        manager = WorkflowInstructionManager(config, instructions_dir)
        
        # Test reading instructions
        planner_inst = manager.get_planner_instructions()
        actor_inst = manager.get_actor_instructions()
        
        assert "Planner Instructions" in planner_inst
        assert "Actor Instructions" in actor_inst
        
        print("✓ Reading planner and actor instructions")
        
        # Test version tracking
        assert manager.current_planner_version is not None
        assert manager.current_actor_version is not None
        
        print("✓ Version tracking initialized")
        
        # Test updating instructions
        initial_version = manager.current_planner_version
        new_planner = planner_inst + "\n\nNew rule"
        version = manager.update_planner_instructions(
            new_planner,
            "test",
            "Added new rule"
        )
        
        assert version is not None
        assert "New rule" in manager.get_planner_instructions()
        
        print("✓ Updating and versioning instructions")
        
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_workflow_orchestrator_init():
    """Test workflow orchestrator initialization"""
    print("\nTesting workflow orchestrator initialization...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    instructions_dir = Path(temp_dir) / "instructions"
    instructions_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create instruction files
        (instructions_dir / "planner.md").write_text("# Planner\n\nPlan workflows")
        (instructions_dir / "actor.md").write_text("# Actor\n\nExecute steps")
        (instructions_dir / "instructions.md").write_text("# Instructions\n\nBase")
        
        config = SystemConfig(instructions_dir=instructions_dir)
        
        orchestrator = WorkflowOrchestrator(config)
        
        assert orchestrator.config == config
        assert orchestrator.planner is not None
        assert orchestrator.executor is not None
        assert orchestrator.critic is not None
        
        print("✓ Orchestrator initialized with all components")
        
        # Test active workflows tracking
        assert len(orchestrator.active_workflows) == 0
        assert len(orchestrator.workflow_history) == 0
        
        print("✓ Workflow tracking initialized")
        
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_fallback_plan_creation():
    """Test fallback plan creation"""
    print("\nTesting fallback plan creation...")
    
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
        
        # Create fallback plan
        plan = orchestrator._create_fallback_plan("Test goal")
        
        assert plan.goal == "Test goal"
        assert len(plan.steps) == 1
        assert plan.steps[0].name == "Execute Goal"
        
        print("✓ Fallback plan created correctly")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_workflow_step_status():
    """Test workflow step status tracking"""
    print("\nTesting workflow step status tracking...")
    
    step = WorkflowStep(
        id="test_step",
        name="Test",
        description="Test step",
    )
    
    # Initial status
    assert step.status == StepStatus.PENDING
    assert step.started_at is None
    assert step.completed_at is None
    
    print("✓ Initial step status")
    
    # Update status
    from datetime import datetime
    step.status = StepStatus.RUNNING
    step.started_at = datetime.now()
    
    assert step.status == StepStatus.RUNNING
    assert step.started_at is not None
    
    print("✓ Running status")
    
    # Complete step
    step.status = StepStatus.COMPLETED
    step.completed_at = datetime.now()
    step.outputs = {"result": "success"}
    
    assert step.status == StepStatus.COMPLETED
    assert step.completed_at is not None
    assert "result" in step.outputs
    
    print("✓ Completed status with outputs")
    
    # Failed step
    failed_step = WorkflowStep(id="failed", name="Failed")
    failed_step.status = StepStatus.FAILED
    failed_step.error_message = "Something went wrong"
    
    assert failed_step.status == StepStatus.FAILED
    assert failed_step.error_message is not None
    
    print("✓ Failed status with error message")
    
    return True


def run_all_tests():
    """Run all workflow tests"""
    print("=" * 70)
    print("Running Workflow Orchestrator Tests")
    print("=" * 70)
    
    tests = [
        ("Workflow Models", test_workflow_models),
        ("Workflow Instruction Manager", test_workflow_instruction_manager),
        ("Workflow Orchestrator Init", test_workflow_orchestrator_init),
        ("Fallback Plan Creation", test_fallback_plan_creation),
        ("Workflow Step Status", test_workflow_step_status),
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
