from celery import Celery
from kombu import Queue, Exchange
from utils.config import settings

# Initialize Celery app
celery_app = Celery("spatial_ai_platform")

# Configure broker and backend
celery_app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Acknowledge tasks late (only when fully complete/failed)
    task_acks_late=True,
    
    # If tasks are rejected (e.g. worker killed), re-queue them
    task_reject_on_worker_lost=True,
    
    # Prefetch limits - CPU tasks can be many, GPU should be limited
    worker_prefetch_multiplier=1,
)

# Setup Task Routing
default_exchange = Exchange("default", type="direct")
cpu_exchange = Exchange("cpu_tasks", type="direct")
gpu_exchange = Exchange("gpu_tasks", type="direct")

celery_app.conf.task_queues = (
    Queue("cpu", cpu_exchange, routing_key="task.cpu"),
    Queue("gpu", gpu_exchange, routing_key="task.gpu"),
)

celery_app.conf.task_default_queue = "cpu"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "task.cpu"

# Explicit routing by task pattern
celery_app.conf.task_routes = {
    # Any tasks within workers.gpu module go to GPU queue
    "workers.gpu.*": {
        "queue": "gpu",
        "routing_key": "task.gpu",
    },
    
    # Exclude specifically known CPU bounds if needed, default goes to cpu
    "workers.cpu.*": {
        "queue": "cpu",
        "routing_key": "task.cpu",
    },
    
    # Fallback pattern matching
    "*.gpu.*": {"queue": "gpu", "routing_key": "task.gpu"},
}

if __name__ == "__main__":
    celery_app.start()
