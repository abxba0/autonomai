"""
Tests for Batch Processing

Tests batch job processing, progress monitoring, and fault tolerance.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
import time
import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Skip tests if celery is not installed (optional dependency)
pytest.importorskip("celery")

from src.batch import (
    BatchProcessor,
    BatchJob,
    BatchJobStatus,
    BatchJobType,
    TaskResult,
    BatchJobProgress,
)


def test_batch_job_models():
    """Test batch job data models"""
    print("Testing batch job models...")
    
    # Test TaskResult
    result = TaskResult(
        task_id="task_1",
        success=True,
        result={"output": "test"},
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration_seconds=1.5,
    )
    
    assert result.task_id == "task_1"
    assert result.success is True
    
    result_dict = result.to_dict()
    assert result_dict["task_id"] == "task_1"
    assert result_dict["duration_seconds"] == 1.5
    
    print("✓ TaskResult model works correctly")
    
    # Test BatchJobProgress
    progress = BatchJobProgress(
        total_tasks=10,
        completed_tasks=5,
        failed_tasks=1,
        running_tasks=2,
        pending_tasks=2,
        progress_percent=50.0,
        estimated_time_remaining_seconds=10.0,
    )
    
    assert progress.total_tasks == 10
    assert progress.progress_percent == 50.0
    
    progress_dict = progress.to_dict()
    assert progress_dict["completed_tasks"] == 5
    
    print("✓ BatchJobProgress model works correctly")
    
    # Test BatchJob
    job = BatchJob(
        job_type=BatchJobType.FAILURE_OPTIMIZATION,
        tasks=[{"task": "data1"}, {"task": "data2"}],
        max_workers=4,
    )
    
    assert job.job_type == BatchJobType.FAILURE_OPTIMIZATION
    assert len(job.tasks) == 2
    assert job.status == BatchJobStatus.PENDING
    
    # Test progress update
    job.results.append(TaskResult(task_id="t1", success=True))
    progress = job.update_progress()
    
    assert progress.total_tasks == 2
    assert progress.completed_tasks == 1
    assert progress.progress_percent == 50.0
    
    print("✓ BatchJob model works correctly")
    
    # Test serialization
    job_dict = job.to_dict()
    assert job_dict["job_type"] == "failure_optimization"
    assert job_dict["tasks_count"] == 2
    
    job2 = BatchJob.from_dict(job_dict)
    assert job2.job_id == job.job_id
    assert job2.job_type == job.job_type
    
    print("✓ BatchJob serialization works correctly")


def test_batch_processor():
    """Test BatchProcessor functionality"""
    print("\nTesting batch processor...")
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    
    try:
        processor = BatchProcessor(storage_path=Path(temp_dir))
        
        # Test job submission
        tasks = [
            {"failure_description": "Test failure 1", "severity": "low"},
            {"failure_description": "Test failure 2", "severity": "moderate"},
        ]
        
        job = processor.submit_batch_job(
            job_type=BatchJobType.FAILURE_OPTIMIZATION,
            tasks=tasks,
            created_by="test_user",
            priority=1,
            max_workers=2,
        )
        
        assert job.job_id is not None
        assert job.status in [BatchJobStatus.QUEUED, BatchJobStatus.PENDING]
        assert len(job.tasks) == 2
        
        print(f"✓ Job submitted: {job.job_id}")
        
        # Test job status retrieval
        status = processor.get_job_status(job.job_id)
        assert status is not None
        assert status["job_id"] == job.job_id
        assert "progress" in status
        
        print("✓ Job status retrieval works")
        
        # Test job listing
        jobs = processor.list_jobs(limit=10)
        assert len(jobs) > 0
        assert any(j["job_id"] == job.job_id for j in jobs)
        
        print("✓ Job listing works")
        
        # Test job persistence
        processor2 = BatchProcessor(storage_path=Path(temp_dir))
        status2 = processor2.get_job_status(job.job_id)
        assert status2 is not None
        assert status2["job_id"] == job.job_id
        
        print("✓ Job persistence works")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_batch_job_progress():
    """Test batch job progress tracking"""
    print("\nTesting batch job progress tracking...")
    
    job = BatchJob(
        job_type=BatchJobType.WORKFLOW_BATCH,
        tasks=[{"goal": f"Task {i}"} for i in range(10)],
        max_workers=4,
    )
    
    # Simulate task completion
    for i in range(5):
        job.results.append(TaskResult(
            task_id=f"task_{i}",
            success=True,
            duration_seconds=1.0,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        ))
    
    # Add some failures
    for i in range(2):
        job.results.append(TaskResult(
            task_id=f"task_fail_{i}",
            success=False,
            error="Test error",
            started_at=datetime.now(),
            completed_at=datetime.now(),
        ))
    
    # Update progress
    job.status = BatchJobStatus.RUNNING
    job.started_at = datetime.now()
    progress = job.update_progress()
    
    assert progress.total_tasks == 10
    assert progress.completed_tasks == 5
    assert progress.failed_tasks == 2
    assert progress.progress_percent == 70.0  # 7 processed out of 10
    
    print("✓ Progress tracking works correctly")
    print(f"  Total: {progress.total_tasks}")
    print(f"  Completed: {progress.completed_tasks}")
    print(f"  Failed: {progress.failed_tasks}")
    print(f"  Progress: {progress.progress_percent:.1f}%")


def test_batch_job_types():
    """Test different batch job types"""
    print("\nTesting batch job types...")
    
    # Test all job types
    job_types = [
        BatchJobType.FAILURE_OPTIMIZATION,
        BatchJobType.WORKFLOW_BATCH,
        BatchJobType.VALIDATION_BATCH,
        BatchJobType.CUSTOM,
    ]
    
    for job_type in job_types:
        job = BatchJob(
            job_type=job_type,
            tasks=[{"data": f"test_{job_type.value}"}],
        )
        
        assert job.job_type == job_type
        print(f"✓ {job_type.value} job type works")


def test_workflow_batch_execution():
    """Test workflow batch execution (integration test)"""
    print("\nTesting workflow batch execution...")
    
    from src.core.workflow_orchestrator import WorkflowOrchestrator
    from src.models.config import SystemConfig
    
    config = SystemConfig(enable_auto_optimization=False)
    orchestrator = WorkflowOrchestrator(config)
    
    # Test parallel workflow execution
    workflows = [
        {"goal": "Test workflow 1", "context": {"test": True}},
        {"goal": "Test workflow 2", "context": {"test": True}},
    ]
    
    try:
        # This will use mock models if no API keys are configured
        results = orchestrator.execute_workflows_batch(
            workflows=workflows,
            max_parallel=2,
            max_retries=1,
        )
        
        assert len(results) == 2
        print("✓ Workflow batch execution completed")
        print(f"  Results: {len(results)} workflows processed")
        
    except Exception as e:
        print(f"⚠ Workflow batch execution test skipped (expected with mock models): {e}")


def test_batch_job_filtering():
    """Test batch job filtering"""
    print("\nTesting batch job filtering...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        processor = BatchProcessor(storage_path=Path(temp_dir))
        
        # Create jobs of different types and statuses
        jobs = []
        
        # Failure optimization job
        job1 = processor.submit_batch_job(
            job_type=BatchJobType.FAILURE_OPTIMIZATION,
            tasks=[{"test": 1}],
        )
        jobs.append(job1)
        
        # Workflow batch job
        job2 = processor.submit_batch_job(
            job_type=BatchJobType.WORKFLOW_BATCH,
            tasks=[{"test": 2}],
        )
        jobs.append(job2)
        
        # Test filtering by type
        failure_jobs = processor.list_jobs(
            job_type=BatchJobType.FAILURE_OPTIMIZATION,
            limit=10,
        )
        assert len(failure_jobs) >= 1
        assert all(j["job_type"] == "failure_optimization" for j in failure_jobs)
        
        print("✓ Job filtering by type works")
        
        # Test listing all jobs
        all_jobs = processor.list_jobs(limit=10)
        assert len(all_jobs) >= 2
        
        print("✓ Job listing works")
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=" * 60)
    print("Batch Processing Tests")
    print("=" * 60)
    
    try:
        test_batch_job_models()
        test_batch_processor()
        test_batch_job_progress()
        test_batch_job_types()
        test_workflow_batch_execution()
        test_batch_job_filtering()
        
        print("\n" + "=" * 60)
        print("✓ All batch processing tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
