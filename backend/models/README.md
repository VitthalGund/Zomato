# MongoDB Schema Documentation

This directory contains the MongoDB schema definitions for the Zomato EdgeVision system.

## Collections

### 1. VerificationLog

Stores verification events from edge devices with fraud detection flags.

**Fields:**
- `order_id` (str): Unique order identifier
- `merchant_id` (str): Merchant identifier
- `verified_timestamp` (datetime): When verification occurred
- `confidence_score` (float): AI detection confidence (0.0-1.0)
- `fallback_used` (bool): Whether manual override was used
- `fraud_flag` (FraudFlag | None): Fraud detection flag
- `processing_time_ms` (int): Backend processing time
- `device_id` (str | None): Device identifier
- `created_at` (datetime): Document creation timestamp

**Indexes:**
- Compound index on `(merchant_id, verified_timestamp)` - for velocity queries
- Index on `order_id` - for fraud detection lookups
- Index on `fraud_flag` - for analytics queries

**Requirements:** 13.1, 13.2, 13.3, 13.4

---

### 2. MerchantVelocityState

Stores calculated throughput velocity metrics and KPT penalty for merchants.

**Fields:**
- `merchant_id` (str): Unique merchant identifier
- `current_velocity_orders_per_hour` (float): Recent velocity (last 15 min)
- `baseline_velocity_orders_per_hour` (float): Historical baseline velocity
- `invisible_load_ratio` (float): Ratio of current to baseline velocity
- `active_kpt_penalty_minutes` (int): Dynamic KPT penalty (0-30 minutes)
- `last_calculated` (datetime): Timestamp of last calculation
- `calculation_window_start` (datetime): Start of calculation window
- `calculation_window_end` (datetime): End of calculation window

**Indexes:**
- Unique index on `merchant_id`
- Index on `last_calculated` - for stale data cleanup
- Index on `active_kpt_penalty_minutes` - for operational dashboards

**Requirements:** 13.1, 13.2, 13.6

---

### 3. Order (Reference Schema)

Represents customer orders with items and timestamps.

**Fields:**
- `order_id` (str): Unique order identifier
- `merchant_id` (str): Merchant identifier
- `customer_id` (str): Customer identifier
- `order_creation_timestamp` (datetime): When order was created
- `item_list` (List[OrderItem]): List of ordered items
- `status` (OrderStatus): Current order status
- `assigned_rider_id` (str | None): Assigned delivery rider ID
- `rider_arrival_timestamp` (datetime | None): When rider arrived

**Indexes:**
- Unique index on `order_id`
- Index on `merchant_id` - for merchant queries
- Index on `order_creation_timestamp` - for temporal queries

**Requirements:** 13.3

---

### 4. MenuItem (Reference Schema)

Represents menu items with preparation time and complexity.

**Fields:**
- `item_id` (str): Menu item identifier
- `item_name` (str): Menu item name
- `merchant_id` (str): Merchant identifier
- `category` (str): Item category
- `prep_time_minutes` (int): Preparation time (1-120 minutes)
- `complexity_score` (int): Complexity score (1-10)

**Indexes:**
- Compound unique index on `(item_id, merchant_id)`
- Index on `merchant_id` - for merchant queries

**Requirements:** 13.4

---

## Enums

### FraudFlag

Fraud detection flags for verification events:
- `FRAUD_EMPTY_BAG`: Verification occurred before minimum prep time
- `FRAUD_GHOST_SCAN`: Verification before rider GPS arrival
- `FRAUD_TEMPORAL_ANOMALY`: Negative time delta or clock skew

### OrderStatus

Order status enumeration:
- `PENDING`: Order received, not yet preparing
- `PREPARING`: Kitchen is preparing the order
- `READY`: Order is ready for pickup
- `PICKED_UP`: Rider has picked up the order
- `DELIVERED`: Order delivered to customer

---

## Usage

```python
from models import VerificationLog, MerchantVelocityState, Order, MenuItem, FraudFlag

# Create a verification log
log = VerificationLog(
    order_id="ZOM-12345",
    merchant_id="MERCH-001",
    verified_timestamp=datetime.utcnow(),
    confidence_score=0.95,
    fallback_used=False,
    fraud_flag=None,
    processing_time_ms=45
)

# Insert into MongoDB
await db.verification_logs.insert_one(log.model_dump(by_alias=True))
```

---

## Testing

Run the test script to verify database setup:

```bash
python test_db_setup.py
```

This will:
1. Connect to MongoDB
2. Create all required indexes
3. Verify index creation
4. Display index information for each collection
