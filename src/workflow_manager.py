"""
Workflow management for SelfOptimizingSystem.

Handles multi-step workflow execution using the Planner-Executor-Critic pattern.
"""

from typing import Optional, Dict, Any


class WorkflowManager:
    """Manages workflow execution for the system.

    Lazily initializes the WorkflowOrchestrator and delegates
    workflow execution to it.
    """

    def __init__(self, config, instruction_manager):
        self.config = config
        self.instruction_manager = instruction_manager
        self._workflow_orchestrator = None

    def execute_workflow(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Execute a multi-step workflow from a high-level goal.

        This creates a workflow plan using the Planner, executes steps with the Executor,
        and automatically optimizes based on failures using the Critic.

        Args:
            goal: The high-level objective to achieve
            context: Optional context information for planning
            max_retries: Maximum retries for failed steps

        Returns:
            Dict with workflow execution results including:
            - workflow_id: Unique workflow identifier
            - status: completed or failed
            - steps_completed: Number of successful steps
            - results: Detailed results for each step
        """
        if self._workflow_orchestrator is None:
            from .core.workflow import WorkflowOrchestrator
            self._workflow_orchestrator = WorkflowOrchestrator(
                self.config,
                self.instruction_manager,
            )

        return self._workflow_orchestrator.execute_workflow(goal, context, max_retries)
