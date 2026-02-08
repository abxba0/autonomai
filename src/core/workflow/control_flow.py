"""
Workflow Control Flow Engine

Handles conditional branching, loops, and subworkflow execution
for the workflow orchestration system.
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from ...models.workflow import (
    WorkflowPlan,
    WorkflowStep,
    StepStatus,
    StepType,
)


class ControlFlowEngine:
    """
    Handles control flow constructs: conditionals, loops, and subworkflows

    Responsibilities:
    - Evaluate conditions safely
    - Execute conditional (if/else) steps
    - Execute loop (while, for, foreach) steps
    - Execute subworkflow steps
    """

    def __init__(self, active_workflows: Dict[str, WorkflowPlan], execute_step_by_type_fn):
        self.active_workflows = active_workflows
        self._execute_step_by_type = execute_step_by_type_fn

    def _evaluate_condition(
        self, condition: str, context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a condition expression in the given context
        
        Args:
            condition: Condition expression to evaluate
            context: Context with variables and step outputs
            
        Returns:
            Boolean result of condition evaluation
        """
        try:
            # Create safe evaluation environment with context variables
            safe_dict = {
                "__builtins__": {},
                "true": True,
                "false": False,
                "True": True,
                "False": False,
                "None": None,
            }
            safe_dict.update(context)
            
            # Evaluate the condition
            # Note: This uses eval() with restricted builtins for safety.
            # For production, consider using a safer expression parser like
            # simpleeval or ast.literal_eval for simple expressions.
            result = eval(condition, safe_dict)
            return bool(result)
        except Exception as e:
            # Log error instead of printing
            logging.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def execute_conditional_step(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a conditional step (if/else or switch/case)
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the conditional step
            context: Execution context with variables
            
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

        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        ctx = context or {}
        
        # Evaluate condition
        condition_result = self._evaluate_condition(step.condition, ctx)
        
        # Determine which branch to take
        branch_key = "true" if condition_result else "false"
        branch_steps = step.branches.get(branch_key, [])
        
        # Mark non-taken branch steps as skipped
        other_branch_key = "false" if condition_result else "true"
        other_branch_steps = step.branches.get(other_branch_key, [])
        for other_step_id in other_branch_steps:
            other_step = workflow.get_step_by_id(other_step_id)
            if other_step and other_step.status == StepStatus.PENDING:
                other_step.status = StepStatus.SKIPPED
        
        # Mark this conditional step as completed
        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.now()
        step.outputs = {
            "condition_result": condition_result,
            "branch_taken": branch_key,
            "branch_steps": branch_steps,
        }
        
        return {
            "success": True,
            "step_id": step_id,
            "status": "completed",
            "outputs": step.outputs,
        }

    def execute_loop_step(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a loop step (while, for, foreach)
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the loop step
            context: Execution context with variables
            
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

        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        ctx = context or {}
        iterations_performed = []
        
        try:
            if step.loop_type == "foreach":
                # Execute for each item in collection
                collection = step.loop_collection or []
                for i, item in enumerate(collection):
                    if step.iteration_count >= step.max_iterations:
                        break
                    
                    # Set loop variable in context
                    ctx[step.loop_variable] = item
                    ctx[f"{step.loop_variable}_index"] = i
                    
                    step.iteration_count += 1
                    iterations_performed.append({
                        "iteration": step.iteration_count,
                        "value": item,
                        "index": i,
                    })
            
            elif step.loop_type == "while":
                # Execute while condition is true
                while step.iteration_count < step.max_iterations:
                    if not self._evaluate_condition(step.condition, ctx):
                        break
                    
                    step.iteration_count += 1
                    iterations_performed.append({
                        "iteration": step.iteration_count,
                        "condition_result": True,
                    })
            
            elif step.loop_type == "for":
                # Execute for a specific range
                start = step.inputs.get("start", 0)
                end = step.inputs.get("end", 0)
                step_val = step.inputs.get("step", 1)
                
                for i in range(start, end, step_val):
                    if step.iteration_count >= step.max_iterations:
                        break
                    
                    ctx[step.loop_variable] = i
                    step.iteration_count += 1
                    iterations_performed.append({
                        "iteration": step.iteration_count,
                        "value": i,
                    })
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            step.outputs = {
                "iterations_performed": len(iterations_performed),
                "iterations": iterations_performed,
                "loop_type": step.loop_type,
            }
            
            return {
                "success": True,
                "step_id": step_id,
                "status": "completed",
                "outputs": step.outputs,
            }
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            return {
                "success": False,
                "step_id": step_id,
                "status": "failed",
                "error": str(e),
            }

    def execute_subworkflow_step(
        self, workflow_id: str, step_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a subworkflow step
        
        Args:
            workflow_id: ID of the parent workflow
            step_id: ID of the subworkflow step
            context: Execution context to pass to subworkflow
            
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

        if not step.subworkflow_plan:
            return {
                "success": False,
                "error": f"No subworkflow plan defined for step {step_id}",
            }

        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        # Register subworkflow as active
        subworkflow = step.subworkflow_plan
        self.active_workflows[subworkflow.id] = subworkflow
        
        try:
            # Execute subworkflow steps
            ctx = context or {}
            subworkflow.started_at = datetime.now()
            
            # Execute subworkflow respecting dependencies (like main workflow)
            max_subworkflow_iterations = len(subworkflow.steps) * 2 + 10
            iteration_count = 0
            
            while not subworkflow.is_complete() and iteration_count < max_subworkflow_iterations:
                iteration_count += 1
                ready_steps = subworkflow.get_ready_steps()
                
                if not ready_steps:
                    # Check if there are failures blocking progress
                    if subworkflow.has_failures():
                        failed_step = subworkflow.get_failed_steps()[0]
                        step.status = StepStatus.FAILED
                        step.error_message = f"Subworkflow step failed: {failed_step.error_message}"
                        return {
                            "success": False,
                            "step_id": step_id,
                            "status": "failed",
                            "error": step.error_message,
                        }
                    break
                
                # Execute ready steps
                for sub_step in ready_steps:
                    result = self._execute_step_by_type(subworkflow.id, sub_step.id, ctx)
                    
                    if not result["success"]:
                        step.status = StepStatus.FAILED
                        step.error_message = f"Subworkflow step failed: {result.get('error')}"
                        return result
            
            subworkflow.completed_at = datetime.now()
            
            # Collect subworkflow outputs
            subworkflow_outputs = {}
            for sub_step in subworkflow.steps:
                if sub_step.outputs:
                    subworkflow_outputs[sub_step.id] = sub_step.outputs
            
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now()
            step.outputs = {
                "subworkflow_id": subworkflow.id,
                "subworkflow_status": "completed",
                "subworkflow_outputs": subworkflow_outputs,
            }
            
            return {
                "success": True,
                "step_id": step_id,
                "status": "completed",
                "outputs": step.outputs,
            }
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            return {
                "success": False,
                "step_id": step_id,
                "status": "failed",
                "error": str(e),
            }
