"""
Batch Processing API

API endpoints for batch job submission, tracking, and result retrieval.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uvicorn
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.batch import (
    BatchProcessor,
    BatchJob,
    BatchJobStatus,
    BatchJobType,
)

# Initialize FastAPI app
app = FastAPI(
    title="AutonomAI Batch Processing API",
    description="API for batch processing and progress monitoring",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global batch processor instance
_batch_processor = None


def get_batch_processor() -> BatchProcessor:
    """Get or create batch processor instance"""
    global _batch_processor
    if _batch_processor is None:
        storage_path = Path(os.getenv("BATCH_STORAGE_PATH", "./data/batch_jobs"))
        _batch_processor = BatchProcessor(storage_path=storage_path)
    return _batch_processor


# Pydantic models for API requests/responses

class BatchJobSubmitRequest(BaseModel):
    """Request model for submitting a batch job"""
    job_type: str = Field(..., description="Type of batch job: failure_optimization, workflow_batch, validation_batch, or custom")
    tasks: List[Dict[str, Any]] = Field(..., description="List of task data to process")
    created_by: Optional[str] = Field(None, description="User or system creating the job")
    priority: int = Field(0, description="Job priority (higher = more urgent)")
    max_workers: int = Field(4, description="Maximum parallel workers", ge=1, le=16)
    retry_failed: bool = Field(True, description="Whether to retry failed tasks")
    max_retries: int = Field(3, description="Maximum retries per task", ge=0, le=10)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchJobResponse(BaseModel):
    """Response model for batch job operations"""
    job_id: str
    job_type: str
    status: str
    tasks_count: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_by: Optional[str] = None
    priority: int
    max_workers: int
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


class BatchJobResultsResponse(BaseModel):
    """Response model for job results"""
    job_id: str
    status: str
    results: List[Dict[str, Any]]
    progress: Optional[Dict[str, Any]] = None


class BatchJobListResponse(BaseModel):
    """Response model for listing jobs"""
    jobs: List[Dict[str, Any]]
    total: int


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AutonomAI Batch Processing API",
        "version": "1.0.0",
        "description": "API for batch processing and progress monitoring",
        "endpoints": {
            "submit": "POST /batch/submit - Submit a new batch job",
            "status": "GET /batch/{job_id}/status - Get job status and progress",
            "results": "GET /batch/{job_id}/results - Get job results",
            "cancel": "POST /batch/{job_id}/cancel - Cancel a running job",
            "list": "GET /batch/jobs - List batch jobs",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        processor = get_batch_processor()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "batch_processor": "operational",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.post("/batch/submit", response_model=BatchJobResponse)
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
                detail=f"Invalid job type: {request.job_type}. Must be one of: {[t.value for t in BatchJobType]}",
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
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            created_by=job.created_by,
            priority=job.priority,
            max_workers=job.max_workers,
            message="Batch job submitted successfully",
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit batch job: {str(e)}")


@app.get("/batch/{job_id}/status", response_model=BatchJobStatusResponse)
async def get_job_status(
    job_id: str,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """
    Get status and progress of a batch job
    
    Returns real-time progress information including:
    - Total, completed, failed, running, and pending tasks
    - Progress percentage
    - Estimated time remaining
    """
    status = processor.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return BatchJobStatusResponse(**status)


@app.get("/batch/{job_id}/results", response_model=BatchJobResultsResponse)
async def get_job_results(
    job_id: str,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """
    Get results of a completed batch job
    
    Returns detailed results for each task including:
    - Task success/failure status
    - Task output/results
    - Error messages for failed tasks
    - Execution duration
    """
    results = processor.get_job_results(job_id)
    
    if not results:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return BatchJobResultsResponse(**results)


@app.post("/batch/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """
    Cancel a running or queued batch job
    
    Terminates all running tasks and prevents pending tasks from executing.
    """
    success = processor.cancel_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to cancel job {job_id}. Job may not exist or is already completed.",
        )
    
    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Batch job cancelled successfully",
    }


@app.get("/batch/jobs", response_model=BatchJobListResponse)
async def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 100,
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """
    List batch jobs with optional filtering
    
    Query parameters:
    - status: Filter by job status (pending, queued, running, completed, failed, cancelled, partial)
    - job_type: Filter by job type (failure_optimization, workflow_batch, validation_batch, custom)
    - limit: Maximum number of jobs to return (default: 100)
    """
    # Validate filters
    status_filter = None
    if status:
        try:
            status_filter = BatchJobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: {[s.value for s in BatchJobStatus]}",
            )
    
    job_type_filter = None
    if job_type:
        try:
            job_type_filter = BatchJobType(job_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job type: {job_type}. Must be one of: {[t.value for t in BatchJobType]}",
            )
    
    # List jobs
    jobs = processor.list_jobs(
        status=status_filter,
        job_type=job_type_filter,
        limit=limit,
    )
    
    return BatchJobListResponse(
        jobs=jobs,
        total=len(jobs),
    )


@app.get("/batch/stats")
async def get_batch_stats(
    processor: BatchProcessor = Depends(get_batch_processor),
):
    """
    Get overall batch processing statistics
    
    Returns aggregated statistics across all jobs.
    """
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Batch Processing API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "api_batch:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
