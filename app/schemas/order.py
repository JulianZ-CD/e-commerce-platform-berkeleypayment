"""
Pydantic schemas for Order API requests and responses.
Handles validation and serialization for order-related endpoints.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.models.order import OrderStatus, PaymentStatus


class OrderItemCreate(BaseModel):
    """
    Schema for creating an order item within an order.
    
    Example:
        {
            "product_id": "123e4567-e89b-12d3-a456-426614174000",
            "quantity": 2
        }
    """
    product_id: UUID = Field(..., description="Product UUID")
    quantity: int = Field(..., gt=0, description="Quantity to order (must be > 0)")


class OrderItemResponse(BaseModel):
    """
    Schema for order item in responses.
    Includes product details and price information.
    """
    id: int
    product_id: UUID
    quantity: int
    price_at_purchase: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """
    Schema for creating a new order.
    
    Example:
        {
            "customer_id": 12345,
            "products": [
                {"product_id": "uuid-1", "quantity": 2},
                {"product_id": "uuid-2", "quantity": 1}
            ]
        }
    """
    customer_id: int = Field(..., gt=0, description="Customer ID (must be > 0)")
    products: list[OrderItemCreate] = Field(..., min_length=1, description="List of products to order (at least 1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": 12345,
                "products": [
                    {"product_id": "123e4567-e89b-12d3-a456-426614174000", "quantity": 2}
                ]
            }
        }


class OrderResponse(BaseModel):
    """
    Schema for order responses.
    Includes all order fields and associated order items.
    """
    id: UUID
    customer_id: int
    total_price: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    order_items: list[OrderItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """
    Schema for paginated order list responses.
    
    Example:
        {
            "items": [...],
            "total": 50,
            "page": 1,
            "page_size": 20,
            "total_pages": 3
        }
    """
    items: list[OrderResponse]
    total: int = Field(..., description="Total number of orders")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class OrderStatusUpdate(BaseModel):
    """
    Schema for updating order status.
    
    Only allows specific status transitions:
    - pending -> completed
    - pending -> canceled
    
    Example:
        {
            "status": "completed"
        }
    """
    status: OrderStatus = Field(..., description="New order status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed"
            }
        }

