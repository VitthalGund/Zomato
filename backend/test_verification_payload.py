"""
Test VerificationPayload Pydantic model validation.

This test verifies that the VerificationPayload model correctly validates
all fields according to the requirements.
"""

import pytest
from pydantic import ValidationError
from models import VerificationPayload


def test_valid_payload():
    """Test that a valid payload passes validation."""
    payload = VerificationPayload(
        order_id="ZOM-12345",
        verified_timestamp=1705347000,
        confidence_score=0.95,
        crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        fallback_used=False,
        device_id="device-abc-123"
    )
    
    assert payload.order_id == "ZOM-12345"
    assert payload.verified_timestamp == 1705347000
    assert payload.confidence_score == 0.95
    assert payload.crypto_hash == "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    assert payload.fallback_used is False
    assert payload.device_id == "device-abc-123"


def test_valid_payload_without_device_id():
    """Test that device_id is optional."""
    payload = VerificationPayload(
        order_id="ZOM-12345",
        verified_timestamp=1705347000,
        confidence_score=0.95,
        crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        fallback_used=False
    )
    
    assert payload.device_id is None


def test_empty_order_id():
    """Test that empty order_id is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="",
            verified_timestamp=1705347000,
            confidence_score=0.95,
            crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            fallback_used=False
        )
    
    assert "order_id must be non-empty" in str(exc_info.value)


def test_whitespace_only_order_id():
    """Test that whitespace-only order_id is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="   ",
            verified_timestamp=1705347000,
            confidence_score=0.95,
            crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            fallback_used=False
        )
    
    assert "order_id must be non-empty" in str(exc_info.value)


def test_negative_timestamp():
    """Test that negative timestamp is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="ZOM-12345",
            verified_timestamp=-1,
            confidence_score=0.95,
            crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            fallback_used=False
        )
    
    assert "greater than 0" in str(exc_info.value)


def test_zero_timestamp():
    """Test that zero timestamp is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="ZOM-12345",
            verified_timestamp=0,
            confidence_score=0.95,
            crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            fallback_used=False
        )
    
    assert "greater than 0" in str(exc_info.value)


def test_confidence_score_below_range():
    """Test that confidence_score below 0.0 is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="ZOM-12345",
            verified_timestamp=1705347000,
            confidence_score=-0.1,
            crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            fallback_used=False
        )
    
    assert "greater than or equal to 0" in str(exc_info.value)


def test_confidence_score_above_range():
    """Test that confidence_score above 1.0 is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="ZOM-12345",
            verified_timestamp=1705347000,
            confidence_score=1.1,
            crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            fallback_used=False
        )
    
    assert "less than or equal to 1" in str(exc_info.value)


def test_confidence_score_at_boundaries():
    """Test that confidence_score at 0.0 and 1.0 is accepted."""
    payload_min = VerificationPayload(
        order_id="ZOM-12345",
        verified_timestamp=1705347000,
        confidence_score=0.0,
        crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        fallback_used=False
    )
    assert payload_min.confidence_score == 0.0
    
    payload_max = VerificationPayload(
        order_id="ZOM-12345",
        verified_timestamp=1705347000,
        confidence_score=1.0,
        crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        fallback_used=False
    )
    assert payload_max.confidence_score == 1.0


def test_crypto_hash_too_short():
    """Test that crypto_hash shorter than 64 characters is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="ZOM-12345",
            verified_timestamp=1705347000,
            confidence_score=0.95,
            crypto_hash="a1b2c3d4e5f6",
            fallback_used=False
        )
    
    assert "64 characters" in str(exc_info.value)


def test_crypto_hash_too_long():
    """Test that crypto_hash longer than 64 characters is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="ZOM-12345",
            verified_timestamp=1705347000,
            confidence_score=0.95,
            crypto_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567890",
            fallback_used=False
        )
    
    assert "64 characters" in str(exc_info.value)


def test_crypto_hash_invalid_hex():
    """Test that crypto_hash with non-hexadecimal characters is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        VerificationPayload(
            order_id="ZOM-12345",
            verified_timestamp=1705347000,
            confidence_score=0.95,
            crypto_hash="g1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            fallback_used=False
        )
    
    assert "valid hexadecimal string" in str(exc_info.value)


def test_crypto_hash_uppercase_normalized():
    """Test that uppercase crypto_hash is normalized to lowercase."""
    payload = VerificationPayload(
        order_id="ZOM-12345",
        verified_timestamp=1705347000,
        confidence_score=0.95,
        crypto_hash="A1B2C3D4E5F6789012345678901234567890ABCDEF1234567890ABCDEF123456",
        fallback_used=False
    )
    
    assert payload.crypto_hash == "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
