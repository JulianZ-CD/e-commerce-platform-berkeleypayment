"""
OrderItem model - association table between orders and products.
Stores the relationship between orders and products, including quantity and historical price.
"""
from sqlalchemy import Column, Integer, DECIMAL, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class OrderItem(Base):
    """
    OrderItem table links orders to products with quantity and price information.
    
    This is a many-to-many association table that also stores:
    - Quantity of each product in the order
    - Price at the time of purchase (for historical accuracy)
    
    Attributes:
        id: Auto-incrementing primary key
        order_id: Foreign key to orders table
        product_id: Foreign key to products table
        quantity: Number of units ordered (must be > 0)
        price_at_purchase: Product price when order was placed
        
    Relationships:
        order: The order this item belongs to
        product: The product being ordered
    """
    __tablename__ = "order_items"
    
    # Primary key (auto-increment)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey('orders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey('products.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    
    # Order details
    quantity = Column(Integer, nullable=False)
    
    # Store price at time of purchase for historical accuracy
    # This prevents retroactive price changes from affecting past orders
    price_at_purchase = Column(DECIMAL(10, 2), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    
    # Constraints
    __table_args__ = (
        # Quantity must be positive
        CheckConstraint('quantity > 0', name='check_order_item_quantity_positive'),
        # Price must be positive
        CheckConstraint('price_at_purchase > 0', name='check_price_at_purchase_positive'),
    )
    
    def __repr__(self):
        return (f"<OrderItem(id={self.id}, order_id={self.order_id}, "
                f"product_id={self.product_id}, quantity={self.quantity})>")

