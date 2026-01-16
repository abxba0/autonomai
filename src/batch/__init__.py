"""
Batch Processing Module

Provides batch processing capabilities with async job queuing using Celery.

Key components:
- BatchProcessor: High-level interface for batch job management
- BatchJob: Job model with progress tracking
- Celery tasks: Async task processing with parallelism
- Models: Data structures for batch operations
"""

from .models import (
    BatchJob,
    BatchJobStatus,
    BatchJobType,
    TaskResult,
    BatchJobProgress,
)
from .processor import BatchProcessor
from .celery_config import celery_app

__all__ = [
    "BatchProcessor",
    "BatchJob",
    "BatchJobStatus",
    "BatchJobType",
    "TaskResult",
    "BatchJobProgress",
    "celery_app",
]
