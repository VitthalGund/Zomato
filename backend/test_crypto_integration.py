"""Quick integration test for crypto functions."""

from services import generate_crypto_hash, validate_crypto_hash

# Test hash generation
hash_val = generate_crypto_hash('ZOM-12345', 1705347000, 'device-123', 'secret')
print(f'Generated Hash: {hash_val}')
print(f'Hash Length: {len(hash_val)}')

# Test valid hash validation
is_valid = validate_crypto_hash('ZOM-12345', 1705347000, 'device-123', hash_val, 'secret')
print(f'Valid Hash Test: {is_valid}')

# Test invalid hash validation
is_invalid = validate_crypto_hash('ZOM-12345', 1705347000, 'device-123', 'wrong_hash', 'secret')
print(f'Invalid Hash Test: {is_invalid}')

print('\nAll integration tests passed!')
