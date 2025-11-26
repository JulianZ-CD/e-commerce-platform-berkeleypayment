
# Berkeley Payments Take-Home Assignment - Complete Implementation Guide

## 核心guidelines
- 具体需求在pre_requirement.md文档中，需要牢记
- 保持代码简洁，注释量适当，代码和注释仅使用英文
- 中文仅出现在对话中，以及pre_开头的markdown文档
- 设计要符合最佳实践，但是不要过度设计
- 一步步来，先完成基础功能，再添加其他
- 接下的guidelines仅做参考，不需要完全遵循，可以适当调整

---

## 🎯 核心目标

1. ✅ 完成所有必需功能（Product + Order + Webhook）
2. ✅ 代码质量高于功能数量
3. ✅ 文档清晰（README 是第一印象）
4. ✅ 展示处理 ambiguity 的能力
5. ✅ Git commits 体现工作习惯

---

## 🏗️ 技术架构

### Tech Stack 选择

```yaml
语言: Python 3.11
框架: FastAPI
数据库: PostgreSQL
ORM: SQLAlchemy 2.0
Migration: Alembic
测试: Pytest
容器化: Docker + Docker Compose
```

**为什么这个组合？**
- FastAPI: 你的 CryptoQuant 项目经验，自动文档生成
- SQLAlchemy: 成熟稳定，完整功能支持
- Docker: Interviewer 一键运行，环境可复现
- PostgreSQL: Assignment 推荐的关系型数据库

---

## 📁 项目结构

```
ecommerce-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app 入口
│   ├── config.py               # 配置管理（env vars）
│   ├── database.py             # DB 连接和 session
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── order_item.py       # 订单-产品关联表
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── product.py          # ProductCreate, ProductResponse
│   │   ├── order.py            # OrderCreate, OrderResponse
│   │   └── webhook.py          # PaymentWebhookSchema
│   │
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── products.py         # 5 endpoints
│   │   ├── orders.py           # 3 endpoints
│   │   └── webhooks.py         # 1 endpoint
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── product_service.py  # Product CRUD logic
│   │   ├── order_service.py    # Order creation, validation
│   │   └── webhook_service.py  # Payment status update
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py       # Input validation helpers
│       └── webhook_auth.py     # HMAC signature verification
│
├── alembic/                    # Database migrations
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_products.py        # Product endpoints tests
│   ├── test_orders.py          # Order endpoints tests
│   └── test_webhooks.py        # Webhook tests (重点)
│
├── .env.example                # Environment variables template
├── .gitignore
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Docker services
├── Dockerfile                  # API container
├── README.md                   # 项目文档
└── requirements.txt            # Python dependencies
```

---

## 🗄️ Database Schema 设计

### 表结构概览

```sql
products
  ├── id (UUID, PK)
  ├── name (VARCHAR, NOT NULL)
  ├── description (TEXT, NULL)
  ├── price (NUMERIC(10,2), NOT NULL, CHECK > 0)
  ├── quantity (INTEGER, NOT NULL, CHECK >= 0)
  ├── created_at (TIMESTAMP)
  └── updated_at (TIMESTAMP)

orders
  ├── id (UUID, PK)
  ├── customer_id (INTEGER, NOT NULL)
  ├── total_price (NUMERIC(10,2), NOT NULL)
  ├── status (ENUM: pending/completed/canceled)
  ├── payment_status (ENUM: unpaid/paid/failed)
  ├── created_at (TIMESTAMP)
  └── updated_at (TIMESTAMP)

order_items (关联表)
  ├── id (SERIAL, PK)
  ├── order_id (UUID, FK -> orders.id)
  ├── product_id (UUID, FK -> products.id)
  ├── quantity (INTEGER, NOT NULL, CHECK > 0)
  └── price_at_purchase (NUMERIC(10,2), NOT NULL)
```

### 关键设计决策

**1. UUID vs Auto-increment ID**
- ✅ 使用 UUID：分布式友好，不暴露业务量
- Assignment 明确要求 UUID

**2. Order Items 独立表**
- ✅ 支持多产品订单
- ✅ 记录购买时价格（历史数据）
- ✅ 便于统计分析

**3. Enum 实现方式**
```python
# 使用 Python Enum + SQLAlchemy
from enum import Enum as PyEnum

class OrderStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELED = "canceled"

# SQLAlchemy model
status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
```

