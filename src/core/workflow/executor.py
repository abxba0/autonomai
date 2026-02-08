"""
Workflow Step Executor

Handles execution of individual workflow steps and batch workflow operations.
"""

from typing import Optional, Dict, Any, List
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...models.workflow import (
    WorkflowPlan,
    WorkflowStep,
    StepStatus,
    StepType,
)
from .instruction_manager import WorkflowInstructionManager, swap_instructions_temporarily
from .control_flow import ControlFlowEngine


class WorkflowExecutor:
    """
    Executes workflow steps and manages batch workflow operations

    Responsibilities:
    - Execute individual steps with LLM
    - Dispatch steps by type (standard, conditional, loop, subworkflow)
    - Batch and shared-context workflow execution
    """

    def __init__(
        self,
        workflow_instruction_manager: WorkflowInstructionManager,
        executor_model,
        base_instruction_manager,
        active_workflows: Dict[str, WorkflowPlan],
        control_flow: ControlFlowEngine,
        execute_workflow_fn=None,
    ):
        self.workflow_instruction_manager = workflow_instruction_manager
        self.executor = executor_model
        self.base_instruction_manager = base_instruction_manager
        self.active_workflows = active_workflows
        self.control_flow = control_flow
        self._execute_workflow = execute_workflow_fn

    def execute_step(
        self, workflow_id: str, step_id: str, inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step using the Executor
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the step to execute
            inputs: Optional inputs to override step's default inputs
            
        Returns:
            Dict with execution results
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
                "error": f"Step {step_id} not found in workflow",
            }

        # Check dependencies
        for dep_id in step.dependencies:
            dep_step = workflow.get_step_by_id(dep_id)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return {
                    "success": False,
                    "error": f"Dependency {dep_id} not completed",
                }

        # Update step status
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()

        # Merge inputs
        step_inputs = {**step.inputs, **(inputs or {})}

        # Construct execution prompt
        execution_prompt = f"""
Execute the following workflow step:

STEP: {step.name}
DESCRIPTION: {step.description}
INPUTS: {json.dumps(step_inputs, indent=2)}

Follow the actor instructions to execute this step precisely.
Return your results in JSON format with status and outputs.

Expected format:
{{
  "status": "completed" or "failed",
  "outputs": {{...}},
  "error": "error message if failed"
}}
"""

        try:
            # Get actor instructions
            actor_instructions = self.workflow_instruction_manager.get_actor_instructions()

            # Execute step with temporarily swapped instructions
            def execute_step_logic():
                result = self.executor.model.invoke(execution_prompt)
                if hasattr(result, "content"):
                    return result.content
                return str(result)
            
            response = swap_instructions_temporarily(
                self.base_instruction_manager,
                actor_instructions,
                execute_step_logic
            )

            # Parse result
            result_data = self._extract_json_from_response(response)
            
            # If parsing failed, treat as execution failure
            if result_data is None:
                step.status = StepStatus.FAILED
                step.error_message = "Failed to parse execution result as JSON"
                success = False
                result_data = {
                    "status": "failed",
                    "error": "Failed to parse execution result as JSON"
                }
            elif result_data.get("status") == "completed":
                step.status = StepStatus.COMPLETED
                step.outputs = result_data.get("outputs", {})
                step.completed_at = datetime.now()
                success = True
            else:
                step.status = StepStatus.FAILED
                step.error_message = result_data.get("error", "Unknown error")
                success = False

            # Log execution
            step.execution_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "status": step.status.value,
                    "result": result_data,
                }
            )

            return {
                "success": success,
                "step_id": step_id,
                "status": step.status.value,
                "outputs": step.outputs,
                "error": step.error_message,
            }

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            step.execution_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": str(e),
                }
            )

            return {
                "success": False,
                "step_id": step_id,
                "status": "failed",
                "error": str(e),
            }

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks"""
        response = response.strip()

        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    def execute_step_by_type(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a step based on its type
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the step
            context: Execution context
            
        Returns:
            Dict with execution results
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

        # Route to appropriate execution method based on step type
        if step.step_type == StepType.CONDITIONAL:
            return self.control_flow.execute_conditional_step(workflow_id, step_id, context)
        elif step.step_type == StepType.LOOP:
            return self.control_flow.execute_loop_step(workflow_id, step_id, context)
        elif step.step_type == StepType.SUBWORKFLOW:
            return self.control_flow.execute_subworkflow_step(workflow_id, step_id, context)
        else:  # StepType.STANDARD
            return self.execute_step(workflow_id, step_id, step.inputs)

    def execute_workflows_batch(
        self,
        workflows: List[Dict[str, Any]],
        max_parallel: int = 4,
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple workflows in parallel (batch processing)
        
        This enables workflow-level batch operations with parallelism.
        Each workflow is executed independently, and results are collected.
        
        Args:
            workflows: List of workflow specifications, each with 'goal' and optional 'context'
            max_parallel: Maximum number of workflows to execute in parallel
            max_retries: Maximum retries per workflow
            
        Returns:
            List of workflow execution results
        """
        results = []
        
        def execute_single_workflow(workflow_spec: Dict[str, Any], index: int) -> Dict[str, Any]:
            """Execute a single workflow with error handling"""
            try:
                goal = workflow_spec.get("goal", "")
                context = workflow_spec.get("context")
                
                result = self._execute_workflow(
                    goal=goal,
                    context=context,
                    max_retries=max_retries,
                )
                
                return {
                    "index": index,
                    "success": result.get("status") == "completed",
                    "result": result,
                    "error": None,
                }
            except Exception as e:
                return {
                    "index": index,
                    "success": False,
                    "result": None,
                    "error": str(e),
                }
        
        # Execute workflows in parallel
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all workflows
            future_to_index = {
                executor.submit(execute_single_workflow, wf, i): i
                for i, wf in enumerate(workflows)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    index = future_to_index[future]
                    results.append({
                        "index": index,
                        "success": False,
                        "result": None,
                        "error": str(e),
                    })
        
        # Sort by original index
        results.sort(key=lambda x: x["index"])
        
        return results

    def execute_workflows_with_shared_context(
        self,
        workflows: List[Dict[str, Any]],
        shared_context: Optional[Dict[str, Any]] = None,
        max_parallel: int = 4,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Execute multiple workflows with a shared context
        
        Useful for batch operations that need to share data or state.
        Results from earlier workflows can inform later ones.
        
        Args:
            workflows: List of workflow specifications
            shared_context: Context shared across all workflows
            max_parallel: Maximum parallel workflows
            max_retries: Maximum retries per workflow
            
        Returns:
            Dict with batch execution results and shared context updates
        """
        shared_context = shared_context or {}
        results = []
        
        for i, workflow_spec in enumerate(workflows):
            goal = workflow_spec.get("goal", "")
            workflow_context = workflow_spec.get("context", {})
            
            # Merge shared context with workflow-specific context
            merged_context = {**shared_context, **workflow_context}
            
            try:
                result = self._execute_workflow(
                    goal=goal,
                    context=merged_context,
                    max_retries=max_retries,
                )
                
                # Update shared context with workflow outputs
                if result.get("status") == "completed":
                    workflow_outputs = {}
                    for step_result in result.get("results", []):
                        if step_result.get("outputs"):
                            workflow_outputs.update(step_result["outputs"])
                    
                    shared_context[f"workflow_{i}_outputs"] = workflow_outputs
                
                results.append({
                    "index": i,
                    "success": result.get("status") == "completed",
                    "result": result,
                    "error": None,
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "result": None,
                    "error": str(e),
                })
        
        return {
            "results": results,
            "shared_context": shared_context,
            "total": len(workflows),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
        }
