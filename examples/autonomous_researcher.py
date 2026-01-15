#!/usr/bin/env python3
"""
Autonomous Researcher Example - Workflow Orchestrator Demo

Demonstrates the Self-Optimizing Workflow Orchestrator using the
Planner-Executor-Critic pattern for a research task.

This example shows:
1. Dynamic planning from a high-level goal
2. Step-by-step execution with dependency management
3. Automatic failure recovery through Critic optimization
4. Granular versioning of planner and actor instructions
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import SelfOptimizingSystem


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def print_workflow_status(status: dict):
    """Print workflow status in a readable format"""
    print(f"Workflow: {status['name']}")
    print(f"Goal: {status['goal']}")
    print(f"Status: {status['status']}")
    print(f"Progress: {status['completed_steps']}/{status['total_steps']} steps completed")
    
    if status['failed_steps'] > 0:
        print(f"Failed: {status['failed_steps']} steps")
    
    print("\nSteps:")
    for step in status['steps']:
        status_icon = {
            'completed': '✓',
            'failed': '✗',
            'running': '→',
            'pending': '○',
            'skipped': '-'
        }.get(step['status'], '?')
        
        print(f"  {status_icon} {step['name']} ({step['status']})")
        if step.get('error'):
            print(f"    Error: {step['error']}")


def main():
    """Run the autonomous researcher demo"""
    
    print_section("Autonomous Researcher - Workflow Orchestrator Demo")
    
    print("This demo shows how the workflow orchestrator:")
    print("1. Plans a multi-step research workflow from a goal")
    print("2. Executes steps with proper dependency management")
    print("3. Recovers from failures using Critic optimization")
    print("4. Maintains separate versions for planner and actor instructions")
    
    # Initialize the system
    print_section("1. Initializing Self-Optimizing System")
    system = SelfOptimizingSystem()
    print("✓ System initialized")
    
    # Define research goal
    research_goal = """
    Research and create a comprehensive report on the current state of 
    autonomous AI agents in 2024, including key capabilities, challenges, 
    and future directions.
    """
    
    print_section("2. Executing Research Workflow")
    print(f"Goal: {research_goal.strip()}")
    
    # Execute the workflow
    print("\nCreating workflow plan and executing steps...")
    result = system.execute_workflow(
        goal=research_goal,
        context={
            "output_format": "markdown report",
            "focus_areas": ["capabilities", "challenges", "future directions"],
            "target_length": "1500-2000 words"
        },
        max_retries=3
    )
    
    # Show results
    print_section("3. Workflow Results")
    
    print(f"Workflow ID: {result['workflow_id']}")
    print(f"Status: {result['status']}")
    print(f"Total Steps: {result['total_steps']}")
    print(f"Completed: {result['steps_completed']}")
    print(f"Failed: {result['steps_failed']}")
    
    # Show step details
    print("\n--- Step Execution Details ---\n")
    for i, step_result in enumerate(result['results'], 1):
        step_id = step_result['step_id']
        success = step_result['success']
        status_icon = '✓' if success else '✗'
        
        print(f"{i}. Step {step_id}: {status_icon} {step_result['status']}")
        
        if success and step_result.get('outputs'):
            outputs = step_result['outputs']
            if isinstance(outputs, dict):
                for key, value in outputs.items():
                    value_str = str(value)[:100]
                    if len(str(value)) > 100:
                        value_str += "..."
                    print(f"   Output '{key}': {value_str}")
        
        if not success and step_result.get('error'):
            print(f"   Error: {step_result['error']}")
    
    # Show failures and recovery
    if result['failures']:
        print_section("4. Failures and Recovery")
        
        print("The following failures occurred during execution:")
        for failure in result['failures']:
            print(f"\n- Step: {failure['step_name']} (ID: {failure['step_id']})")
            print(f"  Error: {failure['error']}")
        
        print("\n✓ Critic analyzed failures and optimized instructions")
        print("✓ Failed steps were retried with improved instructions")
    
    # Show final workflow state
    print_section("5. Final Workflow State")
    
    workflow_data = result.get('workflow', {})
    if workflow_data:
        print(f"Workflow: {workflow_data.get('name', 'N/A')}")
        print(f"Created: {workflow_data.get('created_at', 'N/A')}")
        print(f"Completed: {workflow_data.get('completed_at', 'N/A')}")
        print(f"Planner Version: {workflow_data.get('planner_version', 'N/A')}")
        print(f"Actor Version: {workflow_data.get('actor_version', 'N/A')}")
        
        steps = workflow_data.get('steps', [])
        if steps:
            print(f"\nTotal Steps: {len(steps)}")
            completed = sum(1 for s in steps if s.get('status') == 'completed')
            failed = sum(1 for s in steps if s.get('status') == 'failed')
            print(f"Completed: {completed}")
            print(f"Failed: {failed}")
    
    # Summary
    print_section("Demo Summary")
    
    if result['status'] == 'completed':
        print("✓ Workflow completed successfully!")
        print(f"✓ All {result['steps_completed']} steps executed")
    else:
        print("⚠ Workflow completed with some failures")
        print(f"✓ {result['steps_completed']} steps completed")
        print(f"✗ {result['steps_failed']} steps failed")
    
    print("\nKey Features Demonstrated:")
    print("✓ Dynamic workflow planning from high-level goals")
    print("✓ Dependency-aware step execution")
    print("✓ Automatic failure analysis and recovery")
    print("✓ Separate planner and actor instruction optimization")
    print("✓ Granular version control for each role")
    
    print("\n" + "=" * 70)
    print("For more information, see:")
    print("- Workflow models: src/models/workflow.py")
    print("- Orchestrator: src/core/workflow_orchestrator.py")
    print("- Planner instructions: instructions/planner.md")
    print("- Actor instructions: instructions/actor.md")
    print("=" * 70)


def demo_simple_workflow():
    """
    Run a simpler workflow demo for testing
    """
    print_section("Simple Workflow Demo")
    
    system = SelfOptimizingSystem()
    
    # Simpler goal
    goal = "Calculate the sum of numbers from 1 to 10 and report the result"
    
    print(f"Goal: {goal}\n")
    
    result = system.execute_workflow(goal=goal, max_retries=2)
    
    print(f"\nStatus: {result['status']}")
    print(f"Steps: {result['steps_completed']}/{result['total_steps']} completed")
    
    return result


if __name__ == "__main__":
    # Run full demo by default
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        demo_simple_workflow()
    else:
        main()
