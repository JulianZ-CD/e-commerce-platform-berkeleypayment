"""
Unit tests for order service.
Tests order creation, inventory management, and status updates.
"""
import pytest
from decimal import Decimal
from fastapi import HTTPException

from app.services.order_service import (
    create_order,
    get_order,
    update_order_status,
    update_payment_status
)
from app.schemas.order import OrderCreate, OrderItemCreate, OrderStatusUpdate
from app.models.order import OrderStatus, PaymentStatus
from app.models.product import Product


class TestCreateOrder:
    """Test order creation with inventory management."""
    
    def test_create_order_success(self, db_session, sample_product):
        """Test successful order creation."""
        order_data = OrderCreate(
            customer_id=12345,
            products=[
                OrderItemCreate(
                    product_id=sample_product.id,
                    quantity=2
                )
            ]
        )
        
        # Record initial quantity
        initial_quantity = sample_product.quantity
        
        # Create order
        order = create_order(db_session, order_data)
        
        # Verify order created
        assert order.id is not None
        assert order.customer_id == 12345
        assert order.status == OrderStatus.PENDING
        assert order.payment_status == PaymentStatus.UNPAID
        
        # Verify total price calculated correctly
        expected_total = sample_product.price * 2
        assert order.total_price == expected_total
        
        # Verify order items created
        assert len(order.order_items) == 1
        assert order.order_items[0].product_id == sample_product.id
        assert order.order_items[0].quantity == 2
        assert order.order_items[0].price_at_purchase == sample_product.price
        
        # Verify inventory deducted
        db_session.refresh(sample_product)
        assert sample_product.quantity == initial_quantity - 2
    
    def test_create_order_multiple_products(self, db_session, sample_products):
        """Test order creation with multiple products."""
        order_data = OrderCreate(
            customer_id=99999,
            products=[
                OrderItemCreate(product_id=sample_products[0].id, quantity=1),
                OrderItemCreate(product_id=sample_products[1].id, quantity=2),
            ]
        )
        
        # Record initial quantities
        initial_qty_0 = sample_products[0].quantity
        initial_qty_1 = sample_products[1].quantity
        
        # Create order
        order = create_order(db_session, order_data)
        
        # Verify order items
        assert len(order.order_items) == 2
        
        # Verify total price
        expected_total = (
            sample_products[0].price * 1 +
            sample_products[1].price * 2
        )
        assert order.total_price == expected_total
        
        # Verify inventory deducted for all products
        db_session.refresh(sample_products[0])
        db_session.refresh(sample_products[1])
        assert sample_products[0].quantity == initial_qty_0 - 1
        assert sample_products[1].quantity == initial_qty_1 - 2
    
    def test_create_order_insufficient_stock(self, db_session, sample_product):
        """Test order creation fails with insufficient stock."""
        # Try to order more than available
        order_data = OrderCreate(
            customer_id=12345,
            products=[
                OrderItemCreate(
                    product_id=sample_product.id,
                    quantity=sample_product.quantity + 1  # More than available
                )
            ]
        )
        
        # Should raise 400 error
        with pytest.raises(HTTPException) as exc_info:
            create_order(db_session, order_data)
        
        assert exc_info.value.status_code == 400
        assert "Insufficient stock" in exc_info.value.detail
        
        # Verify inventory not changed
        db_session.refresh(sample_product)
        assert sample_product.quantity == 10  # Original quantity
    
    def test_create_order_product_not_found(self, db_session):
        """Test order creation fails with non-existent product."""
        from uuid import uuid4
        
        order_data = OrderCreate(
            customer_id=12345,
            products=[
                OrderItemCreate(
                    product_id=uuid4(),  # Non-existent product
                    quantity=1
                )
            ]
        )
        
        # Should raise 404 error
        with pytest.raises(HTTPException) as exc_info:
            create_order(db_session, order_data)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
    
    def test_create_order_atomicity(self, db_session, sample_products):
        """Test that order creation is atomic (all or nothing)."""
        # Try to create order where second product has insufficient stock
        order_data = OrderCreate(
            customer_id=12345,
            products=[
                OrderItemCreate(product_id=sample_products[0].id, quantity=1),
                OrderItemCreate(product_id=sample_products[1].id, quantity=9999),  # Too much
            ]
        )
        
        # Record initial quantities
        initial_qty_0 = sample_products[0].quantity
        initial_qty_1 = sample_products[1].quantity
        
        # Should fail
        with pytest.raises(HTTPException):
            create_order(db_session, order_data)
        
        # Verify NO inventory was deducted (atomicity)
        db_session.refresh(sample_products[0])
        db_session.refresh(sample_products[1])
        assert sample_products[0].quantity == initial_qty_0
        assert sample_products[1].quantity == initial_qty_1


class TestUpdateOrderStatus:
    """Test order status updates."""
    
    def test_update_status_pending_to_completed(self, db_session, sample_order):
        """Test updating order from pending to completed."""
        status_update = OrderStatusUpdate(status=OrderStatus.COMPLETED)
        
        updated_order = update_order_status(db_session, sample_order.id, status_update)
        
        assert updated_order is not None
        assert updated_order.status == OrderStatus.COMPLETED
    
    def test_update_status_pending_to_canceled(self, db_session, sample_order, sample_product):
        """Test updating order from pending to canceled restores inventory."""
        # Record initial product quantity (after order creation)
        initial_quantity = sample_product.quantity
        
        # Cancel order
        status_update = OrderStatusUpdate(status=OrderStatus.CANCELED)
        updated_order = update_order_status(db_session, sample_order.id, status_update)
        
        assert updated_order.status == OrderStatus.CANCELED
        
        # Verify inventory restored
        db_session.refresh(sample_product)
        # Original order took 2 units, canceling should restore them
        assert sample_product.quantity == initial_quantity + 2
    
    def test_update_status_invalid_transition(self, db_session, sample_order):
        """Test that invalid status transitions are rejected."""
        # First complete the order
        update_order_status(
            db_session,
            sample_order.id,
            OrderStatusUpdate(status=OrderStatus.COMPLETED)
        )
        
        # Try to cancel completed order (not allowed)
        with pytest.raises(HTTPException) as exc_info:
            update_order_status(
                db_session,
                sample_order.id,
                OrderStatusUpdate(status=OrderStatus.CANCELED)
            )
        
        assert exc_info.value.status_code == 400
        assert "Cannot transition" in exc_info.value.detail
    
    def test_update_status_order_not_found(self, db_session):
        """Test updating non-existent order returns None."""
        from uuid import uuid4
        
        status_update = OrderStatusUpdate(status=OrderStatus.COMPLETED)
        result = update_order_status(db_session, uuid4(), status_update)
        
        assert result is None


class TestUpdatePaymentStatus:
    """Test payment status updates (webhook functionality)."""
    
    def test_update_payment_status_to_paid(self, db_session, sample_order):
        """Test updating payment status to paid."""
        updated_order = update_payment_status(
            db_session,
            sample_order.id,
            PaymentStatus.PAID
        )
        
        assert updated_order is not None
        assert updated_order.payment_status == PaymentStatus.PAID
    
    def test_update_payment_status_to_failed(self, db_session, sample_order):
        """Test updating payment status to failed."""
        updated_order = update_payment_status(
            db_session,
            sample_order.id,
            PaymentStatus.FAILED
        )
        
        assert updated_order is not None
        assert updated_order.payment_status == PaymentStatus.FAILED
    
    def test_update_payment_status_non_pending_order(self, db_session, sample_order):
        """Test that only pending orders can have payment status updated."""
        # Complete the order first
        update_order_status(
            db_session,
            sample_order.id,
            OrderStatusUpdate(status=OrderStatus.COMPLETED)
        )
        
        # Try to update payment status of completed order
        with pytest.raises(HTTPException) as exc_info:
            update_payment_status(
                db_session,
                sample_order.id,
                PaymentStatus.PAID
            )
        
        assert exc_info.value.status_code == 400
        assert "pending" in exc_info.value.detail.lower()
    
    def test_update_payment_status_order_not_found(self, db_session):
        """Test updating payment status of non-existent order."""
        from uuid import uuid4
        
        result = update_payment_status(
            db_session,
            uuid4(),
            PaymentStatus.PAID
        )
        
        assert result is None


class TestGetOrder:
    """Test order retrieval."""
    
    def test_get_existing_order(self, db_session, sample_order):
        """Test retrieving an existing order."""
        order = get_order(db_session, sample_order.id)
        
        assert order is not None
        assert order.id == sample_order.id
        assert order.customer_id == sample_order.customer_id
    
    def test_get_non_existent_order(self, db_session):
        """Test retrieving non-existent order returns None."""
        from uuid import uuid4
        
        order = get_order(db_session, uuid4())
        
        assert order is None

