"""
Integration tests for Product API endpoints.
Tests CRUD operations and pagination/filtering.
"""
import pytest
from fastapi import status


class TestProductAPI:
    """Test product API endpoints."""
    
    def test_create_product_success(self, client):
        """Test successful product creation."""
        product_data = {
            "name": "Test Laptop",
            "description": "High-performance laptop for testing",
            "price": 1299.99,
            "quantity": 50
        }
        
        response = client.post("/api/products", json=product_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == "Test Laptop"
        assert float(data["price"]) == 1299.99
        assert data["quantity"] == 50
        assert "id" in data
        assert "created_at" in data
    
    def test_create_product_invalid_price(self, client):
        """Test product creation fails with invalid price."""
        product_data = {
            "name": "Invalid Product",
            "price": -10.00,  # Negative price
            "quantity": 10
        }
        
        response = client.post("/api/products", json=product_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_product_invalid_quantity(self, client):
        """Test product creation fails with negative quantity."""
        product_data = {
            "name": "Invalid Product",
            "price": 100.00,
            "quantity": -5  # Negative quantity
        }
        
        response = client.post("/api/products", json=product_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_product_by_id(self, client, sample_product):
        """Test retrieving product by ID."""
        response = client.get(f"/api/products/{sample_product.id}")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == str(sample_product.id)
        assert data["name"] == sample_product.name
        assert float(data["price"]) == float(sample_product.price)
    
    def test_get_product_not_found(self, client):
        """Test retrieving non-existent product returns 404."""
        from uuid import uuid4
        
        response = client.get(f"/api/products/{uuid4()}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_products_with_pagination(self, client, sample_products):
        """Test listing products with pagination."""
        response = client.get("/api/products?page=1&page_size=10")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10
    
    def test_list_products_filter_in_stock(self, client, db_session):
        """Test filtering products by stock availability."""
        # Create products with and without stock
        from app.models.product import Product
        
        in_stock = Product(name="In Stock", price=100, quantity=10)
        out_of_stock = Product(name="Out of Stock", price=100, quantity=0)
        
        db_session.add(in_stock)
        db_session.add(out_of_stock)
        db_session.commit()
        
        # Filter for in-stock products
        response = client.get("/api/products?in_stock=true")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # All returned products should have quantity > 0
        for product in data["items"]:
            assert product["quantity"] > 0
    
    def test_update_product_success(self, client, sample_product):
        """Test successful product update."""
        update_data = {
            "price": 899.99,
            "quantity": 25
        }
        
        response = client.put(
            f"/api/products/{sample_product.id}",
            json=update_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert float(data["price"]) == 899.99
        assert data["quantity"] == 25
        # Name should remain unchanged (partial update)
        assert data["name"] == sample_product.name
    
    def test_update_product_not_found(self, client):
        """Test updating non-existent product returns 404."""
        from uuid import uuid4
        
        response = client.put(
            f"/api/products/{uuid4()}",
            json={"price": 100.00}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_product_success(self, client, sample_product):
        """Test successful product deletion."""
        response = client.delete(f"/api/products/{sample_product.id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify product is deleted
        get_response = client.get(f"/api/products/{sample_product.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_product_not_found(self, client):
        """Test deleting non-existent product returns 404."""
        from uuid import uuid4
        
        response = client.delete(f"/api/products/{uuid4()}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_full_crud_cycle(self, client):
        """Test complete CRUD cycle for a product."""
        # Create
        create_data = {
            "name": "CRUD Test Product",
            "description": "Testing full CRUD cycle",
            "price": 599.99,
            "quantity": 100
        }
        create_response = client.post("/api/products", json=create_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        product_id = create_response.json()["id"]
        
        # Read
        get_response = client.get(f"/api/products/{product_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["name"] == "CRUD Test Product"
        
        # Update
        update_response = client.put(
            f"/api/products/{product_id}",
            json={"price": 499.99}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert float(update_response.json()["price"]) == 499.99
        
        # Delete
        delete_response = client.delete(f"/api/products/{product_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deleted
        final_get_response = client.get(f"/api/products/{product_id}")
        assert final_get_response.status_code == status.HTTP_404_NOT_FOUND

