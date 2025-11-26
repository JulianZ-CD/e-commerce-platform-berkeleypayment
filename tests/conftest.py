"""
Pytest configuration and shared fixtures.
Provides test database, client, and common test data.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models import Product, Order, OrderItem


# Test database URL (uses separate database for testing)
TEST_DATABASE_URL = "postgresql://ecommerce_user:ecommerce_pass@localhost:5432/ecommerce_test_db"


@pytest.fixture(scope="function")
def db_engine():
    """
    Create a test database engine.
    Creates fresh tables for each test function.
    """
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a test database session.
    Each test gets a fresh session with rollback after test.
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with overridden database dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_product(db_session):
    """Create a sample product for testing."""
    product = Product(
        name="Test Laptop",
        description="A high-performance test laptop",
        price=999.99,
        quantity=10
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_products(db_session):
    """Create multiple sample products for testing."""
    products = [
        Product(name="Laptop", description="High-end laptop", price=1299.99, quantity=5),
        Product(name="Mouse", description="Wireless mouse", price=29.99, quantity=50),
        Product(name="Keyboard", description="Mechanical keyboard", price=149.99, quantity=20),
    ]
    for product in products:
        db_session.add(product)
    db_session.commit()
    
    for product in products:
        db_session.refresh(product)
    
    return products


@pytest.fixture
def sample_order(db_session, sample_product):
    """Create a sample order for testing."""
    from app.models.order import Order, OrderStatus, PaymentStatus
    
    order = Order(
        customer_id=12345,
        total_price=1999.98,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.UNPAID
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Add order item
    order_item = OrderItem(
        order_id=order.id,
        product_id=sample_product.id,
        quantity=2,
        price_at_purchase=sample_product.price
    )
    db_session.add(order_item)
    db_session.commit()
    
    db_session.refresh(order)
    return order

