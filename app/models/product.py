"""
Product model for inventory management.
Represents items available for purchase in the e-commerce platform.
"""
from sqlalchemy import Column, String, Text, DECIMAL, Integer, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Product(Base):
    """
    Product table stores information about items available for sale.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Product name (required)
        description: Detailed product description (optional)
        price: Product price in decimal format (must be > 0)
        quantity: Available stock quantity (must be >= 0)
        created_at: Timestamp when product was created
        updated_at: Timestamp when product was last updated
    """
    __tablename__ = "products"
    
    # Primary key - using UUID for distributed systems
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Product information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Price stored as DECIMAL for precise financial calculations
    # DECIMAL(10,2) allows values up to 99,999,999.99
    price = Column(DECIMAL(10, 2), nullable=False)
    
    # Stock quantity
    quantity = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    
    # Constraints
    __table_args__ = (
        # Price must be positive
        CheckConstraint('price > 0', name='check_price_positive'),
        # Quantity cannot be negative
        CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
        # Index for efficient stock queries
        Index('idx_products_quantity', 'quantity'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, quantity={self.quantity})>"

