"""
MongoDB schema models for Zomato EdgeVision.

This module defines Pydantic models for all MongoDB collections used in the system.
Models include validation rules and are used for both API request/response validation
and database document structure.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VerificationPayload(BaseModel):
    """
    Verification payload received from edge devices.
    
    This model validates incoming verification requests from mobile devices.
    Contains cryptographic hash for authenticity verification and metadata
    about the verification event.
    
    Validation Rules:
    - order_id must be non-empty string
    - verified_timestamp must be positive integer (Unix timestamp)
    - confidence_score must be in range [0.0, 1.0]
    - crypto_hash must be exactly 64 characters (SHA-256 hex string)
    - fallback_used must be boolean
    - device_id is optional
    """
    order_id: str = Field(..., description="Unique order identifier")
    verified_timestamp: int = Field(..., gt=0, description="Unix timestamp when verification occurred")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI detection confidence score")
    crypto_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash for authenticity")
    fallback_used: bool = Field(..., description="Whether manual override was used")
    device_id: Optional[str] = Field(None, description="Device identifier for security tracking")
    
    @field_validator('order_id')
    @classmethod
    def validate_order_id(cls, v: str) -> str:
        """Validate order_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("order_id must be non-empty")
        return v
    
    @field_validator('crypto_hash')
    @classmethod
    def validate_crypto_hash(cls, v: str) -> str:
        """Validate crypto_hash is 64-character hexadecimal string."""
        if len(v) != 64:
            raise ValueError("crypto_hash must be exactly 64 characters")
        # Verify it's a valid hexadecimal string
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("crypto_hash must be a valid hexadecimal string")
        return v.lower()  # Normalize to lowercase
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ZOM-12345",
                "verified_timestamp": 1705347000,
                "confidence_score": 0.95,
                "crypto_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
                "fallback_used": False,
                "device_id": "device-abc-123"
            }
        }


class FraudFlag(str, Enum):
    """Fraud detection flags for verification events."""
    FRAUD_EMPTY_BAG = "FRAUD_EMPTY_BAG"
    FRAUD_GHOST_SCAN = "FRAUD_GHOST_SCAN"
    FRAUD_TEMPORAL_ANOMALY = "FRAUD_TEMPORAL_ANOMALY"


class VerificationLog(BaseModel):
    """
    Verification log document stored in MongoDB.
    
    Represents a single verification event from an edge device.
    Includes fraud detection flags and processing metrics.
    
    Indexes:
    - Compound index on (merchant_id, verified_timestamp) for velocity queries
    - Index on order_id for fraud detection lookups
    - Index on fraud_flag for analytics queries
    """
    order_id: str = Field(..., description="Unique order identifier (e.g., ZOM-12345)")
    merchant_id: str = Field(..., description="Merchant identifier")
    verified_timestamp: datetime = Field(..., description="Timestamp when verification occurred")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI detection confidence score")
    fallback_used: bool = Field(..., description="Whether manual override was used")
    fraud_flag: Optional[FraudFlag] = Field(None, description="Fraud detection flag if applicable")
    processing_time_ms: int = Field(..., gt=0, description="Backend processing time in milliseconds")
    device_id: Optional[str] = Field(None, description="Device identifier for security tracking")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Document creation timestamp")
    
    @field_validator('order_id')
    @classmethod
    def validate_order_id(cls, v: str) -> str:
        """Validate order_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("order_id must be non-empty")
        return v
    
    @field_validator('merchant_id')
    @classmethod
    def validate_merchant_id(cls, v: str) -> str:
        """Validate merchant_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("merchant_id must be non-empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ZOM-12345",
                "merchant_id": "MERCH-001",
                "verified_timestamp": "2024-01-15T19:30:00Z",
                "confidence_score": 0.95,
                "fallback_used": False,
                "fraud_flag": None,
                "processing_time_ms": 45,
                "device_id": "device-abc-123",
                "created_at": "2024-01-15T19:30:00Z"
            }
        }


