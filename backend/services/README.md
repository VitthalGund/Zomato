# Services Module

This module contains business logic services for the Zomato EdgeVision backend.

## Crypto Service

The crypto service provides secure hash generation and validation for verification payloads.

### Functions

#### `generate_crypto_hash(order_id, timestamp, device_id, secret_salt)`

Generates a SHA-256 cryptographic hash for verification payloads.

**Parameters:**
- `order_id` (str): Unique order identifier
- `timestamp` (int): Unix timestamp in seconds
- `device_id` (str): Device identifier
- `secret_salt` (str): Secret salt for hash generation

**Returns:**
- `str`: 64-character lowercase hexadecimal hash string

**Example:**
```python
from services import generate_crypto_hash

hash_val = generate_crypto_hash(
    order_id="ZOM-12345",
    timestamp=1705347000,
    device_id="device-123",
    secret_salt="my_secret_salt"
)
print(hash_val)  # 64-character hex string
```

#### `validate_crypto_hash(order_id, timestamp, device_id, received_hash, secret_salt)`

Validates a received cryptographic hash using constant-time comparison.

**Parameters:**
- `order_id` (str): Unique order identifier
- `timestamp` (int): Unix timestamp in seconds
- `device_id` (str): Device identifier
- `received_hash` (str): Hash received from client
- `secret_salt` (str): Secret salt matching the one used during generation

**Returns:**
- `bool`: True if hash is valid, False otherwise

**Example:**
```python
from services import generate_crypto_hash, validate_crypto_hash

# Generate hash
hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")

# Validate hash
is_valid = validate_crypto_hash(
    order_id="ZOM-12345",
    timestamp=1705347000,
    device_id="device-123",
    received_hash=hash_val,
    secret_salt="secret"
)
print(is_valid)  # True
```

### Security Features

1. **SHA-256 Hashing**: Uses cryptographically secure SHA-256 algorithm
2. **Constant-Time Comparison**: Prevents timing attacks using XOR-based comparison
3. **Tamper-Proof**: Any modification to the payload invalidates the hash
4. **Replay Attack Prevention**: Timestamp inclusion prevents replay attacks

### Requirements Satisfied

- **Requirement 5.1**: SHA-256 hash generation from OrderID, Timestamp, DeviceID, and SECRET_SALT
- **Requirement 5.2**: JSON payload construction without raw image data
- **Requirement 5.4**: Hash format: Hash(OrderID|Timestamp|DeviceID|SECRET_SALT)
- **Requirement 14.1**: Constant-time comparison for hash validation
- **Requirement 14.2**: XOR-based comparison to prevent timing attacks
- **Requirement 14.3**: Hash length validation (64 characters)

### Testing

Run the test suite:
```bash
pytest services/test_crypto.py -v
```

Run integration test:
```bash
python test_crypto_integration.py
```

### Implementation Details

The hash generation uses the following format:
```
payload_string = f"{order_id}|{timestamp}|{device_id}|{secret_salt}"
hash = SHA256(payload_string.encode('utf-8')).hexdigest()
```

The validation uses XOR-based constant-time comparison:
```python
result = 0
for expected_char, received_char in zip(expected_hash, received_hash):
    result |= ord(expected_char) ^ ord(received_char)
return result == 0
```

This ensures that the execution time is independent of where the mismatch occurs in the hash string, preventing timing attacks.
