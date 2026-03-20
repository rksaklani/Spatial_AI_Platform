import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.celery_app import celery_app
from workers.base_task import SpatialAIBaseTask

def test_config():
    print("Testing Celery Configuration...")
    
    # Check Broker URL (uses redis:// protocol - Valkey is Redis-compatible)
    broker = celery_app.conf.broker_url
    print(f"Broker: {broker}")
    assert broker.startswith("redis://"), "Broker URL should use redis:// (Valkey is Redis-compatible)"
    
    # Check Task Queues
    queues = {q.name: q for q in celery_app.conf.task_queues}
    print(f"Queues: {list(queues.keys())}")
    assert "cpu" in queues
    assert "gpu" in queues

    # Check Routing
    routes = celery_app.conf.task_routes
    print(f"Routes configured: {len(routes)}")
    assert "workers.gpu.*" in routes
    
    # Check Base Task
    print(f"Base Task autoretry_for: {SpatialAIBaseTask.autoretry_for}")
    assert Exception in SpatialAIBaseTask.autoretry_for
    
    print("All Celery configuration tests passed successfully!")

if __name__ == "__main__":
    test_config()
