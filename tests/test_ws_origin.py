import pytest

from backend.core.config import settings


@pytest.fixture
def configured_origins(monkeypatch):
    """Pin CORS_ORIGINS so the test does not depend on the local .env."""
    monkeypatch.setattr(
        settings,
        "CORS_ORIGINS",
        "https://actuator-ai.example.com,http://localhost:8000",
    )


def test_origin_absent_is_allowed(configured_origins):
    # Native/server-side clients send no Origin; browsers always do.
    assert settings.is_allowed_origin(None)
    assert settings.is_allowed_origin("")


def test_configured_origin_is_allowed(configured_origins):
    assert settings.is_allowed_origin("https://actuator-ai.example.com")


def test_loopback_origins_are_allowed(configured_origins):
    # The Vite dev server proxies to the backend, so the browser still sends an
    # Origin header for the loopback dev server.
    assert settings.is_allowed_origin("http://localhost:5173")
    assert settings.is_allowed_origin("http://127.0.0.1:5173")
    assert settings.is_allowed_origin("http://[::1]:5173")


def test_unknown_origin_is_rejected(configured_origins):
    assert not settings.is_allowed_origin("https://evil.example.com")


def test_loopback_lookalike_is_rejected(configured_origins):
    # A host that merely contains "localhost" must not be trusted.
    assert not settings.is_allowed_origin("http://localhost.evil.example.com")
    assert not settings.is_allowed_origin("https://notlocalhost")
