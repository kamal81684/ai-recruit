"""
Background Task Queue System for AI Resume Shortlisting Assistant.

This module provides a lightweight, in-memory task queue for asynchronous
processing of CPU-intensive operations like PDF parsing and LLM evaluation.

Features:
- Thread-based task execution
- Task status tracking
- Result storage
- Automatic cleanup of old tasks
- Integration with existing evaluation engine

Usage:
    from task_queue import submit_evaluation_task, get_task_status

    # Submit a task for async processing
    task_id = submit_evaluation_task(resume_text, job_description)

    # Check task status
    status = get_task_status(task_id)
    if status['status'] == 'completed':
        result = status['result']

Contributor: shubham21155102
"""

import threading
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a background task."""
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization."""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result if not isinstance(self.result, Exception) else None,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count
        }


class TaskQueue:
    """
    In-memory task queue with thread-based execution.

    This provides a simple alternative to Celery/Redis for background processing.
    For production, consider using Celery with Redis or RabbitMQ.
    """

    def __init__(self, max_workers: int = 4, task_ttl: int = 3600):
        """
        Initialize the task queue.

        Args:
            max_workers: Maximum number of worker threads
            task_ttl: Time-to-live for completed tasks in seconds (default: 1 hour)
        """
        self.max_workers = max_workers
        self.task_ttl = task_ttl
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
        self.workers = []
        self.running = False

    def start(self):
        """Start the worker threads."""
        if self.running:
            logger.warning("Task queue is already running")
            return

        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"TaskWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            logger.info(f"Started worker thread: TaskWorker-{i}")

        # Start cleanup thread
        cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="TaskCleanup",
            daemon=True
        )
        cleanup_thread.start()
        logger.info("Started task queue cleanup thread")

    def stop(self):
        """Stop the task queue gracefully."""
        self.running = False
        logger.info("Task queue stopped")

    def submit(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Submit a task to the queue.

        Args:
            func: Function to execute
            *args: Function arguments
            task_id: Optional custom task ID
            **kwargs: Function keyword arguments

        Returns:
            Task ID for tracking
        """
        if task_id is None:
            task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs
        )

        with self.lock:
            self.tasks[task_id] = task

        logger.info(f"Task {task_id} submitted to queue")
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        with self.lock:
            return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled, False otherwise
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                logger.info(f"Task {task_id} cancelled")
                return True
        return False

    def _worker_loop(self):
        """Worker thread main loop."""
        logger.info(f"Worker {threading.current_thread().name} started")

        while self.running:
            task = None

            # Find next pending task
            with self.lock:
                for t in self.tasks.values():
                    if t.status == TaskStatus.PENDING:
                        task = t
                        task.status = TaskStatus.PROCESSING
                        task.started_at = datetime.now()
                        break

            if task:
                self._execute_task(task)
            else:
                time.sleep(0.1)  # Small sleep to avoid busy waiting

        logger.info(f"Worker {threading.current_thread().name} stopped")

    def _execute_task(self, task: Task):
        """Execute a single task."""
        try:
            logger.info(f"Executing task {task.task_id}")

            # Execute the function
            result = task.func(*task.args, **task.kwargs)

            # Store result
            with self.lock:
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()

            logger.info(f"Task {task.task_id} completed successfully")

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {str(e)}")

            with self.lock:
                if task.retry_count < task.max_retries:
                    # Retry the task
                    task.retry_count += 1
                    task.status = TaskStatus.PENDING
                    task.started_at = None
                    logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
                else:
                    # Mark as failed after max retries
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = datetime.now()

    def _cleanup_loop(self):
        """Periodically clean up old completed tasks."""
        while self.running:
            try:
                time.sleep(300)  # Check every 5 minutes

                cutoff = datetime.now() - timedelta(seconds=self.task_ttl)

                with self.lock:
                    to_remove = [
                        task_id for task_id, task in self.tasks.items()
                        if task.completed_at and task.completed_at < cutoff
                    ]

                    for task_id in to_remove:
                        del self.tasks[task_id]
                        logger.debug(f"Cleaned up old task {task_id}")

                    if to_remove:
                        logger.info(f"Cleaned up {len(to_remove)} old tasks")

            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self.lock:
            stats = {
                'total_tasks': len(self.tasks),
                'pending': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                'processing': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PROCESSING),
                'completed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                'failed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
                'cancelled': sum(1 for t in self.tasks.values() if t.status == TaskStatus.CANCELLED),
                'workers': len(self.workers),
                'running': self.running
            }
        return stats


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get the global task queue instance."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
        _task_queue.start()
    return _task_queue


def submit_evaluation_task(
    resume_text: str,
    job_description: str
) -> str:
    """
    Submit a resume evaluation task for background processing.

    This is a convenience function that wraps the evaluation engine
    in a background task.

    Args:
        resume_text: Extracted text from resume
        job_description: Job description text

    Returns:
        Task ID for tracking
    """
    from engine import evaluate_resume

    def _evaluate():
        return evaluate_resume(resume_text, job_description)

    queue = get_task_queue()
    return queue.submit(_evaluate)


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a background task.

    Args:
        task_id: Task ID to check

    Returns:
        Dictionary with task status or None if not found
    """
    queue = get_task_queue()
    task = queue.get_task(task_id)

    if task:
        return task.to_dict()
    return None


def wait_for_task(task_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
    """
    Wait for a task to complete.

    Args:
        task_id: Task ID to wait for
        timeout: Maximum wait time in seconds

    Returns:
        Task dictionary with result or None if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = get_task_status(task_id)
        if status is None:
            return None

        if status['status'] in ('completed', 'failed', 'cancelled'):
            return status

        time.sleep(0.5)

    return get_task_status(task_id)


# Initialize task queue on module import
try:
    get_task_queue()
    logger.info("Task queue system initialized")
except Exception as e:
    logger.error(f"Failed to initialize task queue: {str(e)}")
