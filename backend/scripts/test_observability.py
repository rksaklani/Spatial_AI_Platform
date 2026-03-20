import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoints():
    print("Testing Basic Health Endpoint...")
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok"
    print("✓ Basic /health OK")
    
    print("\nTesting Detailed Health Endpoint...")
    response = client.get("/health/detailed")
    # Even if degraded, the endpoint responds
    assert response.status_code in [200, 503], f"Unexpected status code {response.status_code}"
    data = response.json()
    print(f"Detailed Status: {data['status']}")
    print(f"Dependencies: {data['dependencies']}")
    assert "mongodb" in data["dependencies"]
    assert "valkey" in data["dependencies"]
    assert "minio" in data["dependencies"]
    assert "celery" in data["dependencies"]
    print("✓ Detailed /health/detailed executed successfully")

def test_metrics_endpoint():
    print("\nTesting Prometheus Metrics Endpoint...")
    response = client.get("/metrics")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    content = response.text
    # Should see python/fastapi metrics
    assert "python_info" in content or "http_requests" in content, "Missing expected metric keys"
    print("✓ Prometheus /metrics OK")

if __name__ == "__main__":
    test_health_endpoints()
    test_metrics_endpoint()
    print("\nAll Observability endpoints tested successfully!")
