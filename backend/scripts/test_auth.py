import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app
from utils.database import Database, init_database_async
import pytest

client = TestClient(app)
test_email = "test.user@example.com"
test_password = "SecurePassword123!"

# Using pytest-asyncio to handle database setup directly
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Setup test logic without pytest fully but mimicking it
    pass

def test_user_registration(client):
    print("Testing User Registration...")
    payload = {
        "email": test_email,
        "full_name": "Test User",
        "password": test_password
    }
    response = client.post("/api/v1/auth/register", json=payload)
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Registered User successfully. ID: {data.get('_id')}")
        assert "_id" in data
        assert data["email"] == test_email
        assert "password" not in data
        assert "hashed_password" not in data
    elif response.status_code == 400 and "already exists" in response.text:
        print("✓ Registration endpoint blocked duplicate perfectly")
    else:
        print(f"FAILED: Registration returned {response.status_code}: {response.text}")
        assert False

def test_user_registration_duplicate(client):
    print("\nTesting Duplicate Email Rejection...")
    payload = {
        "email": test_email,
        "full_name": "Test User Copy",
        "password": test_password
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    print("✓ Successfully prevented duplicate registration.")

def test_user_registration_invalid_email(client):
    print("\nTesting Invalid Email Formatting...")
    payload = {
        "email": "not-an-email",
        "full_name": "Bad Email User",
        "password": test_password
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422 # Pydantic formatting error
    print("✓ Successfully prevented bad email strings.")

def test_user_registration_short_password(client):
    print("\nTesting Invalid Short Password...")
    payload = {
        "email": "another@example.com",
        "full_name": "Short Password",
        "password": "short" # Needs min length 8
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422 # Pydantic formatting error
    print("✓ Successfully prevented short passwords.")

async def reset_test_data():
    """Clear test data after tests"""
    await Database.connect()
    db = Database.get_database()
    await db.users.delete_one({"email": test_email})
    await Database.disconnect()

if __name__ == "__main__":
    with TestClient(app) as test_client:
        test_user_registration(test_client)
        test_user_registration_duplicate(test_client)
        test_user_registration_invalid_email(test_client)
        test_user_registration_short_password(test_client)
        
    asyncio.run(reset_test_data())
    print("\nAll Auth tests passed successfully!")
