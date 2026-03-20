import logging
from celery import Task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

class SpatialAIBaseTask(Task):
    """
    Base Celery task class with retry logic for transient failures.
    Provides common functionality for both CPU and GPU tasks.
    """
    abstract = True
    
    # Retry on all exceptions except those explicitly defined as non-retriable later
    autoretry_for = (Exception,)
    
    # Max retries
    max_retries = 3
    
    # Exponential backoff configured to respect platform constraints
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes delay
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log the failure with exception details."""
        logger.error(
            f"Task {self.name}[{task_id}] failed. "
            f"Args: {args}, Kwargs: {kwargs}. "
            f"Exception: {exc}"
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Log successful task execution."""
        logger.info(
            f"Task {self.name}[{task_id}] succeeded."
        )
        super().on_success(retval, task_id, args, kwargs)
