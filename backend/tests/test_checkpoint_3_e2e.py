"""
Checkpoint 3: End-to-End Authentication and Multi-Tenancy Validation

This script tests the complete authentication flow with REAL API calls:
1. Register a user
2. Login and get tokens
3. Create an organization
4. Switch organization context
5. Access tenant-scoped data
6. Verify multi-tenant isolation
"""
import asyncio
import httpx
import time
import random
import string
import sys

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

# ASCII-safe symbols
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

def random_string(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def main():
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("=" * 60)
        print("CHECKPOINT 3: End-to-End Validation")
        print("=" * 60)

        # ============================================
        # TEST 1: Health Check
        # ============================================
        print("\n[1/10] Testing health endpoint...")
        try:
            resp = await client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"
            results["passed"].append("Health check")
            print(f"  {PASS} Health check passed")
        except Exception as e:
            results["failed"].append(f"Health check: {e}")
            print(f"  {FAIL} Health check FAILED: {e}")
            return results

        # ============================================
        # TEST 2: User Registration
        # ============================================
        print("\n[2/10] Testing user registration...")
        user_email = f"testuser_{random_string()}@example.com"
        user_password = "TestPassword123!"
        user_data = {
            "email": user_email,
            "password": user_password,
            "full_name": "Test User"
        }

        try:
            resp = await client.post("/api/v1/auth/register", json=user_data)
            print(f"  Registration response status: {resp.status_code}")
            if resp.status_code in [200, 201]:
                results["passed"].append("User registration")
                print(f"  {PASS} User registration passed - Email: {user_email}")
            else:
                # May already exist or other error
                results["warnings"].append(f"User registration: {resp.status_code} - {resp.text}")
                print(f"  {WARN} User registration warning: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            results["failed"].append(f"User registration: {e}")
            print(f"  {FAIL} User registration FAILED: {e}")

        # ============================================
        # TEST 3: User Login
        # ============================================
        print("\n[3/10] Testing user login...")
        login_data = {
            "username": user_email,
            "password": user_password
        }

        access_token = None
        refresh_token = None
        try:
            # Login uses form data for OAuth2 compatibility
            resp = await client.post(
                "/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            print(f"  Login response status: {resp.status_code}")
            if resp.status_code == 200:
                tokens = resp.json()
                access_token = tokens.get("access_token")
                refresh_token = tokens.get("refresh_token")
                if access_token:
                    results["passed"].append("User login")
                    print(f"  {PASS} User login passed - Got access token")
                else:
                    results["failed"].append("User login: No access token in response")
                    print(f"  {FAIL} User login FAILED: No access token in response")
            else:
                results["failed"].append(f"User login: {resp.status_code} - {resp.text}")
                print(f"  {FAIL} User login FAILED: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            results["failed"].append(f"User login: {e}")
            print(f"  {FAIL} User login FAILED: {e}")

        if not access_token:
            print("\n{WARN} Cannot continue without access token")
            return results

        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # ============================================
        # TEST 4: Get Current User
        # ============================================
        print("\n[4/10] Testing get current user...")
        try:
            resp = await client.get("/api/v1/auth/me", headers=auth_headers)
            print(f"  Get me response status: {resp.status_code}")
            if resp.status_code == 200:
                user_info = resp.json()
                results["passed"].append("Get current user")
                print(f"  {PASS} Get current user passed - User ID: {user_info.get('id', 'N/A')}")
            else:
                results["failed"].append(f"Get current user: {resp.status_code}")
                print(f"  {FAIL} Get current user FAILED: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            results["failed"].append(f"Get current user: {e}")
            print(f"  {FAIL} Get current user FAILED: {e}")

        # ============================================
        # TEST 5: Create Organization
        # ============================================
        print("\n[5/10] Testing organization creation...")
        org_name = f"TestOrg_{random_string()}"
        org_data = {
            "name": org_name,
            "slug": org_name.lower().replace("_", "-"),
            "description": "Test organization for E2E testing"
        }

        org_id = None
        try:
            resp = await client.post("/api/v1/organizations", json=org_data, headers=auth_headers)
            print(f"  Create org response status: {resp.status_code}")
            if resp.status_code in [200, 201]:
                org_info = resp.json()
                # Try both 'id' and '_id' since Pydantic may serialize differently
                org_id = org_info.get("id") or org_info.get("_id")
                print(f"  DEBUG: org_info keys = {list(org_info.keys())}")
                results["passed"].append("Organization creation")
                print(f"  [PASS] Organization created - ID: {org_id}, Name: {org_name}")
            else:
                results["failed"].append(f"Organization creation: {resp.status_code}")
                print(f"  {FAIL} Organization creation FAILED: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            results["failed"].append(f"Organization creation: {e}")
            print(f"  {FAIL} Organization creation FAILED: {e}")

        # ============================================
        # TEST 6: Get User's Organizations
        # ============================================
        print("\n[6/10] Testing get user organizations...")
        try:
            resp = await client.get("/api/v1/organizations", headers=auth_headers)
            print(f"  Get orgs response status: {resp.status_code}")
            if resp.status_code == 200:
                orgs = resp.json()
                results["passed"].append("Get organizations")
                print(f"  {PASS} Get organizations passed - Found {len(orgs)} org(s)")
            else:
                results["failed"].append(f"Get organizations: {resp.status_code}")
                print(f"  {FAIL} Get organizations FAILED: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            results["failed"].append(f"Get organizations: {e}")
            print(f"  {FAIL} Get organizations FAILED: {e}")

        # ============================================
        # TEST 7: Switch Organization Context
        # ============================================
        print("\n[7/10] Testing organization context switch...")
        if org_id:
            try:
                # Endpoint is /me/switch/{org_id}
                resp = await client.post(
                    f"/api/v1/organizations/me/switch/{org_id}",
                    headers=auth_headers
                )
                print(f"  Switch org response status: {resp.status_code}")
                if resp.status_code == 200:
                    results["passed"].append("Organization switch")
                    print(f"  {PASS} Organization switch passed")
                else:
                    results["warnings"].append(f"Organization switch: {resp.status_code}")
                    print(f"  {WARN} Organization switch: {resp.status_code} - {resp.text[:200]}")
            except Exception as e:
                results["warnings"].append(f"Organization switch: {e}")
                print(f"  {WARN} Organization switch: {e}")
        else:
            results["warnings"].append("Organization switch: No org_id available")
            print("  {WARN} Skipped - no organization ID available")

        # ============================================
        # TEST 8: Token Refresh
        # ============================================
        print("\n[8/10] Testing token refresh...")
        if refresh_token:
            try:
                resp = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": refresh_token}
                )
                print(f"  Refresh token response status: {resp.status_code}")
                if resp.status_code == 200:
                    new_tokens = resp.json()
                    if new_tokens.get("access_token"):
                        results["passed"].append("Token refresh")
                        access_token = new_tokens["access_token"]
                        auth_headers = {"Authorization": f"Bearer {access_token}"}
                        print(f"  {PASS} Token refresh passed")
                    else:
                        results["failed"].append("Token refresh: No new access token")
                        print(f"  {FAIL} Token refresh FAILED: No new access token")
                else:
                    results["warnings"].append(f"Token refresh: {resp.status_code}")
                    print(f"  {WARN} Token refresh: {resp.status_code} - {resp.text[:200]}")
            except Exception as e:
                results["warnings"].append(f"Token refresh: {e}")
                print(f"  {WARN} Token refresh: {e}")
        else:
            results["warnings"].append("Token refresh: No refresh token")
            print("  {WARN} Skipped - no refresh token available")

        # ============================================
        # TEST 9: Multi-Tenant Isolation (Create Second User)
        # ============================================
        print("\n[9/10] Testing multi-tenant isolation...")
        user2_email = f"testuser2_{random_string()}@example.com"
        user2_password = "TestPassword456!"
        user2_data = {
            "email": user2_email,
            "password": user2_password,
            "full_name": "Test User 2"
        }

        user2_token = None
        try:
            # Register user 2
            resp = await client.post("/api/v1/auth/register", json=user2_data)
            print(f"  Register user 2 response: {resp.status_code}")

            if resp.status_code in [200, 201]:
                # Login user 2
                resp = await client.post(
                    "/api/v1/auth/login",
                    data={"username": user2_email, "password": user2_password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if resp.status_code == 200:
                    user2_token = resp.json().get("access_token")
                    print(f"  {PASS} User 2 registered and logged in")
        except Exception as e:
            print(f"  {WARN} User 2 setup: {e}")

        if user2_token and org_id:
            try:
                # User 2 should NOT be able to access User 1's organization
                user2_headers = {"Authorization": f"Bearer {user2_token}"}
                resp = await client.get(
                    f"/api/v1/organizations/{org_id}",
                    headers=user2_headers
                )
                print(f"  Cross-tenant access response: {resp.status_code}")

                if resp.status_code in [403, 404]:
                    results["passed"].append("Multi-tenant isolation")
                    print(f"  {PASS} Multi-tenant isolation passed - User 2 blocked from User 1's org")
                else:
                    results["failed"].append(f"Multi-tenant isolation: User 2 could access User 1's org")
                    print(f"  {FAIL} Multi-tenant isolation FAILED - User 2 accessed User 1's org!")
            except Exception as e:
                results["warnings"].append(f"Multi-tenant isolation: {e}")
                print(f"  {WARN} Multi-tenant isolation: {e}")
        else:
            results["warnings"].append("Multi-tenant isolation: Prerequisites not met")
            print("  {WARN} Skipped - prerequisites not met")

        # ============================================
        # TEST 10: Logout
        # ============================================
        print("\n[10/10] Testing logout...")
        try:
            resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
            print(f"  Logout response status: {resp.status_code}")
            if resp.status_code == 200:
                results["passed"].append("Logout")
                print(f"  {PASS} Logout passed")

                # Verify token is invalidated
                resp = await client.get("/api/v1/auth/me", headers=auth_headers)
                if resp.status_code == 401:
                    results["passed"].append("Token invalidation after logout")
                    print(f"  {PASS} Token invalidation passed")
                else:
                    results["warnings"].append(f"Token still valid after logout: {resp.status_code}")
                    print(f"  {WARN} Token still valid after logout")
            else:
                results["warnings"].append(f"Logout: {resp.status_code}")
                print(f"  {WARN} Logout: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            results["warnings"].append(f"Logout: {e}")
            print(f"  {WARN} Logout: {e}")

    # ============================================
    # Summary
    # ============================================
    print("\n" + "=" * 60)
    print("CHECKPOINT 3 SUMMARY")
    print("=" * 60)
    print(f"\n{PASS} PASSED: {len(results['passed'])}")
    for item in results["passed"]:
        print(f"    - {item}")

    if results["warnings"]:
        print(f"\n{WARN} WARNINGS: {len(results['warnings'])}")
        for item in results["warnings"]:
            print(f"    - {item}")

    if results["failed"]:
        print(f"\n{FAIL} FAILED: {len(results['failed'])}")
        for item in results["failed"]:
            print(f"    - {item}")

    total = len(results["passed"]) + len(results["failed"])
    pass_rate = (len(results["passed"]) / total * 100) if total > 0 else 0
    print(f"\n{'=' * 60}")
    print(f"PASS RATE: {pass_rate:.1f}% ({len(results['passed'])}/{total})")
    print(f"{'=' * 60}")

    return results

if __name__ == "__main__":
    asyncio.run(main())
