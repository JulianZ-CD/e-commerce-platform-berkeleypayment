"""
Unit tests for webhook authentication.
Tests HMAC-SHA256 signature generation and verification.
"""
import pytest
import hmac
import hashlib
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException

from app.utils.webhook_auth import verify_webhook_signature, generate_webhook_signature


class TestGenerateWebhookSignature:
    """Test webhook signature generation."""
    
    def test_generate_signature_basic(self):
        """Test basic signature generation."""
        payload = '{"order_id": "123", "payment_status": "paid"}'
        secret = "test_secret"
        
        signature = generate_webhook_signature(payload, secret)
        
        # Verify signature is hex string
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex is 64 chars
        assert all(c in '0123456789abcdef' for c in signature)
    
    def test_generate_signature_consistent(self):
        """Test that same input produces same signature."""
        payload = '{"test": "data"}'
        secret = "my_secret"
        
        sig1 = generate_webhook_signature(payload, secret)
        sig2 = generate_webhook_signature(payload, secret)
        
        assert sig1 == sig2
    
    def test_generate_signature_different_payload(self):
        """Test that different payloads produce different signatures."""
        secret = "secret"
        payload1 = '{"order_id": "1"}'
        payload2 = '{"order_id": "2"}'
        
        sig1 = generate_webhook_signature(payload1, secret)
        sig2 = generate_webhook_signature(payload2, secret)
        
        assert sig1 != sig2
    
    def test_generate_signature_different_secret(self):
        """Test that different secrets produce different signatures."""
        payload = '{"data": "test"}'
        secret1 = "secret1"
        secret2 = "secret2"
        
        sig1 = generate_webhook_signature(payload, secret1)
        sig2 = generate_webhook_signature(payload, secret2)
        
        assert sig1 != sig2
    
    def test_generate_signature_empty_payload(self):
        """Test signature generation with empty payload."""
        payload = ""
        secret = "secret"
        
        signature = generate_webhook_signature(payload, secret)
        
        # Should still generate valid signature
        assert isinstance(signature, str)
        assert len(signature) == 64


class TestVerifyWebhookSignature:
    """Test webhook signature verification."""
    
    @pytest.mark.asyncio
    async def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        # Create mock request
        payload = b'{"order_id": "123", "payment_status": "paid"}'
        secret = "dev_webhook_secret_key"
        
        # Generate valid signature
        expected_sig = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Mock request
        mock_request = Mock()
        mock_request.headers = {"X-Signature": expected_sig}
        mock_request.body = AsyncMock(return_value=payload)
        
        # Should not raise exception
        result = await verify_webhook_signature(mock_request)
        assert result == payload
    
    @pytest.mark.asyncio
    async def test_verify_invalid_signature(self):
        """Test rejection of invalid signature."""
        payload = b'{"order_id": "123"}'
        
        # Mock request with wrong signature
        mock_request = Mock()
        mock_request.headers = {"X-Signature": "invalid_signature_12345"}
        mock_request.body = AsyncMock(return_value=payload)
        
        # Should raise 401
        with pytest.raises(HTTPException) as exc_info:
            await verify_webhook_signature(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid signature" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_missing_signature_header(self):
        """Test rejection when signature header is missing."""
        payload = b'{"order_id": "123"}'
        
        # Mock request without X-Signature header
        mock_request = Mock()
        mock_request.headers = {}  # No X-Signature
        mock_request.body = AsyncMock(return_value=payload)
        
        # Should raise 401
        with pytest.raises(HTTPException) as exc_info:
            await verify_webhook_signature(mock_request)
        
        assert exc_info.value.status_code == 401
        assert "Missing X-Signature" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_empty_body(self):
        """Test rejection of empty request body."""
        # Mock request with empty body
        mock_request = Mock()
        mock_request.headers = {"X-Signature": "some_signature"}
        mock_request.body = AsyncMock(return_value=b'')
        
        # Should raise 400
        with pytest.raises(HTTPException) as exc_info:
            await verify_webhook_signature(mock_request)
        
        assert exc_info.value.status_code == 400
        assert "Empty request body" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_signature_case_sensitive(self):
        """Test that signature verification is case-sensitive."""
        payload = b'{"test": "data"}'
        secret = "dev_webhook_secret_key"
        
        # Generate valid signature
        valid_sig = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Mock request with uppercase signature
        mock_request = Mock()
        mock_request.headers = {"X-Signature": valid_sig.upper()}
        mock_request.body = AsyncMock(return_value=payload)
        
        # Should reject (hex digest is lowercase)
        with pytest.raises(HTTPException) as exc_info:
            await verify_webhook_signature(mock_request)
        
        assert exc_info.value.status_code == 401

