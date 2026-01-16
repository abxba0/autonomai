"""
Celery Configuration for Batch Processing

Configures Celery for asynchronous task processing with Redis as broker and backend.
"""

import os
from celery import Celery
from kombu import Queue
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_BACKEND = os.getenv("REDIS_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery_app = Celery(
    "autonomai_batch",
    broker=REDIS_URL,
    backend=REDIS_BACKEND,
    include=["src.batch.tasks"],
)

# Task name constants
TASK_PROCESS_FAILURE_BATCH = "src.batch.tasks.process_failure_batch"
TASK_PROCESS_WORKFLOW_BATCH = "src.batch.tasks.process_workflow_batch"
TASK_PROCESS_VALIDATION_BATCH = "src.batch.tasks.process_validation_batch"
TASK_PROCESS_SINGLE_TASK = "src.batch.tasks.process_single_task"

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Result backend settings
    result_backend=REDIS_BACKEND,
    result_expires=3600 * 24,  # Results expire after 24 hours
    result_extended=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    task_acks_late=True,  # Acknowledge after task completion for fault tolerance
    task_reject_on_worker_lost=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks
    
    # Retry settings
    task_default_retry_delay=60,  # Retry after 60 seconds
    task_max_retries=3,
    
    # Queue configuration
    task_routes={
        TASK_PROCESS_FAILURE_BATCH: {"queue": "batch_failures"},
        TASK_PROCESS_WORKFLOW_BATCH: {"queue": "batch_workflows"},
        TASK_PROCESS_VALIDATION_BATCH: {"queue": "batch_validations"},
        TASK_PROCESS_SINGLE_TASK: {"queue": "batch_tasks"},
    },
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("batch_failures", routing_key="batch_failures"),
        Queue("batch_workflows", routing_key="batch_workflows"),
        Queue("batch_validations", routing_key="batch_validations"),
        Queue("batch_tasks", routing_key="batch_tasks"),
    ),
    
    # Beat schedule for periodic tasks (optional)
    beat_schedule={},
    
    # Monitoring
    task_send_sent_event=True,
    worker_send_task_events=True,
    
    # Error handling
    task_ignore_result=False,
)

# Optional: Configure for development vs production
if os.getenv("ENVIRONMENT") == "development":
    celery_app.conf.update(
        task_always_eager=False,  # Run tasks asynchronously even in dev
        task_eager_propagates=True,
    )
