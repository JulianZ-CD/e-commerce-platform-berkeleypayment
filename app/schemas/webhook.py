"""
Pydantic schemas for Webhook API requests and responses.
Handles validation for payment webhook payloads.
"""
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.order import PaymentStatus


class PaymentWebhookPayload(BaseModel):
    """
    Schema for payment webhook payload from payment processor.
    
    This represents the data sent by an external payment processor
    to notify us of payment status changes.
    
    Example:
        {
            "order_id": "123e4567-e89b-12d3-a456-426614174000",
            "payment_status": "paid"
        }
    """
    order_id: UUID = Field(..., description="Order UUID")
    payment_status: PaymentStatus = Field(..., description="Payment status (paid or failed)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
                "payment_status": "paid"
            }
        }


class WebhookResponse(BaseModel):
    """
    Schema for webhook response.
    
    Simple acknowledgment response to confirm webhook was processed.
    """
    message: str = Field(..., description="Status message")
    order_id: UUID = Field(..., description="Order UUID that was updated")
    payment_status: PaymentStatus = Field(..., description="New payment status")

