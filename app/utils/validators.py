"""
Validation utilities for business logic.
Contains helper functions for validating state transitions and business rules.
"""
from fastapi import HTTPException, status
from app.models.order import OrderStatus, PaymentStatus


# Define allowed status transitions as a state machine
ALLOWED_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.COMPLETED, OrderStatus.CANCELED],
    OrderStatus.COMPLETED: [],  # Terminal state - no transitions allowed
    OrderStatus.CANCELED: []    # Terminal state - no transitions allowed
}


def validate_status_transition(current: OrderStatus, new: OrderStatus) -> None:
    """
    Validate that a status transition is allowed.
    
    State machine rules:
    - pending -> completed (allowed)
    - pending -> canceled (allowed)
    - completed -> * (not allowed - terminal state)
    - canceled -> * (not allowed - terminal state)
    
    Args:
        current: Current order status
        new: Desired new status
        
    Raises:
        HTTPException 400: If transition is not allowed
        
    Example:
        >>> validate_status_transition(OrderStatus.PENDING, OrderStatus.COMPLETED)
        # OK
        >>> validate_status_transition(OrderStatus.COMPLETED, OrderStatus.CANCELED)
        # Raises HTTPException
    """
    # Check if new status is the same as current (no-op, but allowed)
    if current == new:
        return
    
    # Check if transition is allowed
    allowed_transitions = ALLOWED_STATUS_TRANSITIONS.get(current, [])
    if new not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition order status from '{current.value}' to '{new.value}'. "
                   f"Allowed transitions from '{current.value}': {[s.value for s in allowed_transitions] or 'none (terminal state)'}"
        )


def validate_payment_status_update(
    current_order_status: OrderStatus,
    current_payment_status: PaymentStatus,
    new_payment_status: PaymentStatus
) -> None:
    """
    Validate that a payment status update is allowed.
    
    Rules:
    - Only orders with status 'pending' can have payment status updated
    - Cannot change payment status if already paid
    
    Args:
        current_order_status: Current order status
        current_payment_status: Current payment status
        new_payment_status: Desired new payment status
        
    Raises:
        HTTPException 400: If update is not allowed
    """
    # Only allow payment updates for pending orders
    if current_order_status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update payment status for order with status '{current_order_status.value}'. "
                   f"Only orders with status 'pending' can have payment status updated."
        )
    
    # Don't allow changing payment status if already paid
    if current_payment_status == PaymentStatus.PAID and new_payment_status != PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change payment status for an order that is already paid."
        )

