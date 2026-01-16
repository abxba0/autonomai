"""
Batch Processing Models

Data models for batch job processing and progress monitoring.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


class BatchJobStatus(Enum):
    """Status of a batch job"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"  # Some tasks completed, some failed


class BatchJobType(Enum):
    """Type of batch job"""
    FAILURE_OPTIMIZATION = "failure_optimization"  # Optimize multiple failures
    WORKFLOW_BATCH = "workflow_batch"  # Execute multiple workflows
    VALIDATION_BATCH = "validation_batch"  # Validate multiple outputs
    CUSTOM = "custom"  # Custom batch processing


@dataclass
class TaskResult:
    """Result of a single task in a batch job"""
    task_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class BatchJobProgress:
    """Progress information for a batch job"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    pending_tasks: int
    progress_percent: float
    estimated_time_remaining_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "running_tasks": self.running_tasks,
            "pending_tasks": self.pending_tasks,
            "progress_percent": self.progress_percent,
            "estimated_time_remaining_seconds": self.estimated_time_remaining_seconds,
        }


@dataclass
class BatchJob:
    """
    Represents a batch processing job
    
    Attributes:
        job_id: Unique identifier for the job
        job_type: Type of batch job
        status: Current job status
        tasks: List of task data to process
        results: Results of completed tasks
        progress: Progress information
        created_at: Timestamp when job was created
        started_at: Timestamp when job started processing
        completed_at: Timestamp when job completed
        created_by: User or system that created the job
        priority: Job priority (higher = more urgent)
        max_workers: Maximum number of parallel workers
        retry_failed: Whether to retry failed tasks
        max_retries: Maximum number of retries per task
        metadata: Additional metadata for the job
    """
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: BatchJobType = BatchJobType.CUSTOM
    status: BatchJobStatus = BatchJobStatus.PENDING
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    results: List[TaskResult] = field(default_factory=list)
    progress: Optional[BatchJobProgress] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    priority: int = 0
    max_workers: int = 4
    retry_failed: bool = True
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def update_progress(self) -> BatchJobProgress:
        """Calculate and update progress information"""
        total = len(self.tasks)
        completed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        processed = len(self.results)
        running = min(self.max_workers, total - processed) if self.status == BatchJobStatus.RUNNING else 0
        pending = total - processed - running
        
        progress_percent = (processed / total * 100) if total > 0 else 0
        
        # Estimate time remaining based on completed tasks
        estimated_time = None
        if completed > 0 and self.started_at:
            elapsed = (datetime.now() - self.started_at).total_seconds()
            avg_time_per_task = elapsed / completed
            remaining_tasks = total - processed
            estimated_time = avg_time_per_task * remaining_tasks
        
        self.progress = BatchJobProgress(
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            running_tasks=running,
            pending_tasks=pending,
            progress_percent=progress_percent,
            estimated_time_remaining_seconds=estimated_time,
        )
        
        return self.progress
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "tasks_count": len(self.tasks),
            "results": [r.to_dict() for r in self.results],
            "progress": self.progress.to_dict() if self.progress else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "priority": self.priority,
            "max_workers": self.max_workers,
            "retry_failed": self.retry_failed,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchJob":
        """Create from dictionary"""
        job = cls(
            job_id=data.get("job_id", str(uuid.uuid4())),
            job_type=BatchJobType(data.get("job_type", "custom")),
            status=BatchJobStatus(data.get("status", "pending")),
            tasks=data.get("tasks", []),
            created_by=data.get("created_by"),
            priority=data.get("priority", 0),
            max_workers=data.get("max_workers", 4),
            retry_failed=data.get("retry_failed", True),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
            error_message=data.get("error_message"),
        )
        
        # Parse timestamps
        if data.get("created_at"):
            job.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            job.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            job.completed_at = datetime.fromisoformat(data["completed_at"])
        
        # Parse results
        if data.get("results"):
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
                for r in data["results"]
            ]
        
        return job
