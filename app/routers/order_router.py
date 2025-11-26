"""
Order API endpoints.
Handles HTTP requests for order management operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from math import ceil

from app.database import get_db
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    OrderStatusUpdate
)
from app.models.order import OrderStatus, PaymentStatus
from app.services import order_service

# Create router
router = APIRouter()


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Create a new order with products. Validates stock and deducts inventory automatically."
)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
) -> OrderResponse:
    """
    Create a new order.
    
    Request body:
    - **customer_id**: Customer ID (required, must be > 0)
    - **products**: List of products with quantities (at least 1 product required)
    
    Process:
    1. Validates all products exist
    2. Checks sufficient stock
    3. Calculates total price
    4. Creates order and deducts inventory atomically
    
    Returns:
        OrderResponse: Created order with items and calculated total price
        
    Raises:
        HTTPException 404: Product not found
        HTTPException 400: Insufficient stock
    """
    db_order = order_service.create_order(db, order)
    return db_order


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="List all orders",
    description="Retrieve a paginated list of orders with optional filtering by status and payment status."
)
def list_orders(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    db: Session = Depends(get_db)
) -> OrderListResponse:
    """
    List orders with pagination and filtering.
    
    Query parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status**: Filter by order status (pending/completed/canceled)
    - **payment_status**: Filter by payment status (unpaid/paid/failed)
    
    Returns:
        OrderListResponse: Paginated list of orders with metadata
    """
    orders, total = order_service.get_orders(db, page, page_size, status, payment_status)
    
    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0
    
    return OrderListResponse(
        items=orders,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get an order by ID",
    description="Retrieve detailed information about a specific order including order items."
)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db)
) -> OrderResponse:
    """
    Get a single order by ID.
    
    Path parameters:
    - **order_id**: Order UUID
    
    Returns:
        OrderResponse: Order details with order items
        
    Raises:
        HTTPException 404: Order not found
    """
    db_order = order_service.get_order(db, order_id)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return db_order


@router.put(
    "/orders/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
    description="Update the status of an order. Only specific transitions are allowed (pending->completed/canceled)."
)
def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db)
) -> OrderResponse:
    """
    Update order status.
    
    Path parameters:
    - **order_id**: Order UUID
    
    Request body:
    - **status**: New order status (completed or canceled)
    
    Allowed transitions:
    - pending -> completed
    - pending -> canceled
    - completed/canceled -> (no transitions allowed)
    
    Business logic:
    - If canceling a pending order, inventory is restored
    
    Returns:
        OrderResponse: Updated order
        
    Raises:
        HTTPException 404: Order not found
        HTTPException 400: Invalid status transition
    """
    db_order = order_service.update_order_status(db, order_id, status_update)
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return db_order

