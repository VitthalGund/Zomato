"""
Verify that the endpoint correctly stored data in MongoDB.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


async def verify_stored_data():
    """Check the verification logs stored by the endpoint."""
    print("\n" + "=" * 60)
    print("Verifying Stored Verification Logs")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.zomato_edgevision
    
    try:
        # Find recent verification logs from our tests
        test_device_ids = ["device-test-001", "device-test-002"]
        
        logs = await db.verification_logs.find({
            "device_id": {"$in": test_device_ids}
        }).sort("created_at", -1).limit(10).to_list(length=10)
        
        print(f"\nFound {len(logs)} verification logs from tests:")
        print()
        
        for i, log in enumerate(logs, 1):
            print(f"Log {i}:")
            print(f"  order_id: {log['order_id']}")
            print(f"  merchant_id: {log['merchant_id']}")
            print(f"  verified_timestamp: {log['verified_timestamp']}")
            print(f"  confidence_score: {log['confidence_score']}")
            print(f"  fallback_used: {log['fallback_used']}")
            print(f"  fraud_flag: {log['fraud_flag']}")
            print(f"  processing_time_ms: {log['processing_time_ms']}")
            print(f"  device_id: {log['device_id']}")
            print()
        
        # Verify all required fields are present
        if logs:
            required_fields = [
                "order_id", "merchant_id", "verified_timestamp",
                "confidence_score", "fallback_used", "fraud_flag",
                "processing_time_ms", "device_id", "created_at"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in logs[0]:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
            else:
                print("✅ All required fields present")
            
            # Check processing time is reasonable
            if logs[0]['processing_time_ms'] < 200:
                print(f"✅ Processing time ({logs[0]['processing_time_ms']}ms) is within 200ms budget")
            else:
                print(f"⚠ Processing time ({logs[0]['processing_time_ms']}ms) exceeds 200ms budget")
        
        print("\n" + "=" * 60)
        print("✅ Verification complete!")
        print("=" * 60)
        
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(verify_stored_data())