class MerchantVelocityState(BaseModel):
    """
    Merchant velocity state document stored in MongoDB.
    
    Stores calculated throughput velocity metrics and KPT penalty for a merchant.
    Updated by background worker every 5 minutes for active merchants.
    
    Indexes:
    - Unique index on merchant_id
    - Index on last_calculated for stale data cleanup
    - Index on active_kpt_penalty_minutes for operational dashboards
    """
    merchant_id: str = Field(..., description="Unique merchant identifier")
    current_velocity_orders_per_hour: float = Field(..., ge=0.0, description="Recent velocity (last 15 min)")
    baseline_velocity_orders_per_hour: float = Field(..., gt=0.0, description="Historical baseline velocity")
    invisible_load_ratio: float = Field(..., ge=0.0, description="Ratio of current to baseline velocity")
    active_kpt_penalty_minutes: int = Field(..., ge=0, le=30, description="Dynamic KPT penalty in minutes")
    last_calculated: datetime = Field(..., description="Timestamp of last calculation")
    calculation_window_start: datetime = Field(..., description="Start of calculation window")
    calculation_window_end: datetime = Field(..., description="End of calculation window")
    
    @field_validator('merchant_id')
    @classmethod
    def validate_merchant_id(cls, v: str) -> str:
        """Validate merchant_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("merchant_id must be non-empty")
        return v
    
    @field_validator('calculation_window_end')
    @classmethod
    def validate_window_order(cls, v: datetime, info) -> datetime:
        """Validate calculation_window_end is after calculation_window_start."""
        if 'calculation_window_start' in info.data:
            if v <= info.data['calculation_window_start']:
                raise ValueError("calculation_window_end must be after calculation_window_start")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "MERCH-001",
                "current_velocity_orders_per_hour": 15.0,
                "baseline_velocity_orders_per_hour": 25.0,
                "invisible_load_ratio": 0.6,
                "active_kpt_penalty_minutes": 10,
                "last_calculated": "2024-01-15T19:30:00Z",
                "calculation_window_start": "2024-01-15T19:15:00Z",
                "calculation_window_end": "2024-01-15T19:30:00Z"
            }
        }


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    READY = "READY"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"


class OrderItem(BaseModel):
    """Individual item in an order."""
    item_id: str = Field(..., description="Menu item identifier")
    item_name: str = Field(..., description="Menu item name")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    prep_time_minutes: int = Field(..., gt=0, description="Preparation time in minutes")
    
    @field_validator('item_id', 'item_name')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field must be non-empty")
        return v


class Order(BaseModel):
    """
    Order document stored in MongoDB (reference schema).
    
    Represents a customer order with items and timestamps.
    Used for fraud detection to validate verification timing.
    
    Indexes:
    - Unique index on order_id
    - Index on merchant_id for merchant queries
    - Index on order_creation_timestamp for temporal queries
    """
    order_id: str = Field(..., description="Unique order identifier")
    merchant_id: str = Field(..., description="Merchant identifier")
    customer_id: str = Field(..., description="Customer identifier")
    order_creation_timestamp: datetime = Field(..., description="When order was created")
    item_list: List[OrderItem] = Field(..., min_length=1, description="List of ordered items")
    status: OrderStatus = Field(..., description="Current order status")
    assigned_rider_id: Optional[str] = Field(None, description="Assigned delivery rider ID")
    rider_arrival_timestamp: Optional[datetime] = Field(None, description="When rider arrived at merchant")
    
    @field_validator('order_id', 'merchant_id', 'customer_id')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field must be non-empty")
        return v
    
    @field_validator('rider_arrival_timestamp')
    @classmethod
    def validate_rider_arrival(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate rider_arrival_timestamp is after order_creation_timestamp."""
        if v is not None and 'order_creation_timestamp' in info.data:
            if v < info.data['order_creation_timestamp']:
                raise ValueError("rider_arrival_timestamp must be after order_creation_timestamp")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ZOM-12345",
                "merchant_id": "MERCH-001",
                "customer_id": "CUST-789",
                "order_creation_timestamp": "2024-01-15T19:20:00Z",
                "item_list": [
                    {
                        "item_id": "ITEM-001",
                        "item_name": "Margherita Pizza",
                        "quantity": 1,
                        "prep_time_minutes": 12
                    }
                ],
                "status": "PREPARING",
                "assigned_rider_id": "RIDER-456",
                "rider_arrival_timestamp": None
            }
        }


class MenuItem(BaseModel):
    """
    Menu item document stored in MongoDB (reference schema).
    
    Represents a menu item with preparation time and complexity.
    Used for fraud detection to calculate minimum prep time.
    
    Indexes:
    - Compound unique index on (item_id, merchant_id)
    - Index on merchant_id for merchant queries
    """
    item_id: str = Field(..., description="Menu item identifier")
    item_name: str = Field(..., description="Menu item name")
    merchant_id: str = Field(..., description="Merchant identifier")
    category: str = Field(..., description="Item category (e.g., Pizza, Burger)")
    prep_time_minutes: int = Field(..., ge=1, le=120, description="Preparation time in minutes")
    complexity_score: int = Field(..., ge=1, le=10, description="Complexity score (1-10)")
    
    @field_validator('item_id', 'item_name', 'merchant_id', 'category')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field must be non-empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "ITEM-001",
                "item_name": "Margherita Pizza",
                "merchant_id": "MERCH-001",
                "category": "Pizza",
                "prep_time_minutes": 12,
                "complexity_score": 5
            }
        }
