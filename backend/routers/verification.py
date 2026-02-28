"""
Verification endpoint router.

This module implements the POST /api/v1/verify-order endpoint for ingesting
verification payloads from edge devices. Handles cryptographic validation,
fraud detection, and data persistence.

Requirements: 7.1, 7.2, 7.3, 7.4, 13.1, 13.2
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import os
import logging

from backend.models.schemas import VerificationPayload, VerificationLog
from backend.services.crypto import validate_crypto_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["verification"])


def get_db():
    """Dependency to get database instance."""
    from backend.main import db
    return db


def get_secret_salt():
    """Dependency to get SECRET_SALT from environment."""
    secret_salt = os.getenv("SECRET_SALT")
    if not secret_salt:
        logger.error("SECRET_SALT environment variable not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )
    return secret_salt


async def get_merchant_id_from_order(order_id: str, db) -> str:
    """
    Helper function to fetch merchant_id from order.
    
    Args:
        order_id: Unique order identifier
        db: MongoDB database instance
    
    Returns:
        merchant_id string
    
    Raises:
        HTTPException: 404 if order not found
    """
    order = await db.orders.find_one({"order_id": order_id})
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    return order["merchant_id"]


@router.post("/verify-order")
async def verify_order(
    payload: VerificationPayload,
    db=Depends(get_db),
    secret_salt: str = Depends(get_secret_salt)
):
    """
    Ingest verification payload from edge device.
    
    This endpoint receives verification payloads from mobile devices, validates
    the cryptographic hash for authenticity, and stores the verification log
    in MongoDB. Returns processing time metrics.
    
    Args:
        payload: VerificationPayload containing order_id, timestamp, hash, etc.
        db: MongoDB database instance (injected)
        secret_salt: SECRET_SALT from environment (injected)
    
    Returns:
        dict: Success response with processing_time_ms
    
    Raises:
        HTTPException: 401 if crypto_hash is invalid
        HTTPException: 404 if order not found
        HTTPException: 503 if MongoDB is unavailable
    
    Requirements:
        - 7.1: Validate cryptographic hash
        - 7.2: Return HTTP 401 if hash invalid
        - 7.3: Store verification log in MongoDB
        - 7.4: Complete processing within 200ms for 95% of requests
        - 13.1: Store VerificationLog document
        - 13.2: Create compound index on (merchant_id, verified_timestamp)
    
    Example:
        POST /api/v1/verify-order
        {
            "order_id": "ZOM-12345",
            "verified_timestamp": 1705347000,
            "confidence_score": 0.95,
            "crypto_hash": "a1b2c3...",
            "fallback_used": false,
            "device_id": "device-123"
        }
        
        Response:
        {
            "status": "success",
            "processing_time_ms": 45
        }
    """
    start_time = datetime.utcnow()
    
    # Step 1: Validate cryptographic hash
    # Requirements: 7.1, 14.1, 14.2
    device_id = payload.device_id or "unknown"
    
    is_valid = validate_crypto_hash(
        order_id=payload.order_id,
        timestamp=payload.verified_timestamp,
        device_id=device_id,
        received_hash=payload.crypto_hash,
        secret_salt=secret_salt
    )
    
    # Step 2: Return HTTP 401 if hash invalid
    # Requirements: 7.2, 14.4
    if not is_valid:
        # Log security event
        logger.warning(
            f"Invalid crypto_hash for order {payload.order_id}, "
            f"device_id: {device_id}, "
            f"timestamp: {payload.verified_timestamp}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid crypto hash"
        )
    
    try:
        # Step 3: Get merchant_id from order
        merchant_id = await get_merchant_id_from_order(payload.order_id, db)
        
        # Step 4: Store VerificationLog in MongoDB
        # Requirements: 7.3, 13.1, 13.2
        verification_log = {
            "order_id": payload.order_id,
            "merchant_id": merchant_id,
            "verified_timestamp": datetime.fromtimestamp(payload.verified_timestamp),
            "confidence_score": payload.confidence_score,
            "fallback_used": payload.fallback_used,
            "fraud_flag": None,  # Will be set by fraud detection in task 5.2
            "processing_time_ms": 0,  # Will be updated below
            "device_id": device_id,
            "created_at": datetime.utcnow()
        }
        
        # Insert into MongoDB
        result = await db.verification_logs.insert_one(verification_log)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Update processing time in the document
        await db.verification_logs.update_one(
            {"_id": result.inserted_id},
            {"$set": {"processing_time_ms": int(processing_time)}}
        )
        
        logger.info(
            f"Verification successful for order {payload.order_id}, "
            f"merchant {merchant_id}, "
            f"processing_time: {int(processing_time)}ms"
        )
        
        # Step 5: Return success response with processing_time_ms
        # Requirements: 7.4
        return {
            "status": "success",
            "processing_time_ms": int(processing_time)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for order not found)
        raise
    except Exception as e:
        # Handle MongoDB connection errors
        # Requirements: 7.4 (Handle MongoDB errors with HTTP 503)
        logger.error(f"MongoDB error during verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )
