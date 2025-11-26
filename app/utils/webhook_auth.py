"""
Webhook authentication utilities.
Implements HMAC-SHA256 signature verification for secure webhook handling.
"""
import hmac
import hashlib
from fastapi import Request, HTTPException, status

from app.config import settings


async def verify_webhook_signature(request: Request) -> bytes:
    """
    Verify webhook signature using HMAC-SHA256.
    
    Security Process:
    1. Payment processor generates: signature = HMAC-SHA256(secret, request_body)
    2. Processor sends signature in X-Signature header
    3. We receive the webhook and:
       - Extract the signature from header
       - Compute expected signature using our shared secret
       - Compare signatures using constant-time comparison
    4. If signatures match, webhook is authentic
    
    Args:
        request: FastAPI request object
        
    Returns:
        bytes: Raw request body (for parsing after verification)
        
    Raises:
        HTTPException 401: Missing or invalid signature
        
    Security Features:
    - Uses HMAC-SHA256 (industry standard)
    - Constant-time comparison (prevents timing attacks)
    - Shared secret from environment variable
    
    Example Usage:
        @app.post("/webhook")
        async def webhook(request: Request):
            body = await verify_webhook_signature(request)
            # Process webhook...
    """
    # Extract signature from header
    signature_header = request.headers.get("X-Signature")
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Signature header"
        )
    
    # Get raw request body
    body = await request.body()
    if not body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty request body"
        )
    
    # Compute expected signature
    secret = settings.webhook_secret.encode('utf-8')
    expected_signature = hmac.new(
        secret,
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Verify signature using constant-time comparison
    # This prevents timing attacks where attackers measure
    # response times to guess the signature
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    return body


def generate_webhook_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for a webhook payload.
    
    This is a helper function for testing purposes.
    In production, the payment processor would generate this signature.
    
    Args:
        payload: JSON string of the webhook payload
        secret: Shared secret key
        
    Returns:
        str: Hex-encoded HMAC-SHA256 signature
        
    Example:
        >>> payload = '{"order_id": "123", "payment_status": "paid"}'
        >>> secret = "my_secret_key"
        >>> signature = generate_webhook_signature(payload, secret)
        >>> # Use signature in X-Signature header
    """
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

