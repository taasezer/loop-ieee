"""
Unit tests for authentication
"""

import pytest
from app.core.security import security


class TestPasswordHashing:
    """Test password hashing functionality"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = security.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = security.hash_password(password)
        
        assert security.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = security.hash_password(password)
        
        assert security.verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token functionality"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"user_id": "test-user-id", "role": "customer"}
        token = security.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"user_id": "test-user-id"}
        token = security.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token(self):
        """Test token decoding"""
        data = {"user_id": "test-user-id", "role": "customer"}
        token = security.create_access_token(data)
        
        decoded = security.decode_token(token)
        
        assert decoded["user_id"] == data["user_id"]
        assert decoded["role"] == data["role"]
        assert "exp" in decoded
        assert "iat" in decoded


class TestOTPGeneration:
    """Test OTP generation"""
    
    def test_generate_otp_default_length(self):
        """Test OTP generation with default length"""
        otp = security.generate_otp()
        
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_generate_otp_custom_length(self):
        """Test OTP generation with custom length"""
        otp = security.generate_otp(length=4)
        
        assert isinstance(otp, str)
        assert len(otp) == 4
        assert otp.isdigit()


class TestAPIKeyGeneration:
    """Test API key generation"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        api_key = security.generate_api_key()
        
        assert isinstance(api_key, str)
        assert len(api_key) == 32
    
    def test_generate_api_key_custom_length(self):
        """Test API key generation with custom length"""
        api_key = security.generate_api_key(length=64)
        
        assert isinstance(api_key, str)
        assert len(api_key) == 64


@pytest.mark.asyncio
class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    # TODO: Add more endpoint tests once implementation is complete
    # async def test_register_user(self, client, sample_user_data):
    #     """Test user registration"""
    #     response = await client.post("/api/v1/auth/register", json=sample_user_data)
    #     assert response.status_code == 201
