"""
Celery Tasks for Batch Processing

Defines asynchronous tasks for batch operations using Celery.
"""

from typing import Dict, Any, List
import time
from datetime import datetime
from celery import group, chord
from celery.utils.log import get_task_logger

from .celery_config import celery_app
from .models import TaskResult, BatchJobStatus, BatchJobType
from ..models.config import SystemConfig, FailureEntry
from .. import SelfOptimizingSystem

logger = get_task_logger(__name__)


def get_system_instance() -> SelfOptimizingSystem:
    """Get or create a SelfOptimizingSystem instance for task processing"""
    # Each worker process will have its own instance
    if not hasattr(get_system_instance, "_instance"):
        config = SystemConfig(
            enable_auto_optimization=True,
        )
        get_system_instance._instance = SelfOptimizingSystem(config)
    return get_system_instance._instance


@celery_app.task(bind=True, name="src.batch.tasks.process_single_task")
def process_single_task(self, task_id: str, task_data: Dict[str, Any], task_type: str) -> Dict[str, Any]:
    """
    Process a single task from a batch job
    
    Args:
        task_id: Unique identifier for the task
        task_data: Task data to process
        task_type: Type of task (failure_optimization, workflow_batch, etc.)
    
    Returns:
        Dict with task result
    """
    started_at = datetime.now()
    logger.info(f"Processing task {task_id} of type {task_type}")
    
    try:
        system = get_system_instance()
        result = None
        
        if task_type == "failure_optimization":
            # Process a failure for optimization
            failure = FailureEntry(
                trigger_type=task_data.get("trigger_type", "batch_optimization"),
                failure_description=task_data.get("failure_description", ""),
                user_query=task_data.get("user_query", ""),
                last_model_output=task_data.get("last_model_output", ""),
                validation_errors=task_data.get("validation_errors"),
                severity=task_data.get("severity", "moderate"),
            )
            
            optimization_result = system.critic_model.optimize(failure)
            result = {
                "success": optimization_result.get("success", False),
                "optimization_result": optimization_result,
            }
            
        elif task_type == "workflow_batch":
            # Execute a workflow
            workflow_result = system.execute_workflow(
                goal=task_data.get("goal", ""),
                context=task_data.get("context"),
                max_retries=task_data.get("max_retries", 3),
            )
            result = {
                "success": workflow_result.get("status") == "completed",
                "workflow_result": workflow_result,
            }
            
        elif task_type == "validation_batch":
            # Validate an output
            output = task_data.get("output", "")
            validation_passed = system.validate_output(output)
            result = {
                "success": validation_passed,
                "validation_passed": validation_passed,
                "output": output,
            }
            
        else:
            # Custom task processing
            result = {
                "success": True,
                "task_data": task_data,
                "message": "Custom task processed",
            }
        
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        
        logger.info(f"Task {task_id} completed successfully in {duration:.2f}s")
        
        return {
            "task_id": task_id,
            "success": True,
            "result": result,
            "error": None,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": duration,
        }
        
    except Exception as e:
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        
        return {
            "task_id": task_id,
            "success": False,
            "result": None,
            "error": str(e),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": duration,
        }


@celery_app.task(name="src.batch.tasks.finalize_batch_job")
def finalize_batch_job(results: List[Dict[str, Any]], job_id: str) -> Dict[str, Any]:
    """
    Finalize a batch job after all tasks complete
    
    Args:
        results: List of task results
        job_id: Batch job ID
    
    Returns:
        Dict with finalization status
    """
    logger.info(f"Finalizing batch job {job_id}")
    
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    
    status = "completed" if failed == 0 else ("partial" if successful > 0 else "failed")
    
    return {
        "job_id": job_id,
        "status": status,
        "total_tasks": len(results),
        "successful_tasks": successful,
        "failed_tasks": failed,
        "results": results,
    }


@celery_app.task(bind=True, name="src.batch.tasks.process_failure_batch")
def process_failure_batch(self, job_id: str, failures: List[Dict[str, Any]], max_workers: int = 4) -> str:
    """
    Process multiple failures in a batch for optimization
    
    Args:
        job_id: Batch job ID
        failures: List of failure data to process
        max_workers: Maximum parallel workers
    
    Returns:
        Celery group task ID for tracking
    """
    logger.info(f"Starting failure batch {job_id} with {len(failures)} failures")
    
    # Create tasks for each failure
    tasks = [
        process_single_task.s(
            task_id=f"{job_id}_task_{i}",
            task_data=failure,
            task_type="failure_optimization"
        )
        for i, failure in enumerate(failures)
    ]
    
    # Execute tasks in parallel with a finalizer
    callback = finalize_batch_job.s(job_id=job_id)
    job = chord(tasks)(callback)
    
    return job.id


@celery_app.task(bind=True, name="src.batch.tasks.process_workflow_batch")
def process_workflow_batch(self, job_id: str, workflows: List[Dict[str, Any]], max_workers: int = 4) -> str:
    """
    Process multiple workflows in a batch
    
    Args:
        job_id: Batch job ID
        workflows: List of workflow specifications
        max_workers: Maximum parallel workers
    
    Returns:
        Celery group task ID for tracking
    """
    logger.info(f"Starting workflow batch {job_id} with {len(workflows)} workflows")
    
    # Create tasks for each workflow
    tasks = [
        process_single_task.s(
            task_id=f"{job_id}_workflow_{i}",
            task_data=workflow,
            task_type="workflow_batch"
        )
        for i, workflow in enumerate(workflows)
    ]
    
    # Execute tasks in parallel with a finalizer
    callback = finalize_batch_job.s(job_id=job_id)
    job = chord(tasks)(callback)
    
    return job.id


@celery_app.task(bind=True, name="src.batch.tasks.process_validation_batch")
def process_validation_batch(self, job_id: str, outputs: List[Dict[str, Any]], max_workers: int = 4) -> str:
    """
    Validate multiple outputs in a batch
    
    Args:
        job_id: Batch job ID
        outputs: List of outputs to validate
        max_workers: Maximum parallel workers
    
    Returns:
        Celery group task ID for tracking
    """
    logger.info(f"Starting validation batch {job_id} with {len(outputs)} outputs")
    
    # Create tasks for each validation
    tasks = [
        process_single_task.s(
            task_id=f"{job_id}_validation_{i}",
            task_data=output,
            task_type="validation_batch"
        )
        for i, output in enumerate(outputs)
    ]
    
    # Execute tasks in parallel with a finalizer
    callback = finalize_batch_job.s(job_id=job_id)
    job = chord(tasks)(callback)
    
    return job.id


@celery_app.task(bind=True, name="src.batch.tasks.cancel_batch_job")
def cancel_batch_job(self, job_id: str) -> Dict[str, Any]:
    """
    Cancel a running batch job
    
    Args:
        job_id: Batch job ID to cancel
    
    Returns:
        Dict with cancellation status
    """
    logger.info(f"Cancelling batch job {job_id}")
    
    # Revoke all tasks associated with this job
    celery_app.control.revoke(job_id, terminate=True, signal="SIGKILL")
    
    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Batch job cancelled successfully",
    }
