"""
Enhanced Workflow Orchestrator Demo

Demonstrates the new workflow orchestration capabilities:
- Conditional branching (if/else)
- Loop constructs (foreach, while, for)
- Nested sub-workflows
- Dynamic workflow modification at runtime
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.workflow import WorkflowPlan, WorkflowStep, StepStatus, StepType
from src.models.config import SystemConfig
from src.core.workflow_orchestrator import WorkflowOrchestrator


def demo_conditional_workflow():
    """Demonstrate conditional branching in workflows"""
    print("\n" + "=" * 70)
    print("DEMO 1: Conditional Branching")
    print("=" * 70)
    
    # Create orchestrator
    config = SystemConfig()
    orchestrator = WorkflowOrchestrator(config)
    
    # Create workflow with conditional branching
    # Scenario: Data validation workflow that branches based on data quality
    
    step1 = WorkflowStep(
        id="validate_data",
        name="Validate Data",
        description="Check data quality score",
        status=StepStatus.COMPLETED,  # Simulate already completed
        outputs={"quality_score": 85, "record_count": 1000},
    )
    
    conditional_step = WorkflowStep(
        id="quality_check",
        name="Quality Check",
        description="Branch based on quality score",
        step_type=StepType.CONDITIONAL,
        condition="validate_data['quality_score'] >= 80",
        branches={
            "true": ["high_quality_processing"],
            "false": ["data_cleanup", "revalidate"],
        },
        dependencies=["validate_data"],
    )
    
    step_high_quality = WorkflowStep(
        id="high_quality_processing",
        name="High Quality Processing",
        description="Process high-quality data directly",
        dependencies=["quality_check"],
    )
    
    step_cleanup = WorkflowStep(
        id="data_cleanup",
        name="Data Cleanup",
        description="Clean up low-quality data",
        dependencies=["quality_check"],
    )
    
    step_revalidate = WorkflowStep(
        id="revalidate",
        name="Revalidate Data",
        description="Validate data after cleanup",
        dependencies=["data_cleanup"],
    )
    
    plan = WorkflowPlan(
        name="Data Processing Workflow",
        description="Process data with quality-based branching",
        goal="Process data efficiently based on quality",
        steps=[step1, conditional_step, step_high_quality, step_cleanup, step_revalidate],
    )
    
    orchestrator.active_workflows[plan.id] = plan
    
    # Execute conditional step
    context = {"validate_data": step1.outputs}
    result = orchestrator.execute_conditional_step(plan.id, "quality_check", context)
    
    print(f"\n✓ Conditional Step Executed")
    print(f"  Condition: quality_score >= 80")
    print(f"  Result: {result['outputs']['condition_result']}")
    print(f"  Branch Taken: {result['outputs']['branch_taken']}")
    
    # Check which steps were skipped
    for step in plan.steps:
        if step.status == StepStatus.SKIPPED:
            print(f"  Skipped: {step.name}")
    
    print("\n✓ Conditional workflow completed successfully!")


def demo_loop_workflow():
    """Demonstrate loop constructs in workflows"""
    print("\n" + "=" * 70)
    print("DEMO 2: Loop Constructs")
    print("=" * 70)
    
    config = SystemConfig()
    orchestrator = WorkflowOrchestrator(config)
    
    # Scenario: Process multiple files in a batch
    
    files_to_process = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
    
    foreach_step = WorkflowStep(
        id="process_files",
        name="Process Files",
        description="Process each file in the batch",
        step_type=StepType.LOOP,
        loop_type="foreach",
        loop_variable="file",
        loop_collection=files_to_process,
        max_iterations=10,
    )
    
    plan = WorkflowPlan(
        name="Batch Processing Workflow",
        description="Process multiple files",
        goal="Process all files in batch",
        steps=[foreach_step],
    )
    
    orchestrator.active_workflows[plan.id] = plan
    
    result = orchestrator.execute_loop_step(plan.id, "process_files")
    
    print(f"\n✓ Foreach Loop Executed")
    print(f"  Loop Type: {result['outputs']['loop_type']}")
    print(f"  Iterations: {result['outputs']['iterations_performed']}")
    print(f"  Files Processed:")
    for iteration in result['outputs']['iterations']:
        print(f"    - {iteration['value']} (iteration {iteration['iteration']})")
    
    # Demonstrate FOR loop
    for_step = WorkflowStep(
        id="count_loop",
        name="Count Loop",
        description="Process items 0 to 5",
        step_type=StepType.LOOP,
        loop_type="for",
        loop_variable="i",
        inputs={"start": 0, "end": 5, "step": 1},
    )
    
    plan.steps.append(for_step)
    
    result = orchestrator.execute_loop_step(plan.id, "count_loop")
    
    print(f"\n✓ For Loop Executed")
    print(f"  Range: 0 to 5")
    print(f"  Iterations: {result['outputs']['iterations_performed']}")
    
    print("\n✓ Loop workflows completed successfully!")


def demo_subworkflow():
    """Demonstrate nested sub-workflows"""
    print("\n" + "=" * 70)
    print("DEMO 3: Nested Sub-Workflows")
    print("=" * 70)
    
    config = SystemConfig()
    orchestrator = WorkflowOrchestrator(config)
    
    # Scenario: E-commerce order processing with sub-workflows
    
    # Create sub-workflow for payment processing
    payment_verify = WorkflowStep(
        id="verify_payment",
        name="Verify Payment",
        description="Verify payment details",
        status=StepStatus.COMPLETED,
        outputs={"payment_valid": True, "amount": 99.99},
    )
    
    payment_process = WorkflowStep(
        id="process_payment",
        name="Process Payment",
        description="Process the payment",
        status=StepStatus.COMPLETED,
        outputs={"transaction_id": "TXN-12345", "status": "success"},
        dependencies=["verify_payment"],
    )
    
    payment_workflow = WorkflowPlan(
        name="Payment Processing",
        description="Handle payment verification and processing",
        goal="Process customer payment",
        steps=[payment_verify, payment_process],
    )
    
    # Create sub-workflow for inventory
    inventory_check = WorkflowStep(
        id="check_inventory",
        name="Check Inventory",
        description="Check item availability",
        status=StepStatus.COMPLETED,
        outputs={"available": True, "quantity": 5},
    )
    
    inventory_reserve = WorkflowStep(
        id="reserve_items",
        name="Reserve Items",
        description="Reserve items for order",
        status=StepStatus.COMPLETED,
        outputs={"reserved": True, "reservation_id": "RES-789"},
        dependencies=["check_inventory"],
    )
    
    inventory_workflow = WorkflowPlan(
        name="Inventory Management",
        description="Handle inventory check and reservation",
        goal="Reserve inventory for order",
        steps=[inventory_check, inventory_reserve],
    )
    
    # Create main workflow with sub-workflows
    order_received = WorkflowStep(
        id="receive_order",
        name="Receive Order",
        description="Receive and validate order",
        status=StepStatus.COMPLETED,
        outputs={"order_id": "ORD-001", "items": ["item1", "item2"]},
    )
    
    payment_subwf = WorkflowStep(
        id="payment_subprocess",
        name="Payment Sub-Process",
        description="Execute payment processing sub-workflow",
        step_type=StepType.SUBWORKFLOW,
        subworkflow_plan=payment_workflow,
        dependencies=["receive_order"],
    )
    
    inventory_subwf = WorkflowStep(
        id="inventory_subprocess",
        name="Inventory Sub-Process",
        description="Execute inventory management sub-workflow",
        step_type=StepType.SUBWORKFLOW,
        subworkflow_plan=inventory_workflow,
        dependencies=["receive_order"],
    )
    
    ship_order = WorkflowStep(
        id="ship_order",
        name="Ship Order",
        description="Ship the order",
        dependencies=["payment_subprocess", "inventory_subprocess"],
    )
    
    main_workflow = WorkflowPlan(
        name="Order Processing Workflow",
        description="Main order processing with sub-workflows",
        goal="Process customer order end-to-end",
        steps=[order_received, payment_subwf, inventory_subwf, ship_order],
    )
    
    orchestrator.active_workflows[main_workflow.id] = main_workflow
    
    # Execute sub-workflows
    print(f"\n✓ Main Workflow: {main_workflow.name}")
    print(f"  Total Steps: {len(main_workflow.steps)}")
    
    # Execute payment sub-workflow
    result = orchestrator.execute_subworkflow_step(main_workflow.id, "payment_subprocess")
    print(f"\n✓ Payment Sub-Workflow Executed")
    print(f"  Status: {result['outputs']['subworkflow_status']}")
    print(f"  Outputs: {len(result['outputs']['subworkflow_outputs'])} steps completed")
    
    # Execute inventory sub-workflow
    result = orchestrator.execute_subworkflow_step(main_workflow.id, "inventory_subprocess")
    print(f"\n✓ Inventory Sub-Workflow Executed")
    print(f"  Status: {result['outputs']['subworkflow_status']}")
    print(f"  Outputs: {len(result['outputs']['subworkflow_outputs'])} steps completed")
    
    print("\n✓ Sub-workflow orchestration completed successfully!")


def demo_dynamic_modification():
    """Demonstrate dynamic workflow modification at runtime"""
    print("\n" + "=" * 70)
    print("DEMO 4: Dynamic Workflow Modification")
    print("=" * 70)
    
    config = SystemConfig()
    orchestrator = WorkflowOrchestrator(config)
    
    # Create initial workflow
    step1 = WorkflowStep(
        id="step1",
        name="Initialize",
        description="Initialize the process",
    )
    
    step2 = WorkflowStep(
        id="step2",
        name="Process",
        description="Process data",
        dependencies=["step1"],
    )
    
    step3 = WorkflowStep(
        id="step3",
        name="Finalize",
        description="Finalize the process",
        dependencies=["step2"],
    )
    
    plan = WorkflowPlan(
        name="Dynamic Workflow",
        description="Workflow that can be modified at runtime",
        goal="Demonstrate dynamic modifications",
        steps=[step1, step2, step3],
    )
    
    orchestrator.active_workflows[plan.id] = plan
    
    print(f"\n✓ Initial Workflow Created")
    print(f"  Steps: {len(plan.steps)}")
    for step in plan.steps:
        print(f"    - {step.name}")
    
    # Add a new step dynamically
    new_step = WorkflowStep(
        id="validation",
        name="Validate",
        description="Validate processed data",
        dependencies=["step2"],
    )
    
    result = orchestrator.add_step_to_workflow(plan.id, new_step, after_step_id="step2")
    
    print(f"\n✓ Step Added Dynamically")
    print(f"  Step: {new_step.name}")
    print(f"  After: step2")
    print(f"  New Total: {len(plan.steps)} steps")
    
    # Modify an existing step
    updates = {
        "description": "Process data with enhanced validation",
        "inputs": {"validation_level": "strict"},
    }
    
    result = orchestrator.modify_step_in_workflow(plan.id, "step2", updates)
    
    print(f"\n✓ Step Modified")
    print(f"  Step: step2")
    print(f"  New Description: {plan.get_step_by_id('step2').description}")
    print(f"  New Inputs: {plan.get_step_by_id('step2').inputs}")
    
    # Add a conditional step dynamically
    conditional = WorkflowStep(
        id="error_check",
        name="Error Check",
        description="Check for errors and branch",
        step_type=StepType.CONDITIONAL,
        condition="step2['status'] == 'success'",
        branches={
            "true": ["step3"],
            "false": ["error_handler"],
        },
        dependencies=["validation"],
    )
    
    result = orchestrator.add_step_to_workflow(plan.id, conditional, after_step_id="validation")
    
    print(f"\n✓ Conditional Step Added")
    print(f"  Step: {conditional.name}")
    print(f"  Type: {conditional.step_type.value}")
    print(f"  Condition: {conditional.condition}")
    
    # Remove a step (must be pending)
    # First, let's try to remove a step that hasn't started
    result = orchestrator.remove_step_from_workflow(plan.id, "validation")
    
    if result["success"]:
        print(f"\n✓ Step Removed")
        print(f"  Step: validation")
        print(f"  Final Total: {len(plan.steps)} steps")
    
    print(f"\n✓ Final Workflow Structure:")
    for i, step in enumerate(plan.steps, 1):
        deps = f" (depends on: {', '.join(step.dependencies)})" if step.dependencies else ""
        print(f"  {i}. {step.name} [{step.step_type.value}]{deps}")
    
    print("\n✓ Dynamic workflow modification completed successfully!")


def demo_complex_workflow():
    """Demonstrate a complex workflow combining all features"""
    print("\n" + "=" * 70)
    print("DEMO 5: Complex Workflow (All Features Combined)")
    print("=" * 70)
    
    config = SystemConfig()
    orchestrator = WorkflowOrchestrator(config)
    
    print("\nScenario: ETL Pipeline with Conditional Processing and Error Handling")
    print("-" * 70)
    
    # Step 1: Extract data
    extract = WorkflowStep(
        id="extract",
        name="Extract Data",
        description="Extract data from source",
        status=StepStatus.COMPLETED,
        outputs={"records": 1000, "quality": 85},
    )
    
    # Step 2: Quality check (conditional)
    quality_check = WorkflowStep(
        id="quality_check",
        name="Quality Check",
        description="Check data quality",
        step_type=StepType.CONDITIONAL,
        condition="extract['quality'] >= 80",
        branches={
            "true": ["transform_direct"],
            "false": ["clean_data"],
        },
        dependencies=["extract"],
    )
    
    # Branch 1: Direct transform (high quality)
    transform_direct = WorkflowStep(
        id="transform_direct",
        name="Transform Data",
        description="Transform high-quality data",
        dependencies=["quality_check"],
    )
    
    # Branch 2: Clean then transform (low quality)
    clean_data = WorkflowStep(
        id="clean_data",
        name="Clean Data",
        description="Clean low-quality data",
        step_type=StepType.LOOP,
        loop_type="foreach",
        loop_variable="record",
        loop_collection=list(range(10)),  # Simulate processing records
        max_iterations=100,
        dependencies=["quality_check"],
    )
    
    # Step 3: Load data (sub-workflow)
    load_validate = WorkflowStep(
        id="load_validate",
        name="Validate Load",
        description="Validate data before loading",
        status=StepStatus.COMPLETED,
        outputs={"valid": True},
    )
    
    load_execute = WorkflowStep(
        id="load_execute",
        name="Execute Load",
        description="Load data to target",
        status=StepStatus.COMPLETED,
        outputs={"loaded": True, "count": 1000},
        dependencies=["load_validate"],
    )
    
    load_subworkflow = WorkflowPlan(
        name="Load Process",
        description="Load data with validation",
        goal="Load data safely",
        steps=[load_validate, load_execute],
    )
    
    load_step = WorkflowStep(
        id="load",
        name="Load Sub-Process",
        description="Execute load sub-workflow",
        step_type=StepType.SUBWORKFLOW,
        subworkflow_plan=load_subworkflow,
        dependencies=["transform_direct", "clean_data"],
    )
    
    # Create workflow
    plan = WorkflowPlan(
        name="ETL Pipeline",
        description="Complex ETL with all orchestration features",
        goal="Process data end-to-end with quality checks",
        steps=[extract, quality_check, transform_direct, clean_data, load_step],
    )
    
    orchestrator.active_workflows[plan.id] = plan
    
    print(f"\n✓ Complex Workflow Created")
    print(f"  Total Steps: {len(plan.steps)}")
    print(f"  Features Used:")
    print(f"    - Standard steps: 2")
    print(f"    - Conditional branching: 1")
    print(f"    - Loop processing: 1")
    print(f"    - Sub-workflows: 1")
    
    # Execute conditional
    context = {"extract": extract.outputs}
    result = orchestrator.execute_conditional_step(plan.id, "quality_check", context)
    print(f"\n✓ Quality Check: {result['outputs']['branch_taken']} branch")
    
    # Since quality >= 80, clean_data should be skipped
    print(f"  Skipped low-quality branch: {plan.get_step_by_id('clean_data').status.value}")
    
    print("\n✓ Complex workflow orchestration completed successfully!")


def main():
    """Run all demos"""
    print("\n")
    print("=" * 70)
    print("Enhanced Workflow Orchestrator - Feature Demonstration")
    print("=" * 70)
    print("\nThis demo showcases the new workflow orchestration capabilities:")
    print("  1. Conditional Branching (if/else, switch/case)")
    print("  2. Loop Constructs (foreach, while, for)")
    print("  3. Nested Sub-Workflows")
    print("  4. Dynamic Runtime Modification")
    print("  5. Complex Combined Workflows")
    
    try:
        demo_conditional_workflow()
        demo_loop_workflow()
        demo_subworkflow()
        demo_dynamic_modification()
        demo_complex_workflow()
        
        print("\n" + "=" * 70)
        print("All Demos Completed Successfully!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("✓ Workflows can now branch based on runtime conditions")
        print("✓ Loops enable batch processing and iteration")
        print("✓ Sub-workflows provide modularity and reusability")
        print("✓ Workflows can be modified dynamically at runtime")
        print("✓ All features work together seamlessly")
        print("\nFor more information, see the documentation and tests.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
