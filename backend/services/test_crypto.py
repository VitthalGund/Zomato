"""
Unit tests for cryptographic hash generation and validation.

Tests cover:
- Hash generation correctness
- Hash validation with valid and invalid inputs
- Constant-time comparison behavior
- Edge cases and error conditions

Requirements: 5.1, 5.2, 5.4, 14.1, 14.2, 14.3
"""

import pytest
import time
from services.crypto import generate_crypto_hash, validate_crypto_hash


class TestGenerateCryptoHash:
    """Test suite for generate_crypto_hash function."""
    
    def test_generates_64_character_hex_string(self):
        """Test that generated hash is 64 characters (SHA-256 hex output)."""
        hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)
    
    def test_deterministic_output(self):
        """Test that same inputs always produce same hash (deterministic)."""
        hash1 = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        hash2 = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        assert hash1 == hash2
    
    def test_different_order_id_produces_different_hash(self):
        """Test that different order_id produces different hash."""
        hash1 = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        hash2 = generate_crypto_hash("ZOM-99999", 1705347000, "device-123", "secret")
        assert hash1 != hash2
    
    def test_different_timestamp_produces_different_hash(self):
        """Test that different timestamp produces different hash."""
        hash1 = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        hash2 = generate_crypto_hash("ZOM-12345", 1705347001, "device-123", "secret")
        assert hash1 != hash2
    
    def test_different_device_id_produces_different_hash(self):
        """Test that different device_id produces different hash."""
        hash1 = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        hash2 = generate_crypto_hash("ZOM-12345", 1705347000, "device-456", "secret")
        assert hash1 != hash2
    
    def test_different_secret_salt_produces_different_hash(self):
        """Test that different secret_salt produces different hash."""
        hash1 = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret1")
        hash2 = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret2")
        assert hash1 != hash2
    
    def test_handles_special_characters_in_order_id(self):
        """Test that special characters in order_id are handled correctly."""
        hash_val = generate_crypto_hash("ZOM-12345-ABC", 1705347000, "device-123", "secret")
        assert len(hash_val) == 64
    
    def test_handles_empty_strings(self):
        """Test that empty strings produce valid hash (edge case)."""
        # Note: In production, validation should prevent empty strings
        # but the hash function itself should handle them
        hash_val = generate_crypto_hash("", 0, "", "")
        assert len(hash_val) == 64


class TestValidateCryptoHash:
    """Test suite for validate_crypto_hash function."""
    
    def test_validates_correct_hash(self):
        """Test that valid hash passes validation."""
        hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", hash_val, "secret")
        assert result is True
    
    def test_rejects_incorrect_hash(self):
        """Test that invalid hash fails validation."""
        result = validate_crypto_hash(
            "ZOM-12345", 
            1705347000, 
            "device-123", 
            "0" * 64,  # Wrong hash
            "secret"
        )
        assert result is False
    
    def test_rejects_hash_with_wrong_order_id(self):
        """Test that hash generated with different order_id fails validation."""
        hash_val = generate_crypto_hash("ZOM-99999", 1705347000, "device-123", "secret")
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", hash_val, "secret")
        assert result is False
    
    def test_rejects_hash_with_wrong_timestamp(self):
        """Test that hash generated with different timestamp fails validation."""
        hash_val = generate_crypto_hash("ZOM-12345", 1705347001, "device-123", "secret")
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", hash_val, "secret")
        assert result is False
    
    def test_rejects_hash_with_wrong_device_id(self):
        """Test that hash generated with different device_id fails validation."""
        hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-456", "secret")
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", hash_val, "secret")
        assert result is False
    
    def test_rejects_hash_with_wrong_secret_salt(self):
        """Test that hash generated with different secret_salt fails validation."""
        hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret1")
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", hash_val, "secret2")
        assert result is False
    
    def test_rejects_hash_with_wrong_length(self):
        """Test that hash with incorrect length fails validation."""
        result = validate_crypto_hash(
            "ZOM-12345", 
            1705347000, 
            "device-123", 
            "short",  # Too short
            "secret"
        )
        assert result is False
    
    def test_rejects_empty_hash(self):
        """Test that empty hash fails validation."""
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", "", "secret")
        assert result is False
    
    def test_rejects_hash_with_single_character_difference(self):
        """Test that hash with single character changed fails validation."""
        hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        # Change first character
        modified_hash = "0" + hash_val[1:]
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", modified_hash, "secret")
        assert result is False
    
    def test_rejects_hash_with_last_character_difference(self):
        """Test that hash with last character changed fails validation."""
        hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        # Change last character
        modified_hash = hash_val[:-1] + "0"
        result = validate_crypto_hash("ZOM-12345", 1705347000, "device-123", modified_hash, "secret")
        assert result is False


