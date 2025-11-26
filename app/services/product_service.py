"""
Product service - Business logic for product management.
Handles CRUD operations and business rules for products.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from uuid import UUID
from fastapi import HTTPException

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, product_data: ProductCreate) -> Product:
    """
    Create a new product in the database.
    
    Args:
        db: Database session
        product_data: Product creation data
        
    Returns:
        Product: Created product instance
        
    Business Rules:
        - Product name must be unique (optional, not enforced here)
        - Price must be positive (validated by Pydantic)
        - Quantity must be non-negative (validated by Pydantic)
    """
    # Create new product instance
    db_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        quantity=product_data.quantity
    )
    
    # Add to database
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product


def get_product(db: Session, product_id: UUID) -> Optional[Product]:
    """
    Retrieve a single product by ID.
    
    Args:
        db: Database session
        product_id: Product UUID
        
    Returns:
        Product: Product instance if found, None otherwise
    """
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    in_stock: Optional[bool] = None
) -> tuple[list[Product], int]:
    """
    Retrieve a paginated list of products with optional filtering.
    
    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        in_stock: Filter by stock availability (True = quantity > 0)
        
    Returns:
        tuple: (list of products, total count)
        
    Business Rules:
        - Default page size is 20
        - Maximum page size is 100
        - Page numbers start from 1
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
    
    # Build query
    query = db.query(Product)
    
    # Apply filters
    if in_stock is not None:
        if in_stock:
            query = query.filter(Product.quantity > 0)
        else:
            query = query.filter(Product.quantity == 0)
    
    # Get total count (before pagination)
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()
    
    return products, total


def update_product(
    db: Session,
    product_id: UUID,
    product_data: ProductUpdate
) -> Optional[Product]:
    """
    Update an existing product.
    
    Args:
        db: Database session
        product_id: Product UUID
        product_data: Product update data (partial updates supported)
        
    Returns:
        Product: Updated product instance if found, None otherwise
        
    Business Rules:
        - Only provided fields are updated
        - Validation rules still apply to updated fields
    """
    # Find product
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    # Update only provided fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    # Commit changes
    db.commit()
    db.refresh(db_product)
    
    return db_product


def delete_product(db: Session, product_id: UUID) -> bool:
    """
    Delete a product from the database.
    
    Args:
        db: Database session
        product_id: Product UUID
        
    Returns:
        bool: True if product was deleted, False if not found
        
    Business Rules:
        - Cannot delete products that are referenced in orders (enforced by FK constraint)
        - If delete fails due to FK constraint, raises HTTPException
    """
    # Find product
    db_product = get_product(db, product_id)
    if not db_product:
        return False
    
    try:
        # Delete product
        db.delete(db_product)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        # Check if it's a foreign key constraint error
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete product that is referenced in existing orders"
            )
        raise


def check_product_stock(db: Session, product_id: UUID, required_quantity: int) -> bool:
    """
    Check if a product has sufficient stock.
    
    Args:
        db: Database session
        product_id: Product UUID
        required_quantity: Required quantity
        
    Returns:
        bool: True if sufficient stock available, False otherwise
    """
    product = get_product(db, product_id)
    if not product:
        return False
    return product.quantity >= required_quantity

