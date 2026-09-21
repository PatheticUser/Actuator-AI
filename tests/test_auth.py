import pytest
from pydantic import ValidationError
from backend.api.routes.auth import AuthRequest

def test_auth_request_valid():
    req = AuthRequest(email="test@example.com", password="StrongPassword123")
    assert req.email == "test@example.com"
    assert req.password == "StrongPassword123"

def test_auth_request_invalid_email():
    with pytest.raises(ValidationError):
        AuthRequest(email="not-an-email", password="ValidPassword123")

def test_auth_request_short_password():
    with pytest.raises(ValidationError):
        AuthRequest(email="valid@example.com", password="short")
