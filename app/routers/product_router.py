"""
Product API endpoints.
Handles HTTP requests for product management operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from math import ceil

from app.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)
from app.services import product_service

# Create router with prefix and tags
router = APIRouter()


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product with name, description, price, and quantity."
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
) -> ProductResponse:
    """
    Create a new product.
    
    Request body:
    - **name**: Product name (required, 1-255 characters)
    - **description**: Product description (optional)
    - **price**: Product price (required, must be > 0)
    - **quantity**: Stock quantity (required, must be >= 0)
    
    Returns:
        ProductResponse: Created product with ID and timestamps
    """
    db_product = product_service.create_product(db, product)
    return db_product


@router.get(
    "/products",
    response_model=ProductListResponse,
    summary="List all products",
    description="Retrieve a paginated list of products with optional filtering by stock availability."
)
def list_products(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability (true = in stock)"),
    db: Session = Depends(get_db)
) -> ProductListResponse:
    """
    List products with pagination and filtering.
    
    Query parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **in_stock**: Filter by stock (true = quantity > 0, false = quantity == 0)
    
    Returns:
        ProductListResponse: Paginated list of products with metadata
    """
    products, total = product_service.get_products(db, page, page_size, in_stock)
    
    # Calculate total pages
    total_pages = ceil(total / page_size) if total > 0 else 0
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID",
    description="Retrieve detailed information about a specific product."
)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
) -> ProductResponse:
    """
    Get a single product by ID.
    
    Path parameters:
    - **product_id**: Product UUID
    
    Returns:
        ProductResponse: Product details
        
    Raises:
        HTTPException 404: Product not found
    """
    db_product = product_service.get_product(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return db_product


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
    description="Update an existing product. Only provided fields will be updated."
)
def update_product(
    product_id: UUID,
    product: ProductUpdate,
    db: Session = Depends(get_db)
) -> ProductResponse:
    """
    Update an existing product.
    
    Path parameters:
    - **product_id**: Product UUID
    
    Request body (all fields optional):
    - **name**: New product name
    - **description**: New description
    - **price**: New price (must be > 0)
    - **quantity**: New quantity (must be >= 0)
    
    Returns:
        ProductResponse: Updated product
        
    Raises:
        HTTPException 404: Product not found
    """
    db_product = product_service.update_product(db, product_id, product)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return db_product


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    description="Delete a product from the system. Cannot delete products referenced in orders."
)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a product.
    
    Path parameters:
    - **product_id**: Product UUID
    
    Returns:
        HTTP 204: Product successfully deleted
        
    Raises:
        HTTPException 404: Product not found
        HTTPException 400: Product is referenced in existing orders
    """
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    # Return 204 No Content (no response body)
    return None

