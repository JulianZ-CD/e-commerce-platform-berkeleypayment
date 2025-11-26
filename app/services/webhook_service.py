"""
Webhook service - Business logic for payment webhook handling.
Processes payment status updates from external payment processor.
"""
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status

from app.models.order import Order, OrderStatus, PaymentStatus
from app.services.order_service import update_payment_status


def process_payment_webhook(
    db: Session,
    order_id: UUID,
    payment_status: PaymentStatus
) -> Order:
    """
    Process payment webhook and update order payment status.
    
    Business Rules:
    1. Order must exist
    2. Only orders with status 'pending' can have payment status updated
    3. Valid payment statuses from webhook: 'paid' or 'failed'
    4. Idempotent: Multiple webhooks with same status are safe
    
    Args:
        db: Database session
        order_id: Order UUID from webhook
        payment_status: New payment status (paid or failed)
        
    Returns:
        Order: Updated order instance
        
    Raises:
        HTTPException 404: Order not found
        HTTPException 400: Invalid status or order state
        
    Notes:
        - This function is idempotent: calling it multiple times with
          the same status has no adverse effects
        - In a production system, you might want to store webhook
          delivery IDs to detect and handle duplicates
    """
    # Validate payment status from webhook
    if payment_status not in [PaymentStatus.PAID, PaymentStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment status from webhook: {payment_status.value}. "
                   f"Expected 'paid' or 'failed'."
        )
    
    # Update payment status (will validate order exists and is pending)
    db_order = update_payment_status(db, order_id, payment_status)
    
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    return db_order


def validate_webhook_payload(order_id: UUID, payment_status: PaymentStatus) -> None:
    """
    Validate webhook payload data.
    
    Performs additional validation beyond Pydantic schema validation.
    
    Args:
        order_id: Order UUID
        payment_status: Payment status
        
    Raises:
        HTTPException 400: Invalid payload data
    """
    # Validate order_id is not nil UUID
    if str(order_id) == '00000000-0000-0000-0000-000000000000':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_id: cannot be nil UUID"
        )
    
    # Additional validations can be added here
    # For example:
    # - Check if payment_status is one of the expected values
    # - Validate timestamp if included in payload
    # - Check webhook delivery ID for idempotency

