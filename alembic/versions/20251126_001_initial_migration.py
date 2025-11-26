"""Initial migration: create products, orders, and order_items tables

Revision ID: 001
Revises: 
Create Date: 2025-11-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create all tables for the e-commerce platform.
    
    Tables created:
    - products: Product catalog with inventory
    - orders: Customer orders with status tracking
    - order_items: Association table linking orders to products
    """
    
    # Create enum types
    op.execute("CREATE TYPE order_status_enum AS ENUM ('pending', 'completed', 'canceled')")
    op.execute("CREATE TYPE payment_status_enum AS ENUM ('unpaid', 'paid', 'failed')")
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('price > 0', name='check_price_positive'),
        sa.CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
    )
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('idx_products_quantity', 'products', ['quantity'])
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'canceled', name='order_status_enum'), 
                  nullable=False, server_default='pending'),
        sa.Column('payment_status', sa.Enum('unpaid', 'paid', 'failed', name='payment_status_enum'), 
                  nullable=False, server_default='unpaid'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_orders_id', 'orders', ['id'])
    op.create_index('ix_orders_customer_id', 'orders', ['customer_id'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('ix_orders_payment_status', 'orders', ['payment_status'])
    
    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price_at_purchase', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.CheckConstraint('quantity > 0', name='check_order_item_quantity_positive'),
        sa.CheckConstraint('price_at_purchase > 0', name='check_price_at_purchase_positive'),
    )
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_product_id', 'order_items', ['product_id'])


def downgrade() -> None:
    """
    Drop all tables and enum types.
    """
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS payment_status_enum")
    op.execute("DROP TYPE IF EXISTS order_status_enum")

