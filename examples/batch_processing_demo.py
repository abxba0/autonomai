"""
Batch Processing Demo

Demonstrates batch processing capabilities with async job queuing,
progress monitoring, and result retrieval.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.batch import (
    BatchProcessor,
    BatchJobType,
    BatchJobStatus,
)
from src import SelfOptimizingSystem, SystemConfig


def demo_batch_failure_optimization():
    """Demonstrate batch optimization of multiple failures"""
    print("\n" + "=" * 60)
    print("Demo 1: Batch Failure Optimization")
    print("=" * 60)
    
    # Create batch processor
    processor = BatchProcessor(storage_path=Path("./data/batch_jobs"))
    
    # Prepare multiple failures for optimization
    failures = [
        {
            "trigger_type": "validation_failure",
            "failure_description": "Output was too short",
            "user_query": "Summarize the article",
            "last_model_output": "OK",
            "severity": "high",
        },
        {
            "trigger_type": "validation_failure",
            "failure_description": "Missing required JSON fields",
            "user_query": "Generate user profile",
            "last_model_output": '{"name": "John"}',
            "severity": "high",
        },
        {
            "trigger_type": "human_feedback",
            "failure_description": "Response was too technical",
            "user_query": "Explain quantum computing",
            "last_model_output": "Quantum superposition involves...",
            "severity": "moderate",
        },
    ]
    
    # Submit batch job
    print(f"\nSubmitting batch job with {len(failures)} failures...")
    job = processor.submit_batch_job(
        job_type=BatchJobType.FAILURE_OPTIMIZATION,
        tasks=failures,
        created_by="demo_user",
        priority=1,
        max_workers=3,
        retry_failed=True,
        max_retries=2,
        metadata={
            "source": "demo",
            "batch_name": "failure_optimization_demo",
        },
    )
    
    print(f"✓ Job submitted: {job.job_id}")
    print(f"  Status: {job.status.value}")
    print(f"  Tasks: {len(job.tasks)}")
    print(f"  Max workers: {job.max_workers}")
    
    # Monitor progress (in a real scenario, this would be done separately)
    print("\nMonitoring job progress...")
    for i in range(5):
        time.sleep(1)
        status = processor.get_job_status(job.job_id)
        
        if status:
            progress = status.get("progress")
            if progress:
                print(f"  Progress: {progress['progress_percent']:.1f}% "
                      f"({progress['completed_tasks']}/{progress['total_tasks']} completed, "
                      f"{progress['failed_tasks']} failed)")
            
            if status["status"] in ["completed", "failed", "partial"]:
                print(f"\n✓ Job {status['status']}")
                break
    
    # Get results
    print("\nRetrieving job results...")
    results = processor.get_job_results(job.job_id)
    
    if results:
        print(f"  Job status: {results['status']}")
        print(f"  Total results: {len(results['results'])}")
        
        for i, result in enumerate(results['results'][:3]):  # Show first 3
            print(f"\n  Task {i + 1}:")
            print(f"    Success: {result['success']}")
            if result['error']:
                print(f"    Error: {result['error']}")


def demo_batch_workflow_execution():
    """Demonstrate batch workflow execution"""
    print("\n" + "=" * 60)
    print("Demo 2: Batch Workflow Execution")
    print("=" * 60)
    
    processor = BatchProcessor(storage_path=Path("./data/batch_jobs"))
    
    # Prepare multiple workflows
    workflows = [
        {
            "goal": "Research and summarize recent AI developments",
            "context": {
                "output_format": "bullet points",
                "max_length": 500,
            },
        },
        {
            "goal": "Analyze user feedback and extract key themes",
            "context": {
                "output_format": "structured report",
                "feedback_count": 100,
            },
        },
        {
            "goal": "Generate test cases for a new feature",
            "context": {
                "feature": "user authentication",
                "coverage": "comprehensive",
            },
        },
    ]
    
    print(f"\nSubmitting batch workflow job with {len(workflows)} workflows...")
    job = processor.submit_batch_job(
        job_type=BatchJobType.WORKFLOW_BATCH,
        tasks=workflows,
        created_by="demo_user",
        priority=2,
        max_workers=2,  # Process 2 workflows in parallel
        metadata={
            "source": "demo",
            "batch_name": "workflow_batch_demo",
        },
    )
    
    print(f"✓ Job submitted: {job.job_id}")
    print(f"  Status: {job.status.value}")
    print(f"  Workflows: {len(job.tasks)}")
    
    # Monitor progress
    print("\nJob submitted for async processing.")
    print("In production, you would poll the status endpoint or use webhooks.")


def demo_batch_validation():
    """Demonstrate batch validation"""
    print("\n" + "=" * 60)
    print("Demo 3: Batch Validation")
    print("=" * 60)
    
    processor = BatchProcessor(storage_path=Path("./data/batch_jobs"))
    
    # Prepare outputs to validate
    outputs = [
        {"output": '{"status": "success", "result": "Output 1"}'},
        {"output": '{"status": "success", "result": "Output 2"}'},
        {"output": "Invalid JSON output"},
        {"output": '{"status": "success", "result": "Output 4"}'},
    ]
    
    print(f"\nSubmitting batch validation job with {len(outputs)} outputs...")
    job = processor.submit_batch_job(
        job_type=BatchJobType.VALIDATION_BATCH,
        tasks=outputs,
        created_by="demo_user",
        max_workers=4,
        metadata={
            "source": "demo",
            "batch_name": "validation_batch_demo",
        },
    )
    
    print(f"✓ Job submitted: {job.job_id}")
    print(f"  Status: {job.status.value}")


def demo_job_listing_and_filtering():
    """Demonstrate job listing and filtering"""
    print("\n" + "=" * 60)
    print("Demo 4: Job Listing and Filtering")
    print("=" * 60)
    
    processor = BatchProcessor(storage_path=Path("./data/batch_jobs"))
    
    # List all jobs
    print("\nListing all batch jobs...")
    all_jobs = processor.list_jobs(limit=10)
    
    print(f"  Total jobs: {len(all_jobs)}")
    
    for job in all_jobs[:5]:  # Show first 5
        print(f"\n  Job: {job['job_id']}")
        print(f"    Type: {job['job_type']}")
        print(f"    Status: {job['status']}")
        print(f"    Tasks: {job['tasks_count']}")
        print(f"    Created: {job['created_at']}")
        
        if job.get('progress'):
            progress = job['progress']
            print(f"    Progress: {progress['progress_percent']:.1f}%")
    
    # Filter by job type
    print("\n\nFiltering by job type (failure_optimization)...")
    failure_jobs = processor.list_jobs(
        job_type=BatchJobType.FAILURE_OPTIMIZATION,
        limit=5,
    )
    
    print(f"  Failure optimization jobs: {len(failure_jobs)}")


def demo_workflow_batch_with_orchestrator():
    """Demonstrate workflow batch execution using WorkflowOrchestrator"""
    print("\n" + "=" * 60)
    print("Demo 5: Workflow Batch with Orchestrator")
    print("=" * 60)
    
    from src.core.workflow_orchestrator import WorkflowOrchestrator
    
    config = SystemConfig(enable_auto_optimization=False)
    orchestrator = WorkflowOrchestrator(config)
    
    # Prepare multiple workflows
    workflows = [
        {
            "goal": "Analyze sales data and identify trends",
            "context": {"period": "Q1 2024", "format": "summary"},
        },
        {
            "goal": "Generate customer satisfaction report",
            "context": {"survey_count": 500, "format": "detailed"},
        },
    ]
    
    print(f"\nExecuting {len(workflows)} workflows in parallel...")
    print("(This demo uses mock models if no API keys are configured)\n")
    
    try:
        results = orchestrator.execute_workflows_batch(
            workflows=workflows,
            max_parallel=2,
            max_retries=1,
        )
        
        print(f"✓ Batch execution completed")
        print(f"  Total workflows: {len(results)}")
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        for i, result in enumerate(results):
            print(f"\n  Workflow {i + 1}:")
            print(f"    Success: {result['success']}")
            if result['error']:
                print(f"    Error: {result['error']}")
    
    except Exception as e:
        print(f"⚠ Demo skipped (expected with mock models): {e}")


def demo_batch_statistics():
    """Demonstrate batch job statistics"""
    print("\n" + "=" * 60)
    print("Demo 6: Batch Job Statistics")
    print("=" * 60)
    
    processor = BatchProcessor(storage_path=Path("./data/batch_jobs"))
    
    # Get all jobs
    all_jobs = processor.list_jobs(limit=1000)
    
    # Calculate statistics
    by_status = {}
    by_type = {}
    
    for job in all_jobs:
        status = job['status']
        job_type = job['job_type']
        
        by_status[status] = by_status.get(status, 0) + 1
        by_type[job_type] = by_type.get(job_type, 0) + 1
    
    print(f"\nTotal batch jobs: {len(all_jobs)}")
    
    print("\nBy status:")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count}")
    
    print("\nBy type:")
    for job_type, count in sorted(by_type.items()):
        print(f"  {job_type}: {count}")


if __name__ == "__main__":
    print("=" * 60)
    print("Batch Processing Demo")
    print("=" * 60)
    print("\nThis demo showcases the batch processing capabilities:")
    print("- Async job queuing with Celery")
    print("- Progress monitoring")
    print("- Parallel workflow execution")
    print("- Fault tolerance and retry logic")
    print("- Result retrieval and tracking")
    
    try:
        # Run demos
        demo_batch_failure_optimization()
        demo_batch_workflow_execution()
        demo_batch_validation()
        demo_job_listing_and_filtering()
        demo_workflow_batch_with_orchestrator()
        demo_batch_statistics()
        
        print("\n" + "=" * 60)
        print("✓ Demo completed successfully!")
        print("=" * 60)
        
        print("\n\nNOTE: To run batch jobs with Celery:")
        print("1. Start Redis: redis-server")
        print("2. Start Celery worker: celery -A src.batch.celery_config worker --loglevel=info")
        print("3. Start Celery Flower (monitoring): celery -A src.batch.celery_config flower")
        print("4. Submit jobs via API: python web/api_batch.py")
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
