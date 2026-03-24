"""
Test login performance to identify bottlenecks.

Usage:
    python backend/scripts/test_login_performance.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import get_db
from utils.security import verify_password, get_password_hash
import structlog

logger = structlog.get_logger(__name__)


async def test_login_performance():
    """Test each step of the login process to identify bottlenecks."""
    
    print("\n" + "="*60)
    print("LOGIN PERFORMANCE TEST")
    print("="*60 + "\n")
    
    # Initialize database connection
    from utils.database import Database
    await Database.connect()
    
    # Test 1: Database connection
    print("1. Testing database connection...")
    start = time.time()
    db = await get_db()
    db_time = (time.time() - start) * 1000
    print(f"   ✓ Database connection: {db_time:.2f}ms\n")
    
    # Test 2: Create test user if not exists
    print("2. Setting up test user...")
    test_email = "performance@test.com"
    test_password = "TestPassword123!"
    
    user_doc = await db.users.find_one({"email": test_email})
    if not user_doc:
        print("   Creating test user...")
        start = time.time()
        hashed_password = get_password_hash(test_password)
        hash_time = (time.time() - start) * 1000
        print(f"   ✓ Password hashing: {hash_time:.2f}ms")
        
        await db.users.insert_one({
            "_id": "test-user-perf",
            "email": test_email,
            "full_name": "Performance Test User",
            "hashed_password": hashed_password,
            "is_active": True,
        })
        print(f"   ✓ Test user created\n")
    else:
        print(f"   ✓ Test user already exists\n")
    
    # Test 3: Email lookup (without index)
    print("3. Testing email lookup (full document)...")
    start = time.time()
    user_doc = await db.users.find_one({"email": test_email})
    lookup_time = (time.time() - start) * 1000
    print(f"   ✓ Email lookup: {lookup_time:.2f}ms\n")
    
    # Test 4: Email lookup (with projection - optimized)
    print("4. Testing email lookup (projection only)...")
    start = time.time()
    user_doc = await db.users.find_one(
        {"email": test_email},
        {"_id": 1, "hashed_password": 1, "is_active": 1}
    )
    lookup_proj_time = (time.time() - start) * 1000
    print(f"   ✓ Email lookup (optimized): {lookup_proj_time:.2f}ms")
    print(f"   Improvement: {lookup_time - lookup_proj_time:.2f}ms faster\n")
    
    # Test 5: Password verification
    print("5. Testing password verification...")
    hashed_password = user_doc["hashed_password"]
    
    # Test with correct password
    start = time.time()
    result = verify_password(test_password, hashed_password)
    verify_time = (time.time() - start) * 1000
    print(f"   ✓ Password verification: {verify_time:.2f}ms (result: {result})\n")
    
    # Test 6: Full login simulation
    print("6. Full login simulation...")
    start = time.time()
    
    # Step 1: Database lookup
    step1_start = time.time()
    user_doc = await db.users.find_one(
        {"email": test_email},
        {"_id": 1, "hashed_password": 1, "is_active": 1}
    )
    step1_time = (time.time() - step1_start) * 1000
    
    # Step 2: Password verification
    step2_start = time.time()
    if user_doc:
        is_valid = verify_password(test_password, user_doc["hashed_password"])
    step2_time = (time.time() - step2_start) * 1000
    
    # Step 3: Token generation (simulated)
    step3_start = time.time()
    from utils.security import create_access_token, create_refresh_token
    access_token = create_access_token(str(user_doc["_id"]))
    refresh_token = create_refresh_token(str(user_doc["_id"]))
    step3_time = (time.time() - step3_start) * 1000
    
    total_time = (time.time() - start) * 1000
    
    print(f"   Step 1 (DB lookup):        {step1_time:.2f}ms")
    print(f"   Step 2 (Password verify):  {step2_time:.2f}ms")
    print(f"   Step 3 (Token generation): {step3_time:.2f}ms")
    print(f"   ─────────────────────────────────────")
    print(f"   Total login time:          {total_time:.2f}ms\n")
    
    # Test 7: Check for indexes
    print("7. Checking database indexes...")
    indexes = await db.users.index_information()
    has_email_index = any('email' in str(idx) for idx in indexes.values())
    
    if has_email_index:
        print(f"   ✓ Email index exists")
    else:
        print(f"   ⚠ Email index NOT found - run create_indexes.py")
    
    print(f"   Available indexes: {list(indexes.keys())}\n")
    
    # Summary
    print("="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Database connection:     {db_time:.2f}ms")
    print(f"Email lookup:            {lookup_proj_time:.2f}ms")
    print(f"Password verification:   {verify_time:.2f}ms")
    print(f"Token generation:        {step3_time:.2f}ms")
    print(f"─────────────────────────────────────")
    print(f"Total login time:        {total_time:.2f}ms")
    print("="*60)
    
    # Performance rating
    if total_time < 100:
        rating = "EXCELLENT ⚡"
    elif total_time < 200:
        rating = "GOOD ✓"
    elif total_time < 500:
        rating = "ACCEPTABLE ⚠"
    else:
        rating = "SLOW ❌"
    
    print(f"\nPerformance Rating: {rating}")
    
    if total_time > 200:
        print("\nOptimization suggestions:")
        if not has_email_index:
            print("  • Run create_indexes.py to add email index")
        if verify_time > 100:
            print("  • Password hashing is slow - already optimized to 10 rounds")
        if lookup_proj_time > 50:
            print("  • Database query is slow - check MongoDB performance")
    
    # Disconnect from database
    from utils.database import Database
    await Database.disconnect()
    
    print()


if __name__ == "__main__":
    asyncio.run(test_login_performance())
