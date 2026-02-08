"""
Workflow Step Optimizer

Handles critic-based optimization of workflow steps.
Analyzes failures to determine root cause and optimizes
planner or actor instructions accordingly.
"""

from typing import Dict, Any
import json

from ...models.config import FailureEntry
from ...models.workflow import (
    WorkflowPlan,
    WorkflowStep,
    WorkflowFailure,
    StepStatus,
    FailureSource,
)
from .instruction_manager import WorkflowInstructionManager


class StepOptimizer:
    """
    Optimizes workflow step execution through critic-based analysis

    Responsibilities:
    - Handle step failures and determine root cause
    - Optimize planner instructions for planning failures
    - Optimize actor instructions for execution failures
    """

    def __init__(
        self,
        critic_model,
        workflow_instruction_manager: WorkflowInstructionManager,
    ):
        self.critic = critic_model
        self.workflow_instruction_manager = workflow_instruction_manager

    def handle_step_failure(self, workflow: WorkflowPlan, failed_step: WorkflowStep):
        """
        Handle a failed workflow step using the Critic
        
        Determines whether failure was due to planning or execution,
        then optimizes the appropriate instruction set
        """
        # Analyze failure source
        failure_source = self._determine_failure_source(workflow, failed_step)

        # Create workflow failure context
        workflow_failure = WorkflowFailure(
            workflow_id=workflow.id,
            step_id=failed_step.id,
            failure_source=failure_source,
            error_message=failed_step.error_message or "Unknown error",
            step_context={
                "name": failed_step.name,
                "description": failed_step.description,
                "inputs": failed_step.inputs,
                "dependencies": failed_step.dependencies,
            },
            workflow_context={
                "goal": workflow.goal,
                "total_steps": len(workflow.steps),
                "completed_steps": len(
                    [s for s in workflow.steps if s.status == StepStatus.COMPLETED]
                ),
                "step_sequence": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "status": s.status.value,
                    }
                    for s in workflow.steps
                ],
            },
        )

        # Create failure entry for critic
        failure_entry = FailureEntry(
            trigger_type="workflow_step_failure",
            failure_description=f"Step '{failed_step.name}' failed: {failed_step.error_message}",
            user_query=workflow.goal,
            last_model_output=json.dumps(workflow_failure.to_dict(), indent=2),
            severity="high",
        )

        # Optimize based on failure source
        if failure_source == FailureSource.PLANNING:
            self._optimize_planner(failure_entry, workflow_failure)
        else:
            self._optimize_actor(failure_entry, workflow_failure)

    def _determine_failure_source(
        self, workflow: WorkflowPlan, failed_step: WorkflowStep
    ) -> FailureSource:
        """
        Determine if failure was due to planning or execution
        
        Planning failures: missing dependencies, wrong order, unclear objectives
        Execution failures: implementation issues, runtime errors, resource problems
        """
        error = (failed_step.error_message or "").lower()

        # Indicators of planning issues
        planning_indicators = [
            "dependency",
            "precondition",
            "missing input",
            "wrong order",
            "unclear",
            "ambiguous",
        ]

        for indicator in planning_indicators:
            if indicator in error:
                return FailureSource.PLANNING

        # Default to execution failure
        return FailureSource.EXECUTION

    def _optimize_planner(
        self, failure_entry: FailureEntry, workflow_failure: WorkflowFailure
    ):
        """Optimize planner instructions based on workflow failure"""
        # Add failure context specific to planning
        failure_entry.user_feedback = f"""
Workflow planning issue detected.

Workflow Goal: {workflow_failure.workflow_context.get('goal')}
Failed Step: {workflow_failure.step_context.get('name')}
Error: {workflow_failure.error_message}

The plan needs improvement. Consider:
- Were dependencies properly identified?
- Was the step sequence logical?
- Were preconditions clearly defined?
- Was the step description actionable?

Update the planner instructions to avoid similar planning mistakes.
"""

        # Use critic to optimize
        result = self.critic.optimize(failure_entry)

        if result.get("success"):
            # Update planner instructions
            new_instructions = result.get("updated_instructions", "")
            if new_instructions:
                self.workflow_instruction_manager.update_planner_instructions(
                    new_instructions,
                    "workflow_planning_failure",
                    f"Optimized after step '{workflow_failure.step_context.get('name')}' failure",
                )

    def _optimize_actor(
        self, failure_entry: FailureEntry, workflow_failure: WorkflowFailure
    ):
        """Optimize actor instructions based on execution failure"""
        # Add failure context specific to execution
        failure_entry.user_feedback = f"""
Workflow execution issue detected.

Step: {workflow_failure.step_context.get('name')}
Description: {workflow_failure.step_context.get('description')}
Error: {workflow_failure.error_message}

The execution needs improvement. Consider:
- Were inputs validated properly?
- Was error handling robust enough?
- Were edge cases considered?
- Was the output format correct?

Update the actor instructions to improve execution reliability.
"""

        # Use critic to optimize
        result = self.critic.optimize(failure_entry)

        if result.get("success"):
            # Update actor instructions
            new_instructions = result.get("updated_instructions", "")
            if new_instructions:
                self.workflow_instruction_manager.update_actor_instructions(
                    new_instructions,
                    "workflow_execution_failure",
                    f"Optimized after step '{workflow_failure.step_context.get('name')}' failure",
                )
