"""
Batch Processor for Managing Batch Jobs

Provides high-level interface for batch job submission, tracking, and management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from pathlib import Path

from .models import BatchJob, BatchJobStatus, BatchJobType, TaskResult
from .celery_config import celery_app
from .tasks import (
    process_failure_batch,
    process_workflow_batch,
    process_validation_batch,
    process_single_task,
    cancel_batch_job,
)

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    High-level batch processor for managing batch jobs
    
    Provides:
    - Job submission and tracking
    - Progress monitoring
    - Result retrieval
    - Fault tolerance and retry logic
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize batch processor
        
        Args:
            storage_path: Path to store job metadata (optional)
        """
        self.storage_path = storage_path or Path("./data/batch_jobs")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of active jobs
        self._jobs_cache: Dict[str, BatchJob] = {}
        
        # Load existing jobs from storage
        self._load_jobs()
    
    def _load_jobs(self):
        """Load jobs from storage"""
        try:
            for job_file in self.storage_path.glob("*.json"):
                with open(job_file, "r") as f:
                    job_data = json.load(f)
                    job = BatchJob.from_dict(job_data)
                    self._jobs_cache[job.job_id] = job
            logger.info(f"Loaded {len(self._jobs_cache)} jobs from storage")
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
    
    def _save_job(self, job: BatchJob):
        """Save job to storage"""
        try:
            job_file = self.storage_path / f"{job.job_id}.json"
            with open(job_file, "w") as f:
                json.dump(job.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving job {job.job_id}: {e}")
    
    def submit_batch_job(
        self,
        job_type: BatchJobType,
        tasks: List[Dict[str, Any]],
        created_by: Optional[str] = None,
        priority: int = 0,
        max_workers: int = 4,
        retry_failed: bool = True,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BatchJob:
        """
        Submit a new batch job
        
        Args:
            job_type: Type of batch job
            tasks: List of task data to process
            created_by: User or system creating the job
            priority: Job priority (higher = more urgent)
            max_workers: Maximum parallel workers
            retry_failed: Whether to retry failed tasks
            max_retries: Maximum retries per task
            metadata: Additional metadata
        
        Returns:
            BatchJob instance
        """
        job = BatchJob(
            job_type=job_type,
            tasks=tasks,
            created_by=created_by,
            priority=priority,
            max_workers=max_workers,
            retry_failed=retry_failed,
            max_retries=max_retries,
            metadata=metadata or {},
        )
        
        # Update status and start time
        job.status = BatchJobStatus.QUEUED
        job.update_progress()
        
        # Save job
        self._jobs_cache[job.job_id] = job
        self._save_job(job)
        
        # Submit to Celery based on job type
        try:
            if job_type == BatchJobType.FAILURE_OPTIMIZATION:
                celery_result = process_failure_batch.apply_async(
                    args=[job.job_id, tasks, max_workers],
                    priority=priority,
                )
            elif job_type == BatchJobType.WORKFLOW_BATCH:
                celery_result = process_workflow_batch.apply_async(
                    args=[job.job_id, tasks, max_workers],
                    priority=priority,
                )
            elif job_type == BatchJobType.VALIDATION_BATCH:
                celery_result = process_validation_batch.apply_async(
                    args=[job.job_id, tasks, max_workers],
                    priority=priority,
                )
            else:
                # Custom processing
                celery_result = None
                job.status = BatchJobStatus.PENDING
            
            # Store Celery task ID in metadata
            if celery_result:
                job.metadata["celery_task_id"] = celery_result.id
                job.status = BatchJobStatus.RUNNING
                job.started_at = datetime.now()
                self._save_job(job)
            
            logger.info(f"Submitted batch job {job.job_id} with {len(tasks)} tasks")
            
        except Exception as e:
            logger.warning(f"Celery not available for job {job.job_id}: {e}")
            # Keep job in QUEUED status if Celery is not available
            # This allows the job to be picked up when Celery becomes available
            job.status = BatchJobStatus.QUEUED
            job.error_message = f"Celery unavailable: {str(e)}"
            self._save_job(job)
        
        return job
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a batch job
        
        Args:
            job_id: Job ID to query
        
        Returns:
            Dict with job status and progress, or None if not found
        """
        job = self._jobs_cache.get(job_id)
        if not job:
            # Try loading from storage
            job_file = self.storage_path / f"{job_id}.json"
            if job_file.exists():
                with open(job_file, "r") as f:
                    job_data = json.load(f)
                    job = BatchJob.from_dict(job_data)
                    self._jobs_cache[job_id] = job
            else:
                return None
        
        # Update progress from Celery if still running
        if job.status == BatchJobStatus.RUNNING:
            self._update_job_from_celery(job)
        
        job.update_progress()
        self._save_job(job)
        
        return {
            "job_id": job.job_id,
            "job_type": job.job_type.value,
            "status": job.status.value,
            "progress": job.progress.to_dict() if job.progress else None,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }
    
    def _update_job_from_celery(self, job: BatchJob):
        """Update job status from Celery task results"""
        try:
            celery_task_id = job.metadata.get("celery_task_id")
            if not celery_task_id:
                return
            
            # Get task result from Celery
            from celery.result import AsyncResult
            result = AsyncResult(celery_task_id, app=celery_app)
            
            if result.ready():
                # Task completed
                if result.successful():
                    result_data = result.get()
                    
                    # Map status string to enum, default to COMPLETED if invalid
                    status_str = result_data.get("status", "completed")
                    try:
                        job.status = BatchJobStatus(status_str)
                    except ValueError:
                        logger.warning(f"Invalid status '{status_str}' from Celery, defaulting to COMPLETED")
                        job.status = BatchJobStatus.COMPLETED
                    
                    job.completed_at = datetime.now()
                    
                    # Add task results
                    if "results" in result_data:
                        job.results = [
                            TaskResult(
                                task_id=r["task_id"],
                                success=r["success"],
                                result=r.get("result"),
                                error=r.get("error"),
                                started_at=datetime.fromisoformat(r["started_at"]) if r.get("started_at") else None,
                                completed_at=datetime.fromisoformat(r["completed_at"]) if r.get("completed_at") else None,
                                duration_seconds=r.get("duration_seconds"),
                            )
                            for r in result_data["results"]
                        ]
                else:
                    # Task failed
                    job.status = BatchJobStatus.FAILED
                    job.completed_at = datetime.now()
                    job.error_message = str(result.info)
            
        except Exception as e:
            logger.error(f"Error updating job {job.job_id} from Celery: {e}")
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results of a completed batch job
        
        Args:
            job_id: Job ID to query
        
        Returns:
            Dict with job results, or None if not found
        """
        job = self._jobs_cache.get(job_id)
        if not job:
            # Try loading from storage
            job_file = self.storage_path / f"{job_id}.json"
            if job_file.exists():
                with open(job_file, "r") as f:
                    job_data = json.load(f)
                    job = BatchJob.from_dict(job_data)
                    self._jobs_cache[job_id] = job
            else:
                return None
        
        # Update from Celery if needed
        if job.status == BatchJobStatus.RUNNING:
            self._update_job_from_celery(job)
            self._save_job(job)
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "results": [r.to_dict() for r in job.results],
            "progress": job.progress.to_dict() if job.progress else None,
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running batch job
        
        Args:
            job_id: Job ID to cancel
        
        Returns:
            True if cancelled successfully
        """
        job = self._jobs_cache.get(job_id)
        if not job:
            return False
        
        if job.status not in [BatchJobStatus.RUNNING, BatchJobStatus.QUEUED]:
            return False
        
        try:
            # Cancel Celery task
            celery_task_id = job.metadata.get("celery_task_id")
            if celery_task_id:
                cancel_batch_job.apply_async(args=[celery_task_id])
            
            # Update job status
            job.status = BatchJobStatus.CANCELLED
            job.completed_at = datetime.now()
            self._save_job(job)
            
            logger.info(f"Cancelled batch job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def list_jobs(
        self,
        status: Optional[BatchJobStatus] = None,
        job_type: Optional[BatchJobType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List batch jobs with optional filtering
        
        Args:
            status: Filter by job status
            job_type: Filter by job type
            limit: Maximum number of jobs to return
        
        Returns:
            List of job summaries
        """
        jobs = list(self._jobs_cache.values())
        
        # Apply filters
        if status:
            jobs = [j for j in jobs if j.status == status]
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        # Limit results
        jobs = jobs[:limit]
        
        return [
            {
                "job_id": j.job_id,
                "job_type": j.job_type.value,
                "status": j.status.value,
                "tasks_count": len(j.tasks),
                "created_at": j.created_at.isoformat(),
                "progress": j.progress.to_dict() if j.progress else None,
            }
            for j in jobs
        ]
