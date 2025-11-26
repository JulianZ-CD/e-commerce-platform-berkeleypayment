"""
Integration tests for payment webhook API endpoint.
Tests complete webhook request/response cycle with HMAC authentication.
"""
import pytest
import json
import hmac
import hashlib
from fastapi import status

from app.models.order import OrderStatus, PaymentStatus


class TestPaymentWebhookAPI:
    """Test payment webhook endpoint with authentication."""
    
    def generate_signature(self, payload: str) -> str:
        """Generate valid HMAC-SHA256 signature for webhook."""
        secret = "dev_webhook_secret_key"  # From app settings
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def test_webhook_with_valid_signature(self, client, sample_order):
        """Test webhook processes successfully with valid signature."""
        # Prepare webhook payload
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "paid"
        }
        payload_str = json.dumps(payload)
        
        # Generate valid signature
        signature = self.generate_signature(payload_str)
        
        # Send webhook request
        response = client.post(
            "/api/payment-webhook",
            data=payload_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Payment status updated successfully"
        assert data["order_id"] == str(sample_order.id)
        assert data["payment_status"] == "paid"
    
    def test_webhook_with_invalid_signature(self, client, sample_order):
        """Test webhook rejects request with invalid signature."""
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "paid"
        }
        payload_str = json.dumps(payload)
        
        # Send with invalid signature
        response = client.post(
            "/api/payment-webhook",
            data=payload_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": "invalid_signature_12345"
            }
        )
        
        # Should be rejected
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid signature" in response.json()["detail"]
    
    def test_webhook_without_signature_header(self, client, sample_order):
        """Test webhook rejects request without signature header."""
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "paid"
        }
        
        # Send without X-Signature header
        response = client.post(
            "/api/payment-webhook",
            json=payload  # This sets Content-Type automatically
        )
        
        # Should be rejected
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing X-Signature" in response.json()["detail"]
    
    def test_webhook_updates_payment_status_to_paid(self, client, db_session, sample_order):
        """Test webhook correctly updates order payment status to paid."""
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "paid"
        }
        payload_str = json.dumps(payload)
        signature = self.generate_signature(payload_str)
        
        # Send webhook
        response = client.post(
            "/api/payment-webhook",
            data=payload_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify order payment status updated in database
        db_session.refresh(sample_order)
        assert sample_order.payment_status == PaymentStatus.PAID
    
    def test_webhook_updates_payment_status_to_failed(self, client, db_session, sample_order):
        """Test webhook correctly updates order payment status to failed."""
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "failed"
        }
        payload_str = json.dumps(payload)
        signature = self.generate_signature(payload_str)
        
        # Send webhook
        response = client.post(
            "/api/payment-webhook",
            data=payload_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify order payment status updated
        db_session.refresh(sample_order)
        assert sample_order.payment_status == PaymentStatus.FAILED
    
    def test_webhook_rejects_non_pending_order(self, client, db_session, sample_order):
        """Test webhook rejects payment update for non-pending orders."""
        # Complete the order first
        sample_order.status = OrderStatus.COMPLETED
        db_session.commit()
        
        # Try to update payment status
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "paid"
        }
        payload_str = json.dumps(payload)
        signature = self.generate_signature(payload_str)
        
        response = client.post(
            "/api/payment-webhook",
            data=payload_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            }
        )
        
        # Should be rejected
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pending" in response.json()["detail"].lower()
    
    def test_webhook_with_non_existent_order(self, client):
        """Test webhook returns 404 for non-existent order."""
        from uuid import uuid4
        
        payload = {
            "order_id": str(uuid4()),
            "payment_status": "paid"
        }
        payload_str = json.dumps(payload)
        signature = self.generate_signature(payload_str)
        
        response = client.post(
            "/api/payment-webhook",
            data=payload_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
    
    def test_webhook_with_invalid_payment_status(self, client, sample_order):
        """Test webhook rejects invalid payment status values."""
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "invalid_status"
        }
        payload_str = json.dumps(payload)
        signature = self.generate_signature(payload_str)
        
        response = client.post(
            "/api/payment-webhook",
            data=payload_str,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            }
        )
        
        # Should fail validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_webhook_idempotency(self, client, db_session, sample_order):
        """Test that sending the same webhook multiple times is safe (idempotent)."""
        payload = {
            "order_id": str(sample_order.id),
            "payment_status": "paid"
        }
        payload_str = json.dumps(payload)
        signature = self.generate_signature(payload_str)
        
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature
        }
        
        # Send webhook first time
        response1 = client.post("/api/payment-webhook", data=payload_str, headers=headers)
        assert response1.status_code == status.HTTP_200_OK
        
        # Send same webhook second time (idempotent)
        response2 = client.post("/api/payment-webhook", data=payload_str, headers=headers)
        assert response2.status_code == status.HTTP_200_OK
        
        # Verify order still has correct status
        db_session.refresh(sample_order)
        assert sample_order.payment_status == PaymentStatus.PAID

