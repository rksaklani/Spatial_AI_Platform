"""
Test tasks for verifying Celery worker functionality.

These tasks are used for health checks and system validation.
"""

import time
import logging
from celery import shared_task
from workers.celery_app import celery_app
from workers.base_task import SpatialAIBaseTask

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=SpatialAIBaseTask, name="workers.test_tasks.ping")
def ping(self) -> dict:
    """
    Simple ping task for health checking.
    
    Returns:
        dict: Status information including worker details
    """
    return {
        "status": "pong",
        "worker": self.request.hostname,
        "task_id": self.request.id,
    }


@celery_app.task(bind=True, base=SpatialAIBaseTask, name="workers.test_tasks.add")
def add(self, x: int, y: int) -> dict:
    """
    Simple addition task for testing worker execution.
    
    Args:
        x: First number
        y: Second number
        
    Returns:
        dict: Result with computation details
    """
    result = x + y
    logger.info(f"Task add: {x} + {y} = {result}")
    return {
        "result": result,
        "operation": f"{x} + {y}",
        "worker": self.request.hostname,
        "task_id": self.request.id,
    }


@celery_app.task(bind=True, base=SpatialAIBaseTask, name="workers.test_tasks.echo")
def echo(self, message: str, delay: float = 0) -> dict:
    """
    Echo task with optional delay for testing async behavior.
    
    Args:
        message: Message to echo back
        delay: Optional delay in seconds before returning
        
    Returns:
        dict: Echoed message with timing info
    """
    start = time.time()
    
    if delay > 0:
        time.sleep(delay)
    
    elapsed = time.time() - start
    
    return {
        "message": message,
        "delay_requested": delay,
        "actual_delay": round(elapsed, 3),
        "worker": self.request.hostname,
        "task_id": self.request.id,
    }


@celery_app.task(bind=True, base=SpatialAIBaseTask, name="workers.test_tasks.system_info")
def system_info(self) -> dict:
    """
    Get system information from the worker.
    
    Returns:
        dict: System and environment information
    """
    import platform
    import os
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "worker": self.request.hostname,
        "task_id": self.request.id,
        "pid": os.getpid(),
    }
