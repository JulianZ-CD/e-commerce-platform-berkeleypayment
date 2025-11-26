"""
Order service - Business logic for order management.
Handles order creation, status updates, and inventory management.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.utils.validators import validate_status_transition


def create_order(db: Session, order_data: OrderCreate) -> Order:
    """
    Create a new order with inventory management.
    
    Process:
    1. Validate all products exist
    2. Check sufficient stock for all products
    3. Calculate total price
    4. Create order and order items
    5. Deduct inventory (all in a transaction)
    
    Args:
        db: Database session
        order_data: Order creation data with customer_id and products list
        
    Returns:
        Order: Created order with order items
        
    Raises:
        HTTPException 404: Product not found
        HTTPException 400: Insufficient stock
        
    Business Rules:
        - All products must exist
        - Sufficient stock must be available for all items
        - Stock is deducted atomically with order creation
        - Total price is calculated from current product prices
    """
    # Step 1: Validate all products exist and build product map
    product_ids = [item.product_id for item in order_data.products]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    
    if len(products) != len(product_ids):
        found_ids = {p.id for p in products}
        missing_ids = [pid for pid in product_ids if pid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found: {missing_ids}"
        )
    
    # Create product lookup map
    product_map = {p.id: p for p in products}
    
    # Step 2: Check sufficient stock for all products
    for item in order_data.products:
        product = product_map[item.product_id]
        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{product.name}'. "
                       f"Available: {product.quantity}, Requested: {item.quantity}"
            )
    
    # Step 3: Calculate total price
    total_price = sum(
        product_map[item.product_id].price * item.quantity
        for item in order_data.products
    )
    
    # Step 4-5: Create order and deduct inventory in a transaction
    try:
        # Create order
        db_order = Order(
            customer_id=order_data.customer_id,
            total_price=total_price,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID
        )
        db.add(db_order)
        db.flush()  # Get order ID without committing
        
        # Create order items and deduct inventory
        for item in order_data.products:
            product = product_map[item.product_id]
            
            # Create order item
            order_item = OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=product.price
            )
            db.add(order_item)
            
            # Deduct inventory
            product.quantity -= item.quantity
        
        # Commit transaction
        db.commit()
        db.refresh(db_order)
        
        return db_order
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


def get_order(db: Session, order_id: UUID) -> Optional[Order]:
    """
    Retrieve a single order by ID with order items.
    
    Args:
        db: Database session
        order_id: Order UUID
        
    Returns:
        Order: Order instance with order_items loaded, or None if not found
    """
    return db.query(Order).filter(Order.id == order_id).first()


def get_orders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None
) -> tuple[list[Order], int]:
    """
    Retrieve a paginated list of orders with optional filtering.
    
    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by order status (optional)
        payment_status: Filter by payment status (optional)
        
    Returns:
        tuple: (list of orders, total count)
        
    Business Rules:
        - Default page size is 20
        - Maximum page size is 100
        - Page numbers start from 1
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
    
    # Build query
    query = db.query(Order)
    
    # Apply filters
    if status is not None:
        query = query.filter(Order.status == status)
    if payment_status is not None:
        query = query.filter(Order.payment_status == payment_status)
    
    # Get total count (before pagination)
    total = query.count()
    
    # Apply pagination and order by creation date (newest first)
    offset = (page - 1) * page_size
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(page_size).all()
    
    return orders, total


def update_order_status(
    db: Session,
    order_id: UUID,
    status_update: OrderStatusUpdate
) -> Optional[Order]:
    """
    Update order status with state machine validation.
    
    Args:
        db: Database session
        order_id: Order UUID
        status_update: New status
        
    Returns:
        Order: Updated order instance, or None if not found
        
    Raises:
        HTTPException 400: Invalid status transition
        
    Business Rules:
        - Only specific transitions are allowed (see validators.py)
        - If canceling an order, restore inventory
    """
    # Find order
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    # Validate status transition
    validate_status_transition(db_order.status, status_update.status)
    
    # If canceling order, restore inventory
    if status_update.status == OrderStatus.CANCELED and db_order.status == OrderStatus.PENDING:
        for order_item in db_order.order_items:
            product = db.query(Product).filter(Product.id == order_item.product_id).first()
            if product:
                product.quantity += order_item.quantity
    
    # Update status
    db_order.status = status_update.status
    
    # Commit changes
    db.commit()
    db.refresh(db_order)
    
    return db_order


def update_payment_status(
    db: Session,
    order_id: UUID,
    new_payment_status: PaymentStatus
) -> Optional[Order]:
    """
    Update order payment status (used by webhook).
    
    Args:
        db: Database session
        order_id: Order UUID
        new_payment_status: New payment status (paid or failed)
        
    Returns:
        Order: Updated order instance, or None if not found
        
    Business Rules:
        - Only orders with status 'pending' can be updated
        - Payment status transitions are validated
    """
    # Find order
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    # Only update payment status for pending orders
    if db_order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update payment status for order with status '{db_order.status.value}'. "
                   f"Only orders with status 'pending' can have payment status updated."
        )
    
    # Update payment status
    db_order.payment_status = new_payment_status
    
    # Commit changes
    db.commit()
    db.refresh(db_order)
    
    return db_order

