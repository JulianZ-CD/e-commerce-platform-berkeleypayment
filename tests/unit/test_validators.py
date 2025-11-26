"""
Unit tests for validation utilities.
Tests state machine transitions and business rule validations.
"""
import pytest
from fastapi import HTTPException

from app.utils.validators import validate_status_transition
from app.models.order import OrderStatus, PaymentStatus


class TestStatusTransitionValidation:
    """Test order status transition validation (state machine)."""
    
    def test_pending_to_completed_allowed(self):
        """Test that pending -> completed transition is allowed."""
        # Should not raise exception
        validate_status_transition(OrderStatus.PENDING, OrderStatus.COMPLETED)
    
    def test_pending_to_canceled_allowed(self):
        """Test that pending -> canceled transition is allowed."""
        # Should not raise exception
        validate_status_transition(OrderStatus.PENDING, OrderStatus.CANCELED)
    
    def test_pending_to_pending_allowed(self):
        """Test that pending -> pending (no-op) is allowed."""
        # Should not raise exception
        validate_status_transition(OrderStatus.PENDING, OrderStatus.PENDING)
    
    def test_completed_to_pending_not_allowed(self):
        """Test that completed -> pending transition is not allowed."""
        with pytest.raises(HTTPException) as exc_info:
            validate_status_transition(OrderStatus.COMPLETED, OrderStatus.PENDING)
        
        assert exc_info.value.status_code == 400
        assert "Cannot transition" in exc_info.value.detail
        assert "completed" in exc_info.value.detail.lower()
    
    def test_completed_to_canceled_not_allowed(self):
        """Test that completed -> canceled transition is not allowed."""
        with pytest.raises(HTTPException) as exc_info:
            validate_status_transition(OrderStatus.COMPLETED, OrderStatus.CANCELED)
        
        assert exc_info.value.status_code == 400
        assert "terminal state" in exc_info.value.detail.lower()
    
    def test_canceled_to_completed_not_allowed(self):
        """Test that canceled -> completed transition is not allowed."""
        with pytest.raises(HTTPException) as exc_info:
            validate_status_transition(OrderStatus.CANCELED, OrderStatus.COMPLETED)
        
        assert exc_info.value.status_code == 400
        assert "terminal state" in exc_info.value.detail.lower()
    
    def test_canceled_to_pending_not_allowed(self):
        """Test that canceled -> pending transition is not allowed."""
        with pytest.raises(HTTPException) as exc_info:
            validate_status_transition(OrderStatus.CANCELED, OrderStatus.PENDING)
        
        assert exc_info.value.status_code == 400
        assert "Cannot transition" in exc_info.value.detail

