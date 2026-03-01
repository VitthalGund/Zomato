# Demo Data Seeder

This script generates demo data for the Zomato EdgeVision system to enable testing and demonstration of the velocity calculation and fraud detection features.

## What It Generates

### 1. Menu Items (13 items)
- Pizza items with 12-15 minute prep times
- Side dishes with 5-10 minute prep times
- Salads with 3 minute prep times
- Pasta dishes with 8-15 minute prep times
- Desserts with 3-7 minute prep times

### 2. Historical Verification Data (4 weeks)
- Generates data for **Friday 7PM-8PM** time window
- **20-30 orders per hour** for each week
- Realistic prep times (3-15 minutes based on menu items)
- Clean data (no fraud flags) for baseline calculation

### 3. Sample Orders
- Each order contains 1-3 random menu items
- Realistic order creation timestamps
- Verification timestamps calculated as: `order_creation_time + prep_time + buffer (1-3 min)`
- All orders marked as "READY" status

## Usage

### Prerequisites
1. MongoDB running (local or Atlas)
2. Environment variables configured in `.env`:
   ```
   MONGODB_URI=mongodb://localhost:27017
   ```

### Running the Script

```bash
# From the backend directory
python seed_demo_data.py
```

### Expected Output

```
============================================================
Zomato EdgeVision - Demo Data Seeder
============================================================

🔌 Connecting to MongoDB: mongodb://localhost:27017
✓ Successfully connected to MongoDB

📋 Seeding menu items for Demo Pizza Kitchen...
✓ Menu items: 13 inserted, 0 updated

📊 Seeding 4 weeks of historical data (Friday 7PM-8PM)...
  Week 1: 2024-02-20 - Generating 29 orders
  Week 2: 2024-02-13 - Generating 24 orders
  Week 3: 2024-02-06 - Generating 20 orders
  Week 4: 2024-01-30 - Generating 28 orders
✓ Orders: 101 inserted, 0 already existed
✓ Verification logs: 101 inserted, 0 already existed

🔍 Verifying seeded data...
  Menu items: 13
  Orders: 101
  Verification logs: 101
  Average orders per week: 25.2

✅ Demo data seeding complete!
============================================================

Demo merchant ID: MERCH-DEMO-001
Demo merchant name: Demo Pizza Kitchen
```

## Idempotency

The script is **idempotent** - you can run it multiple times without creating duplicate data:

- Uses `update_one` with `upsert=True` for menu items
- Uses `$setOnInsert` for orders and verification logs
- Checks for existing `order_id` before inserting

Running the script again will show:
```
✓ Orders: 0 inserted, 101 already existed
✓ Verification logs: 0 inserted, 101 already existed
```

## Demo Merchant Details

- **Merchant ID**: `MERCH-DEMO-001`
- **Merchant Name**: Demo Pizza Kitchen
- **Menu Items**: 13 items across 5 categories
- **Historical Data**: 4 weeks of Friday 7PM-8PM data
- **Average Orders**: ~25 orders per hour

## Testing Velocity Calculation

After seeding, you can test the velocity calculation:

1. Start the backend server:
   ```bash
   python main.py
   ```

2. The background worker will calculate velocity metrics for the demo merchant

3. Query the velocity state:
   ```bash
   # Using MongoDB shell or Compass
   db.merchant_velocity_state.findOne({"merchant_id": "MERCH-DEMO-001"})
   ```

4. Expected baseline velocity: **~25 orders/hour** (based on historical Friday 7PM-8PM data)

## Current Week Data

The script also attempts to seed data for the current week if:
- Today is Friday AND
- Current time is between 7PM-8PM

This enables real-time demo scenarios where you can see live velocity calculations.

## Clearing Demo Data

To clear all demo data and start fresh:

```javascript
// Using MongoDB shell
use zomato_edgevision

db.menu_items.deleteMany({"merchant_id": "MERCH-DEMO-001"})
db.orders.deleteMany({"merchant_id": "MERCH-DEMO-001"})
db.verification_logs.deleteMany({"merchant_id": "MERCH-DEMO-001"})
db.merchant_velocity_state.deleteMany({"merchant_id": "MERCH-DEMO-001"})
```

Then run the seed script again to regenerate fresh data.

## Troubleshooting

### Connection Error
```
Error: [Errno 111] Connection refused
```
**Solution**: Ensure MongoDB is running on `localhost:27017` or update `MONGODB_URI` in `.env`

### No Data Generated
**Solution**: Check that the script completed without errors. Verify MongoDB connection and permissions.

### Duplicate Key Error
**Solution**: This shouldn't happen due to idempotency, but if it does, clear the demo data and run again.

## Integration with Demo Endpoints

The seeded data works with the demo simulation endpoints:

- `POST /api/v1/demo/seed-historical-data` - Uses similar logic
- `POST /api/v1/demo/simulate-congestion` - Simulates velocity drops
- `POST /api/v1/demo/inject-fraud` - Tests fraud detection

See the main API documentation for details on these endpoints.
