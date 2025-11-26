"""
Order model for managing customer orders.
Tracks order status, payment status, and associated order items.
"""
from sqlalchemy import Column, Integer, DECIMAL, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from app.database import Base


class OrderStatus(str, PyEnum):
    """
    Order status enumeration.
    Defines the lifecycle states of an order.
    """
    PENDING = "pending"       # Order created, awaiting completion
    COMPLETED = "completed"   # Order fulfilled
    CANCELED = "canceled"     # Order canceled


class PaymentStatus(str, PyEnum):
    """
    Payment status enumeration.
    Tracks the payment state of an order.
    """
    UNPAID = "unpaid"   # Payment not yet received
    PAID = "paid"       # Payment successfully processed
    FAILED = "failed"   # Payment attempt failed


class Order(Base):
    """
    Order table stores customer order information.
    
    Attributes:
        id: Unique identifier (UUID)
        customer_id: Reference to customer (assumed to exist externally)
        total_price: Calculated total price of all items
        status: Current order status (pending/completed/canceled)
        payment_status: Current payment status (unpaid/paid/failed)
        created_at: Timestamp when order was created
        updated_at: Timestamp when order was last updated
        
    Relationships:
        order_items: List of items included in this order
    """
    __tablename__ = "orders"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Customer reference (assuming external customer management)
    customer_id = Column(Integer, nullable=False, index=True)
    
    # Order total
    total_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Status fields using Python Enums
    status = Column(
        SQLEnum(OrderStatus, name='order_status_enum'),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )
    payment_status = Column(
        SQLEnum(PaymentStatus, name='payment_status_enum'),
        default=PaymentStatus.UNPAID,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return (f"<Order(id={self.id}, customer_id={self.customer_id}, "
                f"status={self.status.value}, payment_status={self.payment_status.value})>")

