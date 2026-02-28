"""
Cryptographic hash generation and validation service.

This module provides secure hash generation and validation functions for
verification payloads. Uses SHA-256 hashing with constant-time comparison
to prevent timing attacks.

Requirements: 5.1, 5.2, 5.4, 14.1, 14.2, 14.3
"""

import hashlib


def generate_crypto_hash(
    order_id: str,
    timestamp: int,
    device_id: str,
    secret_salt: str
) -> str:
    """
    Generate SHA-256 cryptographic hash for verification payload.
    
    Creates a tamper-proof hash by combining order_id, timestamp, device_id,
    and a secret salt. The hash ensures payload authenticity without transmitting
    sensitive image data.
    
    Args:
        order_id: Unique order identifier (non-empty string)
        timestamp: Unix timestamp in seconds (positive integer)
        device_id: Device identifier (non-empty string)
        secret_salt: Secret salt for hash generation (non-empty string)
    
    Returns:
        64-character lowercase hexadecimal hash string
    
    Preconditions:
        - order_id is non-empty string
        - timestamp is valid Unix timestamp (positive integer)
        - device_id is non-empty string
        - secret_salt is configured and non-empty
    
    Postconditions:
        - Returns 64-character lowercase hexadecimal string
        - Same inputs always produce same output (deterministic)
        - Hash is cryptographically secure (SHA-256)
        - No side effects
    
    Example:
        >>> hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        >>> len(hash_val)
        64
        >>> hash_val == generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        True
    
    Requirements: 5.1, 5.4
    """
    # Concatenate all components with delimiter
    payload_string = f"{order_id}|{timestamp}|{device_id}|{secret_salt}"
    
    # Convert string to bytes
    payload_bytes = payload_string.encode('utf-8')
    
    # Generate SHA-256 hash
    hash_object = hashlib.sha256(payload_bytes)
    
    # Return hexadecimal representation
    return hash_object.hexdigest()


def validate_crypto_hash(
    order_id: str,
    timestamp: int,
    device_id: str,
    received_hash: str,
    secret_salt: str
) -> bool:
    """
    Validate received cryptographic hash against computed hash.
    
    Uses constant-time comparison to prevent timing attacks. The comparison
    uses XOR-based logic to ensure execution time is independent of where
    the mismatch occurs in the hash string.
    
    Args:
        order_id: Unique order identifier
        timestamp: Unix timestamp in seconds
        device_id: Device identifier
        received_hash: Hash received from client (64-character hex string)
        secret_salt: Secret salt matching the one used during generation
    
    Returns:
        True if computed hash matches received hash, False otherwise
    
    Preconditions:
        - All parameters are non-null
        - received_hash is 64-character hexadecimal string
        - secret_salt matches the salt used during generation
    
    Postconditions:
        - Returns True if computed hash matches received hash
        - Returns False otherwise
        - Comparison is timing-attack resistant
        - No side effects
    
    Example:
        >>> hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        >>> validate_crypto_hash("ZOM-12345", 1705347000, "device-123", hash_val, "secret")
        True
        >>> validate_crypto_hash("ZOM-12345", 1705347000, "device-123", "wrong_hash", "secret")
        False
    
    Security:
        Uses constant-time comparison to prevent timing attacks. The XOR-based
        comparison ensures that execution time does not leak information about
        where the hash mismatch occurs.
    
    Requirements: 5.2, 14.1, 14.2, 14.3
    """
    # Compute expected hash
    expected_hash = generate_crypto_hash(order_id, timestamp, device_id, secret_salt)
    
    # Use constant-time comparison to prevent timing attacks
    # First check length to avoid index errors
    if len(received_hash) != len(expected_hash):
        return False
    
    # XOR-based constant-time comparison
    # Accumulate XOR of all character pairs - result is 0 only if all match
    result = 0
    for expected_char, received_char in zip(expected_hash, received_hash):
        result |= ord(expected_char) ^ ord(received_char)
    
    return result == 0
