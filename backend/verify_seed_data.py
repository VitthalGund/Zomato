"""
Quick verification script to check seeded demo data.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


async def verify_data():
    """Verify seeded demo data."""
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.zomato_edgevision
    
    try:
        print("Verifying Demo Data")
        print("=" * 50)
        
        # Count documents
        menu_count = await db.menu_items.count_documents({"merchant_id": "MERCH-DEMO-001"})
        order_count = await db.orders.count_documents({"merchant_id": "MERCH-DEMO-001"})
        verification_count = await db.verification_logs.count_documents({"merchant_id": "MERCH-DEMO-001"})
        
        print(f"Menu Items: {menu_count}")
        print(f"Orders: {order_count}")
        print(f"Verifications: {verification_count}")
        
        # Sample order
        sample_order = await db.orders.find_one({"merchant_id": "MERCH-DEMO-001"})
        if sample_order:
            print(f"\nSample Order:")
            print(f"  ID: {sample_order['order_id']}")
            print(f"  Items: {len(sample_order['item_list'])}")
            print(f"  Created: {sample_order['order_creation_timestamp']}")
            for item in sample_order['item_list']:
                print(f"    - {item['item_name']} (prep: {item['prep_time_minutes']} min)")
        
        # Sample verification
        sample_verification = await db.verification_logs.find_one({"merchant_id": "MERCH-DEMO-001"})
        if sample_verification:
            print(f"\nSample Verification:")
            print(f"  Order ID: {sample_verification['order_id']}")
            print(f"  Confidence: {sample_verification['confidence_score']:.2f}")
            print(f"  Verified: {sample_verification['verified_timestamp']}")
            print(f"  Fraud Flag: {sample_verification['fraud_flag']}")
        
        # Check time distribution
        print(f"\nTime Distribution:")
        pipeline = [
            {"$match": {"merchant_id": "MERCH-DEMO-001"}},
            {"$group": {
                "_id": {
                    "hour": {"$hour": "$verified_timestamp"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.hour": 1}}
        ]
        
        hourly_counts = await db.verification_logs.aggregate(pipeline).to_list(length=100)
        for hour_data in hourly_counts:
            hour = hour_data["_id"]["hour"]
            count = hour_data["count"]
            print(f"  Hour {hour:02d}: {count} verifications")
        
        print("\n" + "=" * 50)
        print("✅ Verification complete!")
        
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(verify_data())
