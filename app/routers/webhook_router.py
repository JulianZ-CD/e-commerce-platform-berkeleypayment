"""
Webhook API endpoints.
Handles payment status updates from external payment processor.
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.schemas.webhook import PaymentWebhookPayload, WebhookResponse
from app.utils.webhook_auth import verify_webhook_signature
from app.services.webhook_service import process_payment_webhook

# Create router
router = APIRouter()


@router.post(
    "/payment-webhook",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Payment webhook endpoint",
    description="Receive payment status updates from payment processor. Requires HMAC-SHA256 signature verification."
)
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> WebhookResponse:
    """
    Payment webhook endpoint.
    
    Security:
    - Requires X-Signature header with HMAC-SHA256 signature
    - Signature is computed as: HMAC-SHA256(secret, request_body)
    - Uses constant-time comparison to prevent timing attacks
    
    Process:
    1. Verify webhook signature (authentication)
    2. Parse and validate payload
    3. Update order payment status
    4. Return acknowledgment
    
    Headers:
    - **X-Signature**: HMAC-SHA256 hex signature of request body (required)
    
    Request body:
    - **order_id**: UUID of the order (required)
    - **payment_status**: Payment status - "paid" or "failed" (required)
    
    Returns:
        WebhookResponse: Confirmation of successful processing
        
    Raises:
        HTTPException 401: Missing or invalid signature
        HTTPException 404: Order not found
        HTTPException 400: Invalid payload or order state
        
    Example:
        # Generate signature (payment processor side)
        import hmac, hashlib
        payload = '{"order_id":"123e4567-...","payment_status":"paid"}'
        secret = "webhook_secret"
        signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        
        # Send webhook
        POST /api/payment-webhook
        Headers:
            X-Signature: <signature>
            Content-Type: application/json
        Body:
            {"order_id": "123e4567-...", "payment_status": "paid"}
    """
    # Step 1: Verify signature (authentication)
    body = await verify_webhook_signature(request)
    
    # Step 2: Parse payload
    try:
        payload_dict = json.loads(body.decode('utf-8'))
        payload = PaymentWebhookPayload(**payload_dict)
    except json.JSONDecodeError:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}"
        )
    
    # Step 3: Process webhook
    updated_order = process_payment_webhook(
        db,
        payload.order_id,
        payload.payment_status
    )
    
    # Step 4: Return acknowledgment
    return WebhookResponse(
        message="Payment status updated successfully",
        order_id=updated_order.id,
        payment_status=updated_order.payment_status
    )

