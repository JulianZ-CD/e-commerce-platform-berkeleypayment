"""
Integration tests for Order API endpoints.
Tests complete order lifecycle from creation to status updates.
"""
import pytest
from fastapi import status


class TestOrderAPI:
    """Test order API endpoints with end-to-end workflows."""
    
    def test_create_order_success(self, client, sample_product):
        """Test successful order creation."""
        order_data = {
            "customer_id": 12345,
            "products": [
                {
                    "product_id": str(sample_product.id),
                    "quantity": 2
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["customer_id"] == 12345
        assert data["status"] == "pending"
        assert data["payment_status"] == "unpaid"
        assert float(data["total_price"]) == float(sample_product.price * 2)
        assert len(data["order_items"]) == 1
        assert data["order_items"][0]["quantity"] == 2
    
    def test_create_order_deducts_inventory(self, client, db_session, sample_product):
        """Test that creating an order deducts inventory."""
        initial_quantity = sample_product.quantity
        
        order_data = {
            "customer_id": 99999,
            "products": [
                {
                    "product_id": str(sample_product.id),
                    "quantity": 3
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify inventory deducted
        db_session.refresh(sample_product)
        assert sample_product.quantity == initial_quantity - 3
    
    def test_create_order_with_multiple_products(self, client, sample_products):
        """Test order creation with multiple products."""
        order_data = {
            "customer_id": 55555,
            "products": [
                {"product_id": str(sample_products[0].id), "quantity": 1},
                {"product_id": str(sample_products[1].id), "quantity": 2},
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert len(data["order_items"]) == 2
        
        # Verify total price calculation
        expected_total = (
            float(sample_products[0].price * 1) +
            float(sample_products[1].price * 2)
        )
        assert float(data["total_price"]) == expected_total
    
    def test_create_order_insufficient_stock(self, client, sample_product):
        """Test order creation fails with insufficient stock."""
        order_data = {
            "customer_id": 12345,
            "products": [
                {
                    "product_id": str(sample_product.id),
                    "quantity": sample_product.quantity + 100  # More than available
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient stock" in response.json()["detail"]
    
    def test_create_order_product_not_found(self, client):
        """Test order creation fails with non-existent product."""
        from uuid import uuid4
        
        order_data = {
            "customer_id": 12345,
            "products": [
                {
                    "product_id": str(uuid4()),
                    "quantity": 1
                }
            ]
        }
        
        response = client.post("/api/orders", json=order_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_order_by_id(self, client, sample_order):
        """Test retrieving order by ID."""
        response = client.get(f"/api/orders/{sample_order.id}")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == str(sample_order.id)
        assert data["customer_id"] == sample_order.customer_id
        assert data["status"] == sample_order.status.value
    
    def test_get_order_not_found(self, client):
        """Test retrieving non-existent order returns 404."""
        from uuid import uuid4
        
        response = client.get(f"/api/orders/{uuid4()}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_orders_with_pagination(self, client, sample_order):
        """Test listing orders with pagination."""
        response = client.get("/api/orders?page=1&page_size=20")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_list_orders_filter_by_status(self, client, sample_order):
        """Test listing orders filtered by status."""
        response = client.get("/api/orders?status=pending")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # All returned orders should have pending status
        for order in data["items"]:
            assert order["status"] == "pending"
    
    def test_update_order_status_to_completed(self, client, sample_order):
        """Test updating order status from pending to completed."""
        response = client.put(
            f"/api/orders/{sample_order.id}/status",
            json={"status": "completed"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "completed"
    
    def test_update_order_status_to_canceled_restores_inventory(
        self, client, db_session, sample_order, sample_product
    ):
        """Test canceling order restores inventory."""
        # Get current inventory (after order creation)
        current_quantity = sample_product.quantity
        order_quantity = sample_order.order_items[0].quantity
        
        # Cancel order
        response = client.put(
            f"/api/orders/{sample_order.id}/status",
            json={"status": "canceled"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "canceled"
        
        # Verify inventory restored
        db_session.refresh(sample_product)
        assert sample_product.quantity == current_quantity + order_quantity
    
    def test_update_order_status_invalid_transition(self, client, sample_order):
        """Test invalid status transition is rejected."""
        # First complete the order
        client.put(
            f"/api/orders/{sample_order.id}/status",
            json={"status": "completed"}
        )
        
        # Try to cancel completed order (not allowed)
        response = client.put(
            f"/api/orders/{sample_order.id}/status",
            json={"status": "canceled"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot transition" in response.json()["detail"]
    
    def test_end_to_end_order_flow(self, client, db_session, sample_product):
        """Test complete order lifecycle from creation to completion."""
        initial_quantity = sample_product.quantity
        
        # Step 1: Create order
        order_data = {
            "customer_id": 77777,
            "products": [{"product_id": str(sample_product.id), "quantity": 1}]
        }
        create_response = client.post("/api/orders", json=order_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        
        order_id = create_response.json()["id"]
        
        # Step 2: Verify inventory deducted
        db_session.refresh(sample_product)
        assert sample_product.quantity == initial_quantity - 1
        
        # Step 3: Get order details
        get_response = client.get(f"/api/orders/{order_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["status"] == "pending"
        
        # Step 4: Complete the order
        update_response = client.put(
            f"/api/orders/{order_id}/status",
            json={"status": "completed"}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["status"] == "completed"
        
        # Step 5: Verify inventory stays deducted (not restored for completed)
        db_session.refresh(sample_product)
        assert sample_product.quantity == initial_quantity - 1

