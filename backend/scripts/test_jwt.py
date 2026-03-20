import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from fastapi import APIRouter, Depends
from main import app
from utils.database import Database
from api.deps import get_current_user
from models.user import UserResponse
from utils.valkey_client import ValkeyClient
import pytest

client = TestClient(app)
test_email = "jwt.user@example.com"
test_password = "SecurePassword123!"

# -- Add a protected mock route directly to the app for testing --
test_router = APIRouter()
@test_router.get("/api/v1/test_protected")
async def protected_route(current_user: UserResponse = Depends(get_current_user)):
    return {"message": "Access granted", "user": current_user.email}

app.include_router(test_router)
# -----------------------------------------------------------------

def test_setup_user_registration(client):
    print("Setting up User Registration for JWT tests...")
    payload = {
        "email": test_email,
        "full_name": "JWT User",
        "password": test_password
    }
    client.post("/api/v1/auth/register", json=payload)

def test_login(client):
    print("\nTesting User Login...")
    payload = {
        "username": test_email, # OAuth2 form expects 'username' instead of 'email'
        "password": test_password
    }
    # Form data uses data= not json=
    response = client.post("/api/v1/auth/login", data=payload)
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        print("✓ Login returned valid JWT token representations.")
        return data["access_token"], data["refresh_token"]
    else:
        print(f"FAILED: Login returned {response.status_code}: {response.text}")
        assert False

def test_protected_route_access(client, access_token):
    print("\nTesting Protected Route Access...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/test_protected", headers=headers)
    assert response.status_code == 200
    assert response.json()["user"] == test_email
    print("✓ Successfully accessed protected route using valid access token.")

def test_unauthorized_access(client):
    print("\nTesting Unauthorized Route Access...")
    response = client.get("/api/v1/test_protected")
    assert response.status_code == 401
    print("✓ Successfully blocked access without token.")

def test_token_refresh(client, refresh_token):
    print("\nTesting Token Refresh...")
    response = client.post(f"/api/v1/auth/refresh?refresh_token={refresh_token}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    print("✓ Successfully refreshed the access token.")
    return data["access_token"], data["refresh_token"]

def test_logout(client, access_token):
    print("\nTesting Logout / Token Revocation...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    print("✓ Logout endpoint succeeded.")
    
    # Try accessing the protected route again with the blacklisted token
    response_retry = client.get("/api/v1/test_protected", headers=headers)
    assert response_retry.status_code == 401
    assert "revoked" in response_retry.json()["detail"].lower()
    print("✓ Successfully rejected revoked JTI access token.")

async def reset_test_data():
    """Clear test data after tests"""
    await Database.connect()
    db = Database.get_database()
    await db.users.delete_one({"email": test_email})
    await Database.disconnect()
    
    valkey = ValkeyClient()
    valkey.flush_db()

if __name__ == "__main__":
    with TestClient(app) as test_client:
        test_setup_user_registration(test_client)
        
        test_unauthorized_access(test_client)
        
        access_token, refresh_token = test_login(test_client)
        
        test_protected_route_access(test_client, access_token)
        
        new_access_token, new_refresh_token = test_token_refresh(test_client, refresh_token)
        
        test_logout(test_client, new_access_token)
        
    asyncio.run(reset_test_data())
    print("\nAll JWT Auth tests passed successfully!")