**4. 时间戳策略**
```python
from datetime import datetime

created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**5. 约束（Constraints）**
```python
__table_args__ = (
    CheckConstraint('price > 0', name='check_price_positive'),
    CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
    Index('idx_products_quantity', 'quantity'),  # 库存查询优化
)
```

---

## 🔌 API Endpoints 设计

### Product APIs (5个)

```python
POST   /api/products          # 创建产品
GET    /api/products          # 列表（分页 + 过滤）
GET    /api/products/{id}     # 获取单个
PUT    /api/products/{id}     # 更新
DELETE /api/products/{id}     # 删除
```

**关键实现点：**
- Pagination: `?page=1&page_size=20`
- Filtering: `?in_stock=true` (quantity > 0)
- Response Models: 使用 Pydantic 控制返回字段

### Order APIs (3个)

```python
POST   /api/orders            # 创建订单
GET    /api/orders            # 列表（分页 + 过滤）
GET    /api/orders/{id}       # 获取单个
PUT    /api/orders/{id}/status # 更新状态
```

**关键实现点：**
- 创建订单时计算 total_price
- 验证库存是否充足
- 扣减库存（考虑并发）
- 状态转换验证（状态机）

### Webhook API (1个)

```python
POST   /api/payment-webhook   # 接收支付状态更新
```

**关键实现点：**
- HMAC 签名验证（核心考点）
- 只更新 pending 状态的订单
- 幂等性考虑（可选但加分）

---

## 🔐 Webhook 认证设计

### HMAC-SHA256 实现

```python
# 流程
1. Payment Processor: signature = HMAC-SHA256(secret, body)
2. 发送: Header["X-Signature"] = signature
3. Your API: 验证签名
4. 如果有效：处理 webhook
```

### 实现要点

```python
# utils/webhook_auth.py
import hmac
import hashlib
from fastapi import HTTPException, Request

async def verify_webhook_signature(request: Request) -> bool:
    """
    验证 webhook 签名
    
    Headers:
        X-Signature: HMAC-SHA256 signature
    
    Returns:
        True if valid
        
    Raises:
        HTTPException 401 if invalid
    """
    signature = request.headers.get("X-Signature")
    if not signature:
        raise HTTPException(401, "Missing signature")
    
    body = await request.body()
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid signature")
    
    return True
```

### README 说明要点

```markdown
1. 选择 HMAC 的理由
2. 实现细节
3. 测试方法
4. 其他方案对比（API Key, IP Whitelist）
```

---

## 🔄 业务逻辑设计

### 1. 订单创建流程

```python
# services/order_service.py

def create_order(db: Session, order_data: OrderCreate):
    """
    创建订单流程：
    1. 验证产品存在
    2. 检查库存充足
    3. 计算总价
    4. 扣减库存（事务）
    5. 创建订单和订单项
    6. 返回订单
    """
    
    # Step 1: 验证产品
    products = validate_products(db, order_data.products)
    
    # Step 2: 检查库存
    for item in order_data.products:
        product = products[item.product_id]
        if product.quantity < item.quantity:
            raise HTTPException(400, f"Insufficient stock for {product.name}")
    
    # Step 3: 计算总价
    total_price = calculate_total(products, order_data.products)
    
    # Step 4-5: 事务中完成
    with db.begin():
        # 扣减库存
        for item in order_data.products:
            product = products[item.product_id]
            product.quantity -= item.quantity
        
        # 创建订单
        order = Order(
            customer_id=order_data.customer_id,
            total_price=total_price,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID
        )
        db.add(order)
        db.flush()  # 获取 order.id
        
        # 创建订单项
        for item in order_data.products:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=products[item.product_id].price
            )
            db.add(order_item)
        
        db.commit()
    
    return order
```

### 2. 状态转换验证

```python
# 状态机定义
ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.COMPLETED, OrderStatus.CANCELED],
    OrderStatus.COMPLETED: [],
    OrderStatus.CANCELED: []
}

def validate_status_transition(current: OrderStatus, new: OrderStatus):
    """验证状态转换是否合法"""
    if new not in ALLOWED_TRANSITIONS[current]:
        raise HTTPException(
            400,
            f"Cannot transition from {current.value} to {new.value}"
        )
```

### 3. 库存管理策略

```python
# 考虑的场景
1. 创建订单时扣减库存
2. 取消订单时恢复库存
3. 并发下单的库存竞争

# 解决方案
- 使用数据库事务
- 乐观锁或悲观锁（可选）
- 在 README 说明假设
```

---

## 🧪 测试策略

### 测试优先级

**High Priority（必须）：**
1. Webhook 签名验证
2. 订单状态转换
3. 库存扣减逻辑
4. 输入验证

**Medium Priority（建议）：**
1. Product CRUD
2. 分页和过滤
3. 错误处理

**Low Priority（时间允许）：**
1. 边缘情况
2. 性能测试