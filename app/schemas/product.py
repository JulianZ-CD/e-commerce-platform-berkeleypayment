"""
Pydantic schemas for Product API requests and responses.
Handles validation and serialization for product-related endpoints.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class ProductBase(BaseModel):
    """
    Base schema with common product fields.
    Shared between create and update operations.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Product price (must be > 0)")
    quantity: int = Field(..., ge=0, description="Stock quantity (must be >= 0)")


class ProductCreate(ProductBase):
    """
    Schema for creating a new product.
    Inherits all fields from ProductBase.
    
    Example:
        {
            "name": "Laptop",
            "description": "High-performance laptop",
            "price": 999.99,
            "quantity": 50
        }
    """
    pass


class ProductUpdate(BaseModel):
    """
    Schema for updating an existing product.
    All fields are optional to support partial updates.
    
    Example:
        {
            "price": 899.99,
            "quantity": 45
        }
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    quantity: Optional[int] = Field(None, ge=0)


class ProductResponse(ProductBase):
    """
    Schema for product responses.
    Includes all product fields plus metadata.
    
    Used for:
    - GET /api/products/{id}
    - POST /api/products
    - PUT /api/products/{id}
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Configure Pydantic to work with SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """
    Schema for paginated product list responses.
    
    Used for GET /api/products with pagination.
    
    Example:
        {
            "items": [...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        }
    """
    items: list[ProductResponse]
    total: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

