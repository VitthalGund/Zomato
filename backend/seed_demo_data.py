"""
Seed data script for Zomato EdgeVision demo.

This script generates:
1. Demo merchant with menu items (10-15 items with varying prep times)
2. 4 weeks of historical verification data (Friday 7PM-8PM, 20-30 orders/hour)
3. Sample orders with realistic prep times (3-15 minutes)

The script is idempotent - can be run multiple times without creating duplicates.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

# Demo merchant configuration
DEMO_MERCHANT_ID = "MERCH-DEMO-001"
DEMO_MERCHANT_NAME = "Demo Pizza Kitchen"

# Menu items with varying prep times
MENU_ITEMS = [
    {"item_id": "ITEM-001", "item_name": "Margherita Pizza", "category": "Pizza", "prep_time_minutes": 12, "complexity_score": 5},
    {"item_id": "ITEM-002", "item_name": "Pepperoni Pizza", "category": "Pizza", "prep_time_minutes": 14, "complexity_score": 6},
    {"item_id": "ITEM-003", "item_name": "Veggie Supreme Pizza", "category": "Pizza", "prep_time_minutes": 15, "complexity_score": 7},
    {"item_id": "ITEM-004", "item_name": "Garlic Bread", "category": "Sides", "prep_time_minutes": 5, "complexity_score": 2},
    {"item_id": "ITEM-005", "item_name": "Caesar Salad", "category": "Salads", "prep_time_minutes": 3, "complexity_score": 1},
    {"item_id": "ITEM-006", "item_name": "Chicken Wings", "category": "Sides", "prep_time_minutes": 10, "complexity_score": 4},
    {"item_id": "ITEM-007", "item_name": "Pasta Carbonara", "category": "Pasta", "prep_time_minutes": 8, "complexity_score": 5},
    {"item_id": "ITEM-008", "item_name": "Lasagna", "category": "Pasta", "prep_time_minutes": 15, "complexity_score": 8},
    {"item_id": "ITEM-009", "item_name": "Tiramisu", "category": "Desserts", "prep_time_minutes": 3, "complexity_score": 2},
    {"item_id": "ITEM-010", "item_name": "Chocolate Lava Cake", "category": "Desserts", "prep_time_minutes": 7, "complexity_score": 6},
    {"item_id": "ITEM-011", "item_name": "BBQ Chicken Pizza", "category": "Pizza", "prep_time_minutes": 13, "complexity_score": 6},
    {"item_id": "ITEM-012", "item_name": "Hawaiian Pizza", "category": "Pizza", "prep_time_minutes": 12, "complexity_score": 5},
    {"item_id": "ITEM-013", "item_name": "Mozzarella Sticks", "category": "Sides", "prep_time_minutes": 6, "complexity_score": 3},
]


async def seed_menu_items(db):
    """
    Seed menu items for demo merchant.
    Idempotent - uses upsert to avoid duplicates.
    """
    print(f"\n📋 Seeding menu items for {DEMO_MERCHANT_NAME}...")
    
    menu_items_with_merchant = [
        {**item, "merchant_id": DEMO_MERCHANT_ID}
        for item in MENU_ITEMS
    ]
    
    inserted_count = 0
    updated_count = 0
    
    for item in menu_items_with_merchant:
        result = await db.menu_items.update_one(
            {"item_id": item["item_id"], "merchant_id": item["merchant_id"]},
            {"$set": item},
            upsert=True
        )
        if result.upserted_id:
            inserted_count += 1
        elif result.modified_count > 0:
            updated_count += 1
    
    print(f"✓ Menu items: {inserted_count} inserted, {updated_count} updated")
    return menu_items_with_merchant


async def generate_sample_order(order_number: int, creation_timestamp: datetime, menu_items: list) -> dict:
    """
    Generate a sample order with 1-3 random items.
    
    Args:
        order_number: Sequential order number for ID generation
        creation_timestamp: When the order was created
        menu_items: List of available menu items
    
    Returns:
        Order document dict
    """
    # Select 1-3 random items
    num_items = random.randint(1, 3)
    selected_items = random.sample(menu_items, num_items)
    
    order_items = []
    for item in selected_items:
        order_items.append({
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "quantity": random.randint(1, 2),
            "prep_time_minutes": item["prep_time_minutes"]
        })
    
    order = {
        "order_id": f"ZOM-DEMO-{order_number:05d}",
        "merchant_id": DEMO_MERCHANT_ID,
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "order_creation_timestamp": creation_timestamp,
        "item_list": order_items,
        "status": "READY",  # All historical orders are completed
        "assigned_rider_id": f"RIDER-{random.randint(100, 999)}",
        "rider_arrival_timestamp": None
    }
    
    return order


async def generate_verification_log(order: dict, menu_items: list) -> dict:
    """
    Generate a verification log for an order.
    
    Args:
        order: Order document
        menu_items: List of menu items for prep time lookup
    
    Returns:
        VerificationLog document dict
    """
    # Calculate realistic verification timestamp
    # Add prep time + random buffer (1-3 minutes)
    max_prep_time = max(item["prep_time_minutes"] for item in order["item_list"])
    prep_buffer_minutes = random.randint(1, 3)
    total_prep_minutes = max_prep_time + prep_buffer_minutes
    
    verified_timestamp = order["order_creation_timestamp"] + timedelta(minutes=total_prep_minutes)
    
    verification_log = {
        "order_id": order["order_id"],
        "merchant_id": order["merchant_id"],
        "verified_timestamp": verified_timestamp,
        "confidence_score": random.uniform(0.85, 0.98),
        "fallback_used": random.random() < 0.05,  # 5% fallback rate
        "fraud_flag": None,  # Clean historical data
        "processing_time_ms": random.randint(30, 100),
        "device_id": f"device-demo-{random.randint(1, 3)}",
        "created_at": verified_timestamp
    }
    
    return verification_log


async def seed_historical_data(db, menu_items: list, num_weeks: int = 4):
    """
    Seed 4 weeks of historical verification data for Friday 7PM-8PM.
    Generates 20-30 orders per hour for each week.
    
    Args:
        db: MongoDB database instance
        menu_items: List of menu items
        num_weeks: Number of weeks to generate (default 4)
    """
    print(f"\n📊 Seeding {num_weeks} weeks of historical data (Friday 7PM-8PM)...")
    
    orders_to_insert = []
    verifications_to_insert = []
    order_counter = 1
    
    current_date = datetime.utcnow()
    
    for week_offset in range(num_weeks):
        # Calculate target Friday
        target_date = current_date - timedelta(weeks=week_offset + 1)
        days_until_friday = (target_date.weekday() - 4) % 7
        friday = target_date - timedelta(days=days_until_friday)
        
        # Generate 20-30 orders for this Friday 7PM-8PM window
        num_orders = random.randint(20, 30)
        
        print(f"  Week {week_offset + 1}: {friday.strftime('%Y-%m-%d')} - Generating {num_orders} orders")
        
        for i in range(num_orders):
            # Random timestamp within 7PM-8PM window
            random_minutes = random.randint(0, 59)
            random_seconds = random.randint(0, 59)
            
            order_creation_time = friday.replace(
                hour=19,  # 7 PM
                minute=random_minutes,
                second=random_seconds,
                microsecond=0
            )
            
            # Generate order
            order = await generate_sample_order(order_counter, order_creation_time, menu_items)
            orders_to_insert.append(order)
            
            # Generate verification log
            verification = await generate_verification_log(order, menu_items)
            verifications_to_insert.append(verification)
            
            order_counter += 1
    
    # Insert orders (idempotent - skip if order_id exists)
    orders_inserted = 0
    for order in orders_to_insert:
        result = await db.orders.update_one(
            {"order_id": order["order_id"]},
            {"$setOnInsert": order},
            upsert=True
        )
        if result.upserted_id:
            orders_inserted += 1
    
    print(f"✓ Orders: {orders_inserted} inserted, {len(orders_to_insert) - orders_inserted} already existed")
    
    # Insert verification logs (idempotent - skip if order_id exists)
    verifications_inserted = 0
    for verification in verifications_to_insert:
        result = await db.verification_logs.update_one(
            {"order_id": verification["order_id"]},
            {"$setOnInsert": verification},
            upsert=True
        )
        if result.upserted_id:
            verifications_inserted += 1
    
    print(f"✓ Verification logs: {verifications_inserted} inserted, {len(verifications_to_insert) - verifications_inserted} already existed")
    
    return len(orders_to_insert), len(verifications_to_insert)


async def seed_current_week_data(db, menu_items: list):
    """
    Seed some data for the current week to enable real-time demo.
    Generates orders for today if it's Friday, or the most recent Friday.
    
    Args:
        db: MongoDB database instance
        menu_items: List of menu items
    """
    print(f"\n🕐 Seeding current week data for real-time demo...")
    
    current_date = datetime.utcnow()
    
    # Find the most recent Friday (or today if it's Friday)
    days_since_friday = (current_date.weekday() - 4) % 7
    if days_since_friday == 0:
        # Today is Friday
        target_friday = current_date
    else:
        # Go back to last Friday
        target_friday = current_date - timedelta(days=days_since_friday)
    
    # Check if we're within the 7PM-8PM window or past it
    current_hour = current_date.hour
    
    if target_friday.date() == current_date.date() and 19 <= current_hour < 20:
        # We're in the live window - generate some recent orders
        print(f"  Live window detected! Generating recent orders...")
        num_orders = random.randint(5, 10)
        
        orders_to_insert = []
        verifications_to_insert = []
        
        # Generate orders in the last 30 minutes
        for i in range(num_orders):
            minutes_ago = random.randint(5, 30)
            order_creation_time = current_date - timedelta(minutes=minutes_ago)
            order_creation_time = order_creation_time.replace(second=0, microsecond=0)
            
            order = await generate_sample_order(90000 + i, order_creation_time, menu_items)
            orders_to_insert.append(order)
            
            verification = await generate_verification_log(order, menu_items)
            verifications_to_insert.append(verification)
        
        # Insert orders
        orders_inserted = 0
        for order in orders_to_insert:
            result = await db.orders.update_one(
                {"order_id": order["order_id"]},
                {"$setOnInsert": order},
                upsert=True
            )
            if result.upserted_id:
                orders_inserted += 1
        
        # Insert verification logs
        verifications_inserted = 0
        for verification in verifications_to_insert:
            result = await db.verification_logs.update_one(
                {"order_id": verification["order_id"]},
                {"$setOnInsert": verification},
                upsert=True
            )
            if result.upserted_id:
                verifications_inserted += 1
        
        print(f"✓ Current week: {orders_inserted} orders, {verifications_inserted} verifications")
    else:
        print(f"  Not in live window (Friday 7PM-8PM), skipping current week data")


async def verify_seeded_data(db):
    """
    Verify that data was seeded correctly by querying the database.
    
    Args:
        db: MongoDB database instance
    """
    print(f"\n🔍 Verifying seeded data...")
    
    # Count menu items
    menu_count = await db.menu_items.count_documents({"merchant_id": DEMO_MERCHANT_ID})
    print(f"  Menu items: {menu_count}")
    
    # Count orders
    order_count = await db.orders.count_documents({"merchant_id": DEMO_MERCHANT_ID})
    print(f"  Orders: {order_count}")
    
    # Count verification logs
    verification_count = await db.verification_logs.count_documents({"merchant_id": DEMO_MERCHANT_ID})
    print(f"  Verification logs: {verification_count}")
    
    # Calculate average orders per Friday 7PM-8PM
    if verification_count > 0:
        # Group by week and count
        pipeline = [
            {"$match": {"merchant_id": DEMO_MERCHANT_ID, "fraud_flag": None}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$verified_timestamp"},
                    "week": {"$week": "$verified_timestamp"}
                },
                "count": {"$sum": 1}
            }}
        ]
        
        weekly_counts = await db.verification_logs.aggregate(pipeline).to_list(length=100)
        
        if weekly_counts:
            avg_orders = sum(week["count"] for week in weekly_counts) / len(weekly_counts)
            print(f"  Average orders per week: {avg_orders:.1f}")
    
    print(f"\n✅ Data verification complete!")


async def main():
    """Main function to seed all demo data."""
    print("=" * 60)
    print("Zomato EdgeVision - Demo Data Seeder")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    print(f"\n🔌 Connecting to MongoDB: {mongo_uri}")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.zomato_edgevision
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("✓ Successfully connected to MongoDB")
        
        # Seed menu items
        menu_items = await seed_menu_items(db)
        
        # Seed historical data (4 weeks)
        await seed_historical_data(db, menu_items, num_weeks=4)
        
        # Seed current week data (if applicable)
        await seed_current_week_data(db, menu_items)
        
        # Verify seeded data
        await verify_seeded_data(db)
        
        print("\n" + "=" * 60)
        print("✅ Demo data seeding complete!")
        print("=" * 60)
        print(f"\nDemo merchant ID: {DEMO_MERCHANT_ID}")
        print(f"Demo merchant name: {DEMO_MERCHANT_NAME}")
        print(f"Menu items: {len(MENU_ITEMS)}")
        print("\nYou can now run the backend server and test the velocity calculation.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        client.close()
        print("\n🔌 Closed MongoDB connection")


if __name__ == "__main__":
    asyncio.run(main())
