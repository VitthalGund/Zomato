"""
Test script for POST /api/v1/verify-order endpoint.

This script tests the verification endpoint with valid and invalid payloads.
"""

import asyncio
import httpx
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.crypto import generate_crypto_hash

load_dotenv()

BASE_URL = "http://localhost:8000"
SECRET_SALT = os.getenv("SECRET_SALT", "demo_secret_salt_12345")


async def test_valid_verification():
    """Test endpoint with valid crypto hash."""
    print("\n" + "=" * 60)
    print("Test 1: Valid Verification")
    print("=" * 60)
    
    # Use an order from seed data
    order_id = "ZOM-DEMO-00001"
    timestamp = int(datetime.utcnow().timestamp())
    device_id = "device-test-001"
    
    # Generate valid crypto hash
    crypto_hash = generate_crypto_hash(
        order_id=order_id,
        timestamp=timestamp,
        device_id=device_id,
        secret_salt=SECRET_SALT
    )
    
    payload = {
        "order_id": order_id,
        "verified_timestamp": timestamp,
        "confidence_score": 0.95,
        "crypto_hash": crypto_hash,
        "fallback_used": False,
        "device_id": device_id
    }
    
    print(f"\nPayload:")
    print(f"  order_id: {payload['order_id']}")
    print(f"  verified_timestamp: {payload['verified_timestamp']}")
    print(f"  confidence_score: {payload['confidence_score']}")
    print(f"  crypto_hash: {payload['crypto_hash'][:32]}...")
    print(f"  fallback_used: {payload['fallback_used']}")
    print(f"  device_id: {payload['device_id']}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/verify-order",
                json=payload,
                timeout=5.0
            )
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {response.json()}")
            
            if response.status_code == 200:
                print("\n✅ Test PASSED: Valid verification accepted")
                return True
            else:
                print(f"\n❌ Test FAILED: Expected 200, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            return False


async def test_invalid_hash():
    """Test endpoint with invalid crypto hash."""
    print("\n" + "=" * 60)
    print("Test 2: Invalid Crypto Hash")
    print("=" * 60)
    
    order_id = "ZOM-DEMO-00001"
    timestamp = int(datetime.utcnow().timestamp())
    device_id = "device-test-001"
    
    # Use an invalid hash
    invalid_hash = "0" * 64
    
    payload = {
        "order_id": order_id,
        "verified_timestamp": timestamp,
        "confidence_score": 0.95,
        "crypto_hash": invalid_hash,
        "fallback_used": False,
        "device_id": device_id
    }
    
    print(f"\nPayload:")
    print(f"  order_id: {payload['order_id']}")
    print(f"  crypto_hash: {payload['crypto_hash'][:32]}... (INVALID)")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/verify-order",
                json=payload,
                timeout=5.0
            )
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {response.json()}")
            
            if response.status_code == 401:
                print("\n✅ Test PASSED: Invalid hash rejected with 401")
                return True
            else:
                print(f"\n❌ Test FAILED: Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            return False


async def test_order_not_found():
    """Test endpoint with non-existent order."""
    print("\n" + "=" * 60)
    print("Test 3: Order Not Found")
    print("=" * 60)
    
    order_id = "ZOM-NONEXISTENT-99999"
    timestamp = int(datetime.utcnow().timestamp())
    device_id = "device-test-001"
    
    # Generate valid hash for non-existent order
    crypto_hash = generate_crypto_hash(
        order_id=order_id,
        timestamp=timestamp,
        device_id=device_id,
        secret_salt=SECRET_SALT
    )
    
    payload = {
        "order_id": order_id,
        "verified_timestamp": timestamp,
        "confidence_score": 0.95,
        "crypto_hash": crypto_hash,
        "fallback_used": False,
        "device_id": device_id
    }
    
    print(f"\nPayload:")
    print(f"  order_id: {payload['order_id']} (NON-EXISTENT)")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/verify-order",
                json=payload,
                timeout=5.0
            )
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {response.json()}")
            
            if response.status_code == 404:
                print("\n✅ Test PASSED: Non-existent order rejected with 404")
                return True
            else:
                print(f"\n❌ Test FAILED: Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            return False


async def test_fallback_verification():
    """Test endpoint with fallback_used=true."""
    print("\n" + "=" * 60)
    print("Test 4: Fallback Verification")
    print("=" * 60)
    
    order_id = "ZOM-DEMO-00002"
    timestamp = int(datetime.utcnow().timestamp())
    device_id = "device-test-002"
    
    # Generate valid crypto hash
    crypto_hash = generate_crypto_hash(
        order_id=order_id,
        timestamp=timestamp,
        device_id=device_id,
        secret_salt=SECRET_SALT
    )
    
    payload = {
        "order_id": order_id,
        "verified_timestamp": timestamp,
        "confidence_score": 0.0,  # No confidence for manual override
        "crypto_hash": crypto_hash,
        "fallback_used": True,  # Manual override
        "device_id": device_id
    }
    
    print(f"\nPayload:")
    print(f"  order_id: {payload['order_id']}")
    print(f"  fallback_used: {payload['fallback_used']} (MANUAL OVERRIDE)")
    print(f"  confidence_score: {payload['confidence_score']}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/verify-order",
                json=payload,
                timeout=5.0
            )
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Body: {response.json()}")
            
            if response.status_code == 200:
                print("\n✅ Test PASSED: Fallback verification accepted")
                return True
            else:
                print(f"\n❌ Test FAILED: Expected 200, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Zomato EdgeVision - Verification Endpoint Tests")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Secret Salt: {SECRET_SALT[:20]}...")
    
    # Check if server is running
    print("\n🔍 Checking if server is running...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=2.0)
            if response.status_code == 200:
                print("✓ Server is running")
            else:
                print(f"⚠ Server returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Server is not running: {e}")
            print("\nPlease start the server with: uvicorn backend.main:app --reload")
            return
    
    # Run tests
    results = []
    
    results.append(await test_valid_verification())
    results.append(await test_invalid_hash())
    results.append(await test_order_not_found())
    results.append(await test_fallback_verification())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {total - passed} test(s) failed")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

