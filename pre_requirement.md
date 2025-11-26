# Take-Home Assignment: E-commerce and Order Management API with Payment Webhook Handling

## Overview
You are tasked with designing and implementing an API system for an e-commerce platform. This system will manage products, orders, and payments, including a webhook to handle payment status updates from a hypothetical payment processor. The goal is to assess your ability to work with APIs, handle business logic, and manage real-world scenarios like external event handling via webhooks.

You should create a private GitHub repository and share it with the GitHub username (RahmatYousufi) upon completion. There is a 72-hour timeline from the time you receive this assignment. We estimate it will take 4-8 hours to complete.

## Requirements

### 1. Product Management APIs
You will create the following endpoints for managing products:

● **POST /api/products**
Create a new product with the following fields:
- id: unique identifier (UUID)
- name: string, required
- description: string, optional
- price: decimal, required
- quantity: integer, required (This is the stock level.)
- created_at: timestamp (auto-generated)
- updated_at: timestamp (auto-generated)

● **GET /api/products**
Fetch a list of all products with pagination and filtering by availability (in stock only).

● **GET /api/products/{id}**
Fetch details of a specific product by ID.

● **PUT /api/products/{id}**
Update an existing product

● **DELETE /api/products/{id}**
Delete a product by ID.

### 2. Order Management APIs
You will create the following endpoints for managing orders:

● **POST /api/orders**
Place a new order. Each order will contain:
- id: unique identifier (UUID)
- customer_id: integer (assume customers are pre-existing)
- products: list of product IDs and quantities
- total_price: calculated based on product prices and quantities
- status: enum (pending, canceled, completed) - default is pending
- payment_status: enum (unpaid, paid, failed) - default is unpaid
- created_at: timestamp (auto-generated)
- updated_at: timestamp (auto-generated)

● **GET /api/orders**
Fetch a list of all orders with pagination and filtering by status and payment_status.

● **GET /api/orders/{id}**
Fetch details of a specific order by ID.

● **PUT /api/orders/{id}/status**
Update the status of an order. Only allow certain status transitions:
- pending -> completed
- pending -> canceled

### 3. Payment Handling via Webhook
You will implement a webhook to simulate receiving payment status updates from a payment processor. The webhook will handle the following events:

**POST /api/payment-webhook**
The payment processor will send the following payload to update an order's payment status:
```json
{
  "order_id": "UUID of the order",
  "payment_status": "paid or failed"
}
```

● When the webhook is triggered:
- Validate the order_id and ensure the order exists.
- Update the payment_status of the order based on the payment_status value received.
- Only allow the webhook to update an order with the status pending to either paid or failed.

### Ambiguity
Some requirements, design details and edge cases are deliberately left ambiguous to assess how you handle slightly unclear instructions and your ability to ask questions if needed. Ex, how would you authenticate the webhook is coming from the payment processor? If you do not have time to implement everything, some quick notes on some proposed improvements will suffice.

### Validation
● Ensure all inputs are validated. For example:
- Price must be a positive number.
- Quantity must be greater than zero.
- Payment status can only be one of the predefined values (paid, failed).

### 4. Database
● Use a relational database (e.g., PostgreSQL, MySQL).
● Create the necessary database schema and migration files.
● Bonus: Use an ORM such as GORM for database interaction.

### 5. Additional Requirements
● Implement proper error handling to return meaningful error messages and HTTP status codes.
● Provide clear and concise README documentation explaining how to set up and run the project.

## Deliverables
1. **Code**: Your Go(or language of your choice) implementation for the API endpoints and database migration files.
2. **Documentation**: A README file with setup instructions.
3. **Git Workflow**: Ensure your commits reflect logical progress, and commit as you implement.