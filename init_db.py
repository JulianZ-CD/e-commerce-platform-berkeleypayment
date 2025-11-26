"""
Database initialization script.
Creates all tables using SQLAlchemy models.

Usage:
    python init_db.py
"""
from app.database import engine, Base
from app.models import Product, Order, OrderItem

def init_database():
    """
    Create all database tables.
    This is an alternative to using Alembic migrations for quick setup.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    print("\nTables created:")
    print("  - products")
    print("  - orders")
    print("  - order_items")

if __name__ == "__main__":
    init_database()

