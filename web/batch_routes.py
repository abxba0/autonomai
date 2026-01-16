"""
Batch Processing Routes for API v2

Integration of batch processing endpoints into the main API v2.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

try:
    # Try relative import first
    from ..src.batch import (
        BatchProcessor,
        BatchJob,
        BatchJobStatus,
        BatchJobType,
    )
except ImportError:
    # Fallback to absolute import for standalone execution
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from src.batch import (
        BatchProcessor,
        BatchJob,
        BatchJobStatus,
        BatchJobType,
    )

# Create router
router = APIRouter(prefix="/batch", tags=["batch"])

# Global batch processor instance
_batch_processor = None


def get_batch_processor() -> BatchProcessor:
    """Get or create batch processor instance"""
    global _batch_processor
    if _batch_processor is None:
        storage_path = Path(os.getenv("BATCH_STORAGE_PATH", "./data/batch_jobs"))
        _batch_processor = BatchProcessor(storage_path=storage_path)
    return _batch_processor


# Pydantic models
class BatchJobSubmitRequest(BaseModel):
    """Request model for submitting a batch job"""
    job_type: str = Field(..., description="Type of batch job")
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks")
    created_by: Optional[str] = Field(None, description="User or system creating the job")
    priority: int = Field(0, description="Job priority", ge=0, le=10)
    max_workers: int = Field(4, description="Maximum parallel workers", ge=1, le=16)
    retry_failed: bool = Field(True, description="Retry failed tasks")
    max_retries: int = Field(3, description="Maximum retries per task", ge=0, le=10)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchJobResponse(BaseModel):
    """Response model for batch job operations"""
    job_id: str
    job_type: str
    status: str
    tasks_count: int
    created_at: str
    message: Optional[str] = None


class BatchJobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    job_type: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


# Routes

@router.post("/submit", response_model=BatchJobResponse)
async def submit_batch_job(
    request: BatchJobSubmitRequest,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """
    Submit a new batch processing job
    
    Job types:
    - failure_optimization: Optimize multiple failures in batch
    - workflow_batch: Execute multiple workflows in parallel
    - validation_batch: Validate multiple outputs
    - custom: Custom batch processing
    """
    try:
        # Validate job type
        try:
            job_type_enum = BatchJobType(request.job_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job type: {request.job_type}",
            )
        
        # Submit job
        job = processor.submit_batch_job(
            job_type=job_type_enum,
            tasks=request.tasks,
            created_by=request.created_by,
            priority=request.priority,
            max_workers=request.max_workers,
            retry_failed=request.retry_failed,
            max_retries=request.max_retries,
            metadata=request.metadata,
        )
        
        return BatchJobResponse(
            job_id=job.job_id,
            job_type=job.job_type.value,
            status=job.status.value,
            tasks_count=len(job.tasks),
            created_at=job.created_at.isoformat(),
            message="Batch job submitted successfully",
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit batch job: {str(e)}")


@router.get("/{job_id}/status", response_model=BatchJobStatusResponse)
async def get_job_status(
    job_id: str,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """Get status and progress of a batch job"""
    status = processor.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return BatchJobStatusResponse(**status)


@router.get("/{job_id}/results")
async def get_job_results(
    job_id: str,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """Get results of a completed batch job"""
    results = processor.get_job_results(job_id)
    
    if not results:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return results


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """Cancel a running or queued batch job"""
    success = processor.cancel_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to cancel job {job_id}",
        )
    
    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Batch job cancelled successfully",
    }


@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 100,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """List batch jobs with optional filtering"""
    # Validate filters
    status_filter = None
    if status:
        try:
            status_filter = BatchJobStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    job_type_filter = None
    if job_type:
        try:
            job_type_filter = BatchJobType(job_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid job type: {job_type}")
    
    # List jobs
    jobs = processor.list_jobs(
        status=status_filter,
        job_type=job_type_filter,
        limit=limit,
    )
    
    return {
        "jobs": jobs,
        "total": len(jobs),
    }


@router.get("/stats")
async def get_batch_stats(
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """Get overall batch processing statistics"""
    all_jobs = processor.list_jobs(limit=1000)
    
    stats = {
        "total_jobs": len(all_jobs),
        "by_status": {},
        "by_type": {},
    }
    
    for job in all_jobs:
        status = job["status"]
        job_type = job["job_type"]
        
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        stats["by_type"][job_type] = stats["by_type"].get(job_type, 0) + 1
    
    return stats