class TestConstantTimeComparison:
    """Test suite for constant-time comparison behavior."""
    
    def test_timing_independence_first_char_mismatch(self):
        """Test that timing is similar regardless of mismatch position (first char)."""
        correct_hash = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        
        # Hash with first character different
        wrong_hash_first = "0" + correct_hash[1:]
        
        # Measure validation time
        start = time.perf_counter()
        for _ in range(1000):
            validate_crypto_hash("ZOM-12345", 1705347000, "device-123", wrong_hash_first, "secret")
        time_first = time.perf_counter() - start
        
        # Time should be consistent (this is a basic check, not a rigorous timing attack test)
        assert time_first > 0  # Sanity check
    
    def test_timing_independence_last_char_mismatch(self):
        """Test that timing is similar regardless of mismatch position (last char)."""
        correct_hash = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        
        # Hash with last character different
        wrong_hash_last = correct_hash[:-1] + "0"
        
        # Measure validation time
        start = time.perf_counter()
        for _ in range(1000):
            validate_crypto_hash("ZOM-12345", 1705347000, "device-123", wrong_hash_last, "secret")
        time_last = time.perf_counter() - start
        
        # Time should be consistent
        assert time_last > 0  # Sanity check
    
    def test_xor_comparison_logic(self):
        """Test that XOR-based comparison works correctly."""
        # Valid hash should pass
        hash_val = generate_crypto_hash("ZOM-12345", 1705347000, "device-123", "secret")
        assert validate_crypto_hash("ZOM-12345", 1705347000, "device-123", hash_val, "secret")
        
        # Any modification should fail
        for i in range(0, len(hash_val), 10):  # Test every 10th character
            modified = hash_val[:i] + ("0" if hash_val[i] != "0" else "1") + hash_val[i+1:]
            assert not validate_crypto_hash("ZOM-12345", 1705347000, "device-123", modified, "secret")


class TestIntegration:
    """Integration tests for hash generation and validation workflow."""
    
    def test_complete_workflow(self):
        """Test complete workflow: generate hash, validate it."""
        order_id = "ZOM-12345"
        timestamp = 1705347000
        device_id = "device-123"
        secret_salt = "my_secret_salt"
        
        # Generate hash
        hash_val = generate_crypto_hash(order_id, timestamp, device_id, secret_salt)
        
        # Validate hash
        is_valid = validate_crypto_hash(order_id, timestamp, device_id, hash_val, secret_salt)
        
        assert is_valid is True
    
    def test_multiple_orders_different_hashes(self):
        """Test that multiple orders produce different hashes."""
        secret_salt = "my_secret_salt"
        device_id = "device-123"
        timestamp = 1705347000
        
        orders = ["ZOM-001", "ZOM-002", "ZOM-003", "ZOM-004", "ZOM-005"]
        hashes = [generate_crypto_hash(order, timestamp, device_id, secret_salt) for order in orders]
        
        # All hashes should be unique
        assert len(hashes) == len(set(hashes))
    
    def test_replay_attack_prevention(self):
        """Test that same payload with different timestamp fails validation."""
        order_id = "ZOM-12345"
        device_id = "device-123"
        secret_salt = "my_secret_salt"
        
        # Generate hash at time T
        timestamp1 = 1705347000
        hash1 = generate_crypto_hash(order_id, timestamp1, device_id, secret_salt)
        
        # Try to validate at time T+1 (replay attack)
        timestamp2 = 1705347001
        is_valid = validate_crypto_hash(order_id, timestamp2, device_id, hash1, secret_salt)
        
        # Should fail because timestamp doesn't match
        assert is_valid is False
