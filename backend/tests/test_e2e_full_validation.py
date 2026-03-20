"""
Full End-to-End API Validation

Tests complete authentication and multi-tenant flow with REAL HTTP calls:
1. Register users
2. Login and get tokens
3. Create organizations
4. Switch organization context
5. Access tenant-scoped data
6. Verify cross-organization isolation
7. Token lifecycle (refresh, logout, invalidation)
"""
import asyncio
import httpx
import random
import string
import json
import sys

# Ensure proper encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

def random_string(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(test_name: str, passed: bool, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status} {test_name}")
    if details:
        print(f"         {details}")

async def main():
    results = {"passed": 0, "failed": 0, "errors": []}
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        
        # ==================================================================
        # PHASE 1: INFRASTRUCTURE VALIDATION
        # ==================================================================
        print_section("PHASE 1: INFRASTRUCTURE VALIDATION")
        
        # Test 1.1: Health Check
        try:
            resp = await client.get("/health")
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                print_result("Health endpoint", True)
                results["passed"] += 1
            else:
                print_result("Health endpoint", False, f"Status: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("Health endpoint", False, str(e))
            results["failed"] += 1
            results["errors"].append(f"Health check failed: {e}")
            return results
        
        # Test 1.2: Root endpoint
        try:
            resp = await client.get("/")
            if resp.status_code == 200:
                data = resp.json()
                print_result("Root endpoint", True, f"Version: {data.get('version', 'N/A')}")
                results["passed"] += 1
            else:
                print_result("Root endpoint", False, f"Status: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("Root endpoint", False, str(e))
            results["failed"] += 1
        
        # Test 1.3: OpenAPI docs accessible
        try:
            resp = await client.get("/docs")
            if resp.status_code == 200:
                print_result("OpenAPI docs (/docs)", True)
                results["passed"] += 1
            else:
                print_result("OpenAPI docs (/docs)", False, f"Status: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("OpenAPI docs (/docs)", False, str(e))
            results["failed"] += 1
        
        # ==================================================================
        # PHASE 2: USER REGISTRATION & AUTHENTICATION
        # ==================================================================
        print_section("PHASE 2: USER REGISTRATION & AUTHENTICATION")
        
        # Create test users
        user1_email = f"user1_{random_string()}@test.com"
        user1_password = "SecurePass123!"
        user2_email = f"user2_{random_string()}@test.com"
        user2_password = "SecurePass456!"
        
        user1_token = None
        user1_refresh = None
        user2_token = None
        
        # Test 2.1: Register User 1
        try:
            resp = await client.post("/api/v1/auth/register", json={
                "email": user1_email,
                "password": user1_password,
                "full_name": "Test User One"
            })
            if resp.status_code == 201:
                print_result("Register User 1", True, f"Email: {user1_email}")
                results["passed"] += 1
            else:
                print_result("Register User 1", False, f"Status: {resp.status_code}, Body: {resp.text[:100]}")
                results["failed"] += 1
                results["errors"].append(f"User 1 registration failed: {resp.text}")
        except Exception as e:
            print_result("Register User 1", False, str(e))
            results["failed"] += 1
        
        # Test 2.2: Register User 2
        try:
            resp = await client.post("/api/v1/auth/register", json={
                "email": user2_email,
                "password": user2_password,
                "full_name": "Test User Two"
            })
            if resp.status_code == 201:
                print_result("Register User 2", True, f"Email: {user2_email}")
                results["passed"] += 1
            else:
                print_result("Register User 2", False, f"Status: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("Register User 2", False, str(e))
            results["failed"] += 1
        
        # Test 2.3: Duplicate registration rejection
        try:
            resp = await client.post("/api/v1/auth/register", json={
                "email": user1_email,
                "password": user1_password,
                "full_name": "Duplicate User"
            })
            if resp.status_code == 400:
                print_result("Duplicate registration blocked", True)
                results["passed"] += 1
            else:
                print_result("Duplicate registration blocked", False, f"Expected 400, got {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("Duplicate registration blocked", False, str(e))
            results["failed"] += 1
        
        # Test 2.4: Login User 1
        try:
            resp = await client.post("/api/v1/auth/login", data={
                "username": user1_email,
                "password": user1_password
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})
            if resp.status_code == 200:
                tokens = resp.json()
                user1_token = tokens.get("access_token")
                user1_refresh = tokens.get("refresh_token")
                if user1_token and user1_refresh:
                    print_result("Login User 1", True, "Got access + refresh tokens")
                    results["passed"] += 1
                else:
                    print_result("Login User 1", False, "Missing tokens in response")
                    results["failed"] += 1
            else:
                print_result("Login User 1", False, f"Status: {resp.status_code}, Body: {resp.text[:100]}")
                results["failed"] += 1
        except Exception as e:
            print_result("Login User 1", False, str(e))
            results["failed"] += 1
        
        # Test 2.5: Login User 2
        try:
            resp = await client.post("/api/v1/auth/login", data={
                "username": user2_email,
                "password": user2_password
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})
            if resp.status_code == 200:
                user2_token = resp.json().get("access_token")
                print_result("Login User 2", True)
                results["passed"] += 1
            else:
                print_result("Login User 2", False, f"Status: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("Login User 2", False, str(e))
            results["failed"] += 1
        
        # Test 2.6: Invalid login rejection
        try:
            resp = await client.post("/api/v1/auth/login", data={
                "username": user1_email,
                "password": "WrongPassword123!"
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})
            if resp.status_code == 400:
                print_result("Invalid password rejected", True)
                results["passed"] += 1
            else:
                print_result("Invalid password rejected", False, f"Expected 400, got {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("Invalid password rejected", False, str(e))
            results["failed"] += 1
        
        # Test 2.7: Get current user (User 1)
        if user1_token:
            try:
                resp = await client.get("/api/v1/auth/me", headers={
                    "Authorization": f"Bearer {user1_token}"
                })
                if resp.status_code == 200:
                    user_data = resp.json()
                    print_result("Get current user (/me)", True, f"Email: {user_data.get('email', 'N/A')}")
                    results["passed"] += 1
                else:
                    print_result("Get current user (/me)", False, f"Status: {resp.status_code}, Body: {resp.text[:100]}")
                    results["failed"] += 1
                    results["errors"].append(f"/me endpoint failed: {resp.text}")
            except Exception as e:
                print_result("Get current user (/me)", False, str(e))
                results["failed"] += 1
        
        # Test 2.8: Unauthenticated access blocked
        try:
            resp = await client.get("/api/v1/auth/me")
            if resp.status_code == 401:
                print_result("Unauthenticated access blocked", True)
                results["passed"] += 1
            else:
                print_result("Unauthenticated access blocked", False, f"Expected 401, got {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_result("Unauthenticated access blocked", False, str(e))
            results["failed"] += 1
        
        # ==================================================================
        # PHASE 3: ORGANIZATION MANAGEMENT
        # ==================================================================
        print_section("PHASE 3: ORGANIZATION MANAGEMENT")
        
        org1_id = None
        org2_id = None
        
        if not user1_token or not user2_token:
            print("  [SKIP] Cannot test organizations without valid tokens")
        else:
            user1_headers = {"Authorization": f"Bearer {user1_token}"}
            user2_headers = {"Authorization": f"Bearer {user2_token}"}
            
            # Test 3.1: Create Organization 1 (by User 1)
            org1_name = f"TestOrg1_{random_string()}"
            try:
                resp = await client.post("/api/v1/organizations", json={
                    "name": org1_name,
                    "description": "Test Organization 1"
                }, headers=user1_headers)
                if resp.status_code == 201:
                    org_data = resp.json()
                    org1_id = org_data.get("id") or org_data.get("_id")
                    print_result("Create Organization 1", True, f"ID: {org1_id}, Name: {org1_name}")
                    results["passed"] += 1
                else:
                    print_result("Create Organization 1", False, f"Status: {resp.status_code}, Body: {resp.text[:150]}")
                    results["failed"] += 1
                    results["errors"].append(f"Org 1 creation failed: {resp.text}")
            except Exception as e:
                print_result("Create Organization 1", False, str(e))
                results["failed"] += 1
            
            # Test 3.2: Create Organization 2 (by User 2)
            org2_name = f"TestOrg2_{random_string()}"
            try:
                resp = await client.post("/api/v1/organizations", json={
                    "name": org2_name,
                    "description": "Test Organization 2"
                }, headers=user2_headers)
                if resp.status_code == 201:
                    org_data = resp.json()
                    org2_id = org_data.get("id") or org_data.get("_id")
                    print_result("Create Organization 2", True, f"ID: {org2_id}")
                    results["passed"] += 1
                else:
                    print_result("Create Organization 2", False, f"Status: {resp.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_result("Create Organization 2", False, str(e))
                results["failed"] += 1
            
            # Test 3.3: Duplicate org creation blocked
            try:
                resp = await client.post("/api/v1/organizations", json={
                    "name": "Another Org",
                    "description": "User already owns an org"
                }, headers=user1_headers)
                if resp.status_code == 400:
                    print_result("Duplicate org creation blocked", True)
                    results["passed"] += 1
                else:
                    print_result("Duplicate org creation blocked", False, f"Expected 400, got {resp.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_result("Duplicate org creation blocked", False, str(e))
                results["failed"] += 1
            
            # Test 3.4: List organizations (User 1)
            try:
                resp = await client.get("/api/v1/organizations", headers=user1_headers)
                if resp.status_code == 200:
                    orgs = resp.json()
                    print_result("List organizations (User 1)", True, f"Count: {len(orgs)}")
                    results["passed"] += 1
                else:
                    print_result("List organizations (User 1)", False, f"Status: {resp.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_result("List organizations (User 1)", False, str(e))
                results["failed"] += 1
            
            # Test 3.5: Get own organization details
            if org1_id:
                try:
                    resp = await client.get(f"/api/v1/organizations/{org1_id}", headers=user1_headers)
                    if resp.status_code == 200:
                        org_data = resp.json()
                        print_result("Get own org details", True, f"Name: {org_data.get('name', 'N/A')}")
                        results["passed"] += 1
                    else:
                        print_result("Get own org details", False, f"Status: {resp.status_code}")
                        results["failed"] += 1
                except Exception as e:
                    print_result("Get own org details", False, str(e))
                    results["failed"] += 1
            
            # ==================================================================
            # PHASE 4: MULTI-TENANT ISOLATION
            # ==================================================================
            print_section("PHASE 4: MULTI-TENANT ISOLATION")
            
            # Test 4.1: User 2 cannot access User 1's organization
            if org1_id:
                try:
                    resp = await client.get(f"/api/v1/organizations/{org1_id}", headers=user2_headers)
                    if resp.status_code == 403:
                        print_result("Cross-org access blocked (GET)", True, "User 2 cannot access Org 1")
                        results["passed"] += 1
                    else:
                        print_result("Cross-org access blocked (GET)", False, f"Expected 403, got {resp.status_code}")
                        results["failed"] += 1
                        results["errors"].append(f"SECURITY: User 2 could access Org 1! Status: {resp.status_code}")
                except Exception as e:
                    print_result("Cross-org access blocked (GET)", False, str(e))
                    results["failed"] += 1
            
            # Test 4.2: User 1 cannot access User 2's organization
            if org2_id:
                try:
                    resp = await client.get(f"/api/v1/organizations/{org2_id}", headers=user1_headers)
                    if resp.status_code == 403:
                        print_result("Cross-org access blocked (reverse)", True, "User 1 cannot access Org 2")
                        results["passed"] += 1
                    else:
                        print_result("Cross-org access blocked (reverse)", False, f"Expected 403, got {resp.status_code}")
                        results["failed"] += 1
                except Exception as e:
                    print_result("Cross-org access blocked (reverse)", False, str(e))
                    results["failed"] += 1
            
            # Test 4.3: User 2 cannot update User 1's organization
            if org1_id:
                try:
                    resp = await client.patch(f"/api/v1/organizations/{org1_id}", json={
                        "name": "Hacked Org Name"
                    }, headers=user2_headers)
                    if resp.status_code == 403:
                        print_result("Cross-org update blocked", True)
                        results["passed"] += 1
                    else:
                        print_result("Cross-org update blocked", False, f"Expected 403, got {resp.status_code}")
                        results["failed"] += 1
                        results["errors"].append(f"SECURITY: User 2 could update Org 1!")
                except Exception as e:
                    print_result("Cross-org update blocked", False, str(e))
                    results["failed"] += 1
            
            # Test 4.4: User 2 cannot delete User 1's organization
            if org1_id:
                try:
                    resp = await client.delete(f"/api/v1/organizations/{org1_id}", headers=user2_headers)
                    if resp.status_code in [403, 404]:
                        print_result("Cross-org delete blocked", True)
                        results["passed"] += 1
                    else:
                        print_result("Cross-org delete blocked", False, f"Expected 403/404, got {resp.status_code}")
                        results["failed"] += 1
                        results["errors"].append(f"SECURITY: User 2 could delete Org 1!")
                except Exception as e:
                    print_result("Cross-org delete blocked", False, str(e))
                    results["failed"] += 1
            
            # Test 4.5: User 2 cannot list User 1's org members
            if org1_id:
                try:
                    resp = await client.get(f"/api/v1/organizations/{org1_id}/members", headers=user2_headers)
                    if resp.status_code == 403:
                        print_result("Cross-org member list blocked", True)
                        results["passed"] += 1
                    else:
                        print_result("Cross-org member list blocked", False, f"Expected 403, got {resp.status_code}")
                        results["failed"] += 1
                except Exception as e:
                    print_result("Cross-org member list blocked", False, str(e))
                    results["failed"] += 1
            
            # Test 4.6: Non-existent org returns 404 (not 403, to prevent enumeration)
            try:
                fake_org_id = "000000000000000000000000"
                resp = await client.get(f"/api/v1/organizations/{fake_org_id}", headers=user1_headers)
                # Either 403 (not a member) or 404 (not found) is acceptable
                if resp.status_code in [403, 404]:
                    print_result("Non-existent org handling", True, f"Status: {resp.status_code}")
                    results["passed"] += 1
                else:
                    print_result("Non-existent org handling", False, f"Status: {resp.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_result("Non-existent org handling", False, str(e))
                results["failed"] += 1
            
            # ==================================================================
            # PHASE 5: ORGANIZATION CONTEXT SWITCHING
            # ==================================================================
            print_section("PHASE 5: ORGANIZATION CONTEXT SWITCHING")
            
            # Test 5.1: Get current organization
            try:
                resp = await client.get("/api/v1/organizations/me/current", headers=user1_headers)
                if resp.status_code == 200:
                    current_org = resp.json()
                    if current_org:
                        print_result("Get current organization", True, f"Current: {current_org.get('name', 'N/A')}")
                    else:
                        print_result("Get current organization", True, "No current org (null response)")
                    results["passed"] += 1
                else:
                    print_result("Get current organization", False, f"Status: {resp.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_result("Get current organization", False, str(e))
                results["failed"] += 1
            
            # Test 5.2: Switch to own organization
            if org1_id:
                try:
                    resp = await client.post(f"/api/v1/organizations/me/switch/{org1_id}", headers=user1_headers)
                    if resp.status_code == 200:
                        print_result("Switch to own org", True)
                        results["passed"] += 1
                    else:
                        print_result("Switch to own org", False, f"Status: {resp.status_code}, Body: {resp.text[:100]}")
                        results["failed"] += 1
                except Exception as e:
                    print_result("Switch to own org", False, str(e))
                    results["failed"] += 1
            
            # Test 5.3: Cannot switch to non-member organization
            if org2_id:
                try:
                    resp = await client.post(f"/api/v1/organizations/me/switch/{org2_id}", headers=user1_headers)
                    if resp.status_code == 403:
                        print_result("Switch to non-member org blocked", True)
                        results["passed"] += 1
                    else:
                        print_result("Switch to non-member org blocked", False, f"Expected 403, got {resp.status_code}")
                        results["failed"] += 1
                except Exception as e:
                    print_result("Switch to non-member org blocked", False, str(e))
                    results["failed"] += 1
            
            # ==================================================================
            # PHASE 6: TOKEN LIFECYCLE
            # ==================================================================
            print_section("PHASE 6: TOKEN LIFECYCLE")
            
            # Test 6.1: Token refresh
            if user1_refresh:
                try:
                    resp = await client.post("/api/v1/auth/refresh", json={
                        "refresh_token": user1_refresh
                    })
                    if resp.status_code == 200:
                        new_tokens = resp.json()
                        new_access = new_tokens.get("access_token")
                        if new_access:
                            print_result("Token refresh", True, "Got new access token")
                            results["passed"] += 1
                            # Update token for further tests
                            user1_token = new_access
                            user1_headers = {"Authorization": f"Bearer {user1_token}"}
                        else:
                            print_result("Token refresh", False, "No access token in response")
                            results["failed"] += 1
                    else:
                        print_result("Token refresh", False, f"Status: {resp.status_code}, Body: {resp.text[:100]}")
                        results["failed"] += 1
                        results["errors"].append(f"Token refresh failed: {resp.text}")
                except Exception as e:
                    print_result("Token refresh", False, str(e))
                    results["failed"] += 1
            
            # Test 6.2: Invalid refresh token rejected
            try:
                resp = await client.post("/api/v1/auth/refresh", json={
                    "refresh_token": "invalid.token.here"
                })
                if resp.status_code == 401:
                    print_result("Invalid refresh token rejected", True)
                    results["passed"] += 1
                else:
                    print_result("Invalid refresh token rejected", False, f"Expected 401, got {resp.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_result("Invalid refresh token rejected", False, str(e))
                results["failed"] += 1
            
            # Test 6.3: Logout
            try:
                resp = await client.post("/api/v1/auth/logout", headers=user1_headers)
                if resp.status_code == 200:
                    print_result("Logout", True)
                    results["passed"] += 1
                else:
                    print_result("Logout", False, f"Status: {resp.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_result("Logout", False, str(e))
                results["failed"] += 1
            
            # Test 6.4: Token invalidated after logout
            try:
                resp = await client.get("/api/v1/auth/me", headers=user1_headers)
                if resp.status_code == 401:
                    print_result("Token invalidated after logout", True)
                    results["passed"] += 1
                else:
                    print_result("Token invalidated after logout", False, f"Token still valid! Status: {resp.status_code}")
                    results["failed"] += 1
                    results["errors"].append("SECURITY: Token still valid after logout")
            except Exception as e:
                print_result("Token invalidated after logout", False, str(e))
                results["failed"] += 1
        
        # ==================================================================
        # SUMMARY
        # ==================================================================
        print_section("VALIDATION SUMMARY")
        
        total = results["passed"] + results["failed"]
        pass_rate = (results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\n  Total Tests: {total}")
        print(f"  Passed:      {results['passed']}")
        print(f"  Failed:      {results['failed']}")
        print(f"  Pass Rate:   {pass_rate:.1f}%")
        
        if results["errors"]:
            print(f"\n  Critical Errors ({len(results['errors'])}):")
            for err in results["errors"]:
                print(f"    - {err}")
        
        print(f"\n{'='*60}")
        if results["failed"] == 0:
            print("  [SUCCESS] All tests passed!")
        else:
            print(f"  [ISSUES] {results['failed']} test(s) failed - review errors above")
        print(f"{'='*60}\n")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
