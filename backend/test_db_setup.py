"""
Test script to verify MongoDB connection and index creation.

This script connects to MongoDB and verifies that all collections
and indexes are properly created.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


async def test_db_setup():
    """Test MongoDB connection and index creation."""
    print("Testing MongoDB setup...")
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    print(f"Connecting to: {mongo_uri}")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.zomato_edgevision
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("✓ Successfully connected to MongoDB")
        
        # Create indexes (same as in main.py)
        print("\nCreating indexes...")
        
        # VerificationLog indexes
        await db.verification_logs.create_index([("merchant_id", 1), ("verified_timestamp", 1)])
        await db.verification_logs.create_index("order_id")
        await db.verification_logs.create_index("fraud_flag")
        print("✓ Created VerificationLog indexes")
        
        # MerchantVelocityState indexes
        await db.merchant_velocity_state.create_index("merchant_id", unique=True)
        await db.merchant_velocity_state.create_index("last_calculated")
        await db.merchant_velocity_state.create_index("active_kpt_penalty_minutes")
        print("✓ Created MerchantVelocityState indexes")
        
        # Order indexes
        await db.orders.create_index("order_id", unique=True)
        await db.orders.create_index("merchant_id")
        await db.orders.create_index("order_creation_timestamp")
        print("✓ Created Order indexes")
        
        # MenuItem indexes
        await db.menu_items.create_index([("item_id", 1), ("merchant_id", 1)], unique=True)
        await db.menu_items.create_index("merchant_id")
        print("✓ Created MenuItem indexes")
        
        # List all indexes for verification
        print("\nVerifying indexes...")
        
        collections = {
            "verification_logs": ["merchant_id_1_verified_timestamp_1", "order_id_1", "fraud_flag_1"],
            "merchant_velocity_state": ["merchant_id_1", "last_calculated_1", "active_kpt_penalty_minutes_1"],
            "orders": ["order_id_1", "merchant_id_1", "order_creation_timestamp_1"],
            "menu_items": ["item_id_1_merchant_id_1", "merchant_id_1"]
        }
        
        for collection_name, expected_indexes in collections.items():
            collection = db[collection_name]
            indexes = await collection.index_information()
            print(f"\n{collection_name} indexes:")
            for index_name in indexes:
                if index_name != "_id_":  # Skip default _id index
                    print(f"  - {index_name}")
        
        print("\n✓ All indexes created successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        raise
    finally:
        client.close()
        print("\nClosed MongoDB connection")


if __name__ == "__main__":
    asyncio.run(test_db_setup())
