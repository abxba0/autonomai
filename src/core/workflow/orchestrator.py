"""
Workflow Orchestrator

Top-level coordination for multi-step workflows using the
Planner-Executor-Critic pattern. Delegates to specialized subcomponents
for planning, execution, control flow, and optimization.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from ...models.config import SystemConfig
from ...models.workflow import WorkflowPlan, WorkflowStep, StepStatus
from ..main_model import MainModel
from ..critic_model import CriticModel
from ..instruction_manager import InstructionManager
from .instruction_manager import WorkflowInstructionManager
from .planner import WorkflowPlanner
from .executor import WorkflowExecutor
from .control_flow import ControlFlowEngine
from .optimizer import StepOptimizer


class WorkflowOrchestrator:
    """
    Orchestrates multi-step workflows using the Planner-Executor-Critic pattern
    
    Features:
    - Dynamic planning: Generates workflow plans from high-level goals
    - Specialized execution: Executes steps with role-specific instructions
    - Self-optimization: Learns from failures to improve planning and execution
    - Trajectory correction: Optimizes entire workflow patterns, not just individual steps
    """
    
    # Safety limit: extra iterations beyond calculated retries to prevent edge case infinite loops
    WORKFLOW_SAFETY_BUFFER = 10

    def __init__(
        self,
        config: Optional[SystemConfig] = None,
        instruction_manager: Optional[InstructionManager] = None,
    ):
        self.config = config or SystemConfig()
        self.base_instruction_manager = instruction_manager or InstructionManager(
            self.config
        )

        # Initialize workflow-specific instruction manager
        self.workflow_instruction_manager = WorkflowInstructionManager(
            self.config, self.config.instructions_dir
        )

        # Initialize models for different roles
        self._init_planner()
        self._init_executor()
        self._init_critic()

        # Track active workflows
        self.active_workflows: Dict[str, WorkflowPlan] = {}
        self.workflow_history: List[WorkflowPlan] = []

        # Initialize subcomponents
        self._init_subcomponents()

    def _init_planner(self):
        """Initialize the Planner model with planner instructions"""
        self.planner = MainModel(
            self.config,
            self.base_instruction_manager,
            validation_pipeline=None,
        )

    def _init_executor(self):
        """Initialize the Executor model with actor instructions"""
        self.executor = MainModel(
            self.config,
            self.base_instruction_manager,
            validation_pipeline=None,
        )

    def _init_critic(self):
        """Initialize the Critic model for workflow optimization"""
        self.critic = CriticModel(self.config, self.base_instruction_manager)

    def _init_subcomponents(self):
        """Initialize all subcomponents with dependency injection"""
        # Optimizer
        self._optimizer = StepOptimizer(
            critic_model=self.critic,
            workflow_instruction_manager=self.workflow_instruction_manager,
        )

        # Control flow engine (needs execute_step_by_type callback)
        self._control_flow = ControlFlowEngine(
            active_workflows=self.active_workflows,
            execute_step_by_type_fn=None,  # Set after executor is created
        )

        # Executor
        self._executor_component = WorkflowExecutor(
            workflow_instruction_manager=self.workflow_instruction_manager,
            executor_model=self.executor,
            base_instruction_manager=self.base_instruction_manager,
            active_workflows=self.active_workflows,
            control_flow=self._control_flow,
            execute_workflow_fn=self.execute_workflow,
        )

        # Wire up the control flow's step execution callback
        self._control_flow._execute_step_by_type = self._executor_component.execute_step_by_type

        # Planner
        self._planner_component = WorkflowPlanner(
            workflow_instruction_manager=self.workflow_instruction_manager,
            planner_model=self.planner,
            base_instruction_manager=self.base_instruction_manager,
            active_workflows=self.active_workflows,
        )

    def create_workflow_plan(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> WorkflowPlan:
        """
        Use the Planner to generate a workflow plan from a high-level goal
        
        Args:
            goal: The high-level objective to achieve
            context: Optional context information to inform planning
            
        Returns:
            WorkflowPlan with steps and dependencies
        """
        return self._planner_component.create_workflow_plan(goal, context)

    def _create_fallback_plan(self, goal: str) -> WorkflowPlan:
        """Create a simple fallback plan if planning fails"""
        return self._planner_component._create_fallback_plan(goal)

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks"""
        return self._planner_component._extract_json_from_response(response)

    def execute_step(
        self, workflow_id: str, step_id: str, inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step using the Executor
        """
        return self._executor_component.execute_step(workflow_id, step_id, inputs)

    def _execute_step_by_type(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a step based on its type"""
        return self._executor_component.execute_step_by_type(workflow_id, step_id, context)

    def _evaluate_condition(
        self, condition: str, context: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition expression in the given context"""
        return self._control_flow._evaluate_condition(condition, context)

    def execute_conditional_step(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a conditional step (if/else or switch/case)"""
        return self._control_flow.execute_conditional_step(workflow_id, step_id, context)

    def execute_loop_step(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a loop step (while, for, foreach)"""
        return self._control_flow.execute_loop_step(workflow_id, step_id, context)

    def execute_subworkflow_step(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a subworkflow step"""
        return self._control_flow.execute_subworkflow_step(workflow_id, step_id, context)

    def execute_workflow(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow from goal to completion
        
        This is the main entry point for workflow execution. It:
        1. Creates a plan using the Planner
        2. Executes steps using the Executor
        3. Handles failures using the Critic
        4. Retries failed steps with optimized instructions
        
        Args:
            goal: The high-level objective to achieve
            context: Optional context for planning
            max_retries: Maximum number of retries for failed steps
            
        Returns:
            Dict with workflow execution results
        """
        # Create workflow plan
        workflow = self.create_workflow_plan(goal, context)
        workflow.started_at = datetime.now()

        execution_results = {
            "workflow_id": workflow.id,
            "goal": goal,
            "status": "running",
            "steps_completed": 0,
            "steps_failed": 0,
            "total_steps": len(workflow.steps),
            "results": [],
            "failures": [],
        }

        retry_count = 0
        # Safety limit: Calculate max iterations based on workflow size and retries
        # Buffer allows for edge cases without risking infinite loops
        max_iterations = len(workflow.steps) * (max_retries + 1) + self.WORKFLOW_SAFETY_BUFFER
        iteration_count = 0

        # Execute workflow steps
        while not workflow.is_complete() and retry_count < max_retries and iteration_count < max_iterations:
            iteration_count += 1
            ready_steps = workflow.get_ready_steps()

            if not ready_steps:
                # No steps ready - either all done or blocked by failures
                if workflow.has_failures():
                    # Try to optimize and retry failed steps
                    failed_steps = workflow.get_failed_steps()
                    for failed_step in failed_steps:
                        self._handle_step_failure(workflow, failed_step)
                        # Preserve failure history in execution log before retrying
                        failed_step.execution_log.append(
                            {
                                "timestamp": datetime.now().isoformat(),
                                "event": "retry_attempt",
                                "previous_error": failed_step.error_message,
                                "retry_count": retry_count + 1,
                            }
                        )
                        # Reset step to retry
                        failed_step.status = StepStatus.PENDING
                        failed_step.error_message = None

                    retry_count += 1
                else:
                    # All steps complete
                    break
            else:
                # Execute ready steps
                # Build execution context from previous step outputs
                execution_context = {}
                for completed_step in workflow.steps:
                    if completed_step.status == StepStatus.COMPLETED and completed_step.outputs:
                        execution_context[completed_step.id] = completed_step.outputs
                
                for step in ready_steps:
                    result = self._execute_step_by_type(workflow.id, step.id, execution_context)
                    execution_results["results"].append(result)

                    if result["success"]:
                        execution_results["steps_completed"] += 1
                    else:
                        execution_results["steps_failed"] += 1
                        execution_results["failures"].append(
                            {
                                "step_id": step.id,
                                "step_name": step.name,
                                "error": result["error"],
                            }
                        )

        # Finalize workflow
        workflow.completed_at = datetime.now()
        self.workflow_history.append(workflow)

        # Count actual completed steps (including pre-completed ones)
        total_completed = sum(1 for s in workflow.steps if s.status == StepStatus.COMPLETED)
        total_failed = sum(1 for s in workflow.steps if s.status == StepStatus.FAILED)
        
        execution_results["steps_completed"] = total_completed
        execution_results["steps_failed"] = total_failed
        execution_results["status"] = (
            "completed" if workflow.is_complete() else "failed"
        )
        execution_results["workflow"] = workflow.to_dict()

        return execution_results

    def _handle_step_failure(self, workflow: WorkflowPlan, failed_step: WorkflowStep):
        """Handle a failed workflow step using the Critic"""
        self._optimizer.handle_step_failure(workflow, failed_step)

    def _determine_failure_source(self, workflow, failed_step):
        """Determine if failure was due to planning or execution"""
        return self._optimizer._determine_failure_source(workflow, failed_step)

    def _optimize_planner(self, failure_entry, workflow_failure):
        """Optimize planner instructions based on workflow failure"""
        return self._optimizer._optimize_planner(failure_entry, workflow_failure)

    def _optimize_actor(self, failure_entry, workflow_failure):
        """Optimize actor instructions based on execution failure"""
        return self._optimizer._optimize_actor(failure_entry, workflow_failure)

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None

        return {
            "id": workflow.id,
            "name": workflow.name,
            "goal": workflow.goal,
            "status": "complete" if workflow.is_complete() else "in_progress",
            "total_steps": len(workflow.steps),
            "completed_steps": len(
                [s for s in workflow.steps if s.status == StepStatus.COMPLETED]
            ),
            "failed_steps": len(
                [s for s in workflow.steps if s.status == StepStatus.FAILED]
            ),
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status.value,
                    "error": s.error_message,
                }
                for s in workflow.steps
            ],
        }

    def add_step_to_workflow(
        self, workflow_id: str, step: WorkflowStep, after_step_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically add a step to an active workflow
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {
                "success": False,
                "error": f"Workflow {workflow_id} not found",
            }
        
        success = workflow.insert_step(step, after_step_id)
        
        if success:
            workflow.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "step_added",
                "step_id": step.id,
                "step_name": step.name,
                "after_step_id": after_step_id,
            })
        
        return {
            "success": success,
            "workflow_id": workflow_id,
            "step_id": step.id,
        }

    def remove_step_from_workflow(
        self, workflow_id: str, step_id: str
    ) -> Dict[str, Any]:
        """
        Dynamically remove a step from an active workflow
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {
                "success": False,
                "error": f"Workflow {workflow_id} not found",
            }
        
        step = workflow.get_step_by_id(step_id)
        if not step:
            return {
                "success": False,
                "error": f"Step {step_id} not found",
            }
        
        # Don't allow removal of running or completed steps
        if step.status in [StepStatus.RUNNING, StepStatus.COMPLETED]:
            return {
                "success": False,
                "error": f"Cannot remove step with status {step.status.value}",
            }
        
        success = workflow.remove_step(step_id)
        
        if success:
            workflow.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "step_removed",
                "step_id": step_id,
            })
        
        return {
            "success": success,
            "workflow_id": workflow_id,
            "step_id": step_id,
        }

    def modify_step_in_workflow(
        self, workflow_id: str, step_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically modify a step in an active workflow
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {
                "success": False,
                "error": f"Workflow {workflow_id} not found",
            }
        
        step = workflow.get_step_by_id(step_id)
        if not step:
            return {
                "success": False,
                "error": f"Step {step_id} not found",
            }
        
        # Don't allow modification of running or completed steps
        if step.status in [StepStatus.RUNNING, StepStatus.COMPLETED]:
            return {
                "success": False,
                "error": f"Cannot modify step with status {step.status.value}",
            }
        
        success = workflow.update_step(step_id, updates)
        
        if success:
            workflow.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "step_modified",
                "step_id": step_id,
                "updates": updates,
            })
        
        return {
            "success": success,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "updates": updates,
        }

    def execute_workflows_batch(
        self,
        workflows: List[Dict[str, Any]],
        max_parallel: int = 4,
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """Execute multiple workflows in parallel (batch processing)"""
        return self._executor_component.execute_workflows_batch(
            workflows, max_parallel, max_retries
        )

    def execute_workflows_with_shared_context(
        self,
        workflows: List[Dict[str, Any]],
        shared_context: Optional[Dict[str, Any]] = None,
        max_parallel: int = 4,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Execute multiple workflows with a shared context"""
        return self._executor_component.execute_workflows_with_shared_context(
            workflows, shared_context, max_parallel, max_retries
        )
