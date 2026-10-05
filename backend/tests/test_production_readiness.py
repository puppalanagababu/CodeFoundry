import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.execution.runner import DockerCodeRunner
from app.celery_app import celery_app
from app.database import engine


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_production_config_validation_catches_insecure_defaults():
    # Production with dev default secret key should fail validation
    prod_insecure = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="codefoundry-dev-fallback-key-only-for-local-testing",
        DB_PASSWORD="",
    )
    errors = prod_insecure.validate_production_configuration()
    assert len(errors) > 0
    assert any("SECRET_KEY" in e for e in errors)
    assert any("DB_PASSWORD" in e for e in errors)


def test_production_config_validation_catches_short_secret_key():
    prod_short_key = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="short-secret-key",
        DB_PASSWORD="a-secure-database-password",
        CORS_ALLOWED_ORIGINS="https://app.codefoundry.dev",
        ALLOWED_HOSTS="app.codefoundry.dev",
    )
    errors = prod_short_key.validate_production_configuration()
    assert any("at least 32 characters" in e for e in errors)


def test_production_config_validation_catches_wildcard_cors():
    prod_wildcard_cors = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="a-sufficiently-long-and-secure-production-secret-key-12345",
        DB_PASSWORD="a-secure-database-password",
        CORS_ALLOWED_ORIGINS="*",
        ALLOWED_HOSTS="app.codefoundry.dev",
    )
    errors = prod_wildcard_cors.validate_production_configuration()
    assert any("CORS_ALLOWED_ORIGINS" in e for e in errors)


def test_production_config_validation_passes_valid_prod_settings():
    prod_valid = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="a-sufficiently-long-and-secure-production-secret-key-12345",
        DB_PASSWORD="a-secure-database-password",
        CORS_ALLOWED_ORIGINS="https://app.codefoundry.dev,https://admin.codefoundry.dev",
        ALLOWED_HOSTS="app.codefoundry.dev,admin.codefoundry.dev",
    )
    errors = prod_valid.validate_production_configuration()
    assert len(errors) == 0


def test_development_config_allows_local_defaults():
    dev_settings = Settings(
        ENVIRONMENT="development",
        DEBUG=True,
    )
    errors = dev_settings.validate_production_configuration()
    assert len(errors) == 0


def test_cors_origins_list_strips_wildcard_safely():
    settings_with_wildcard = Settings(CORS_ALLOWED_ORIGINS="*")
    assert "*" not in settings_with_wildcard.cors_origins_list
    assert len(settings_with_wildcard.cors_origins_list) > 0


def test_security_headers_present_in_responses(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_global_exception_handler_masks_internal_tracebacks(client, monkeypatch):
    from app.routers import auth

    def mock_broken_login(*args, **kwargs):
        raise RuntimeError("Sensitive internal database connection string: postgresql://secret_user:pass123@internal.db")

    # Force an unhandled exception inside a route handler
    monkeypatch.setattr(auth, "get_client_ip", mock_broken_login)

    response = client.post("/api/auth/login/", json={"username": "test", "password": "password"})
    assert response.status_code == 500
    data = response.json()
    assert data == {"detail": "An internal server error occurred."}
    assert "secret_user" not in response.text
    assert "postgresql://" not in response.text


def test_jwt_token_security_and_expiration():
    access_token = create_access_token(user_id=42, role="STUDENT")
    decoded = decode_token(access_token)
    assert decoded["user_id"] == 42
    assert decoded["role"] == "STUDENT"
    assert decoded["token_type"] == "access"
    assert "exp" in decoded
    assert "iat" in decoded
    assert "jti" in decoded

    refresh_token = create_refresh_token(user_id=42, role="STUDENT")
    decoded_ref = decode_token(refresh_token)
    assert decoded_ref["user_id"] == 42
    assert decoded_ref["token_type"] == "refresh"
    assert decoded_ref["exp"] > decoded["exp"]


def test_password_hashing_security():
    plain = "SuperSecurePassword123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert "pbkdf2" in hashed or "bcrypt" in hashed
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_database_connection_pool_settings():
    pool = engine.pool
    assert pool.size() == 10
    assert pool._max_overflow == 20
    assert pool._recycle == 3600
    assert pool._timeout == 30


def test_docker_runner_security_hardening():
    runner = DockerCodeRunner()
    assert runner.mem_limit == "128m"
    assert runner.memswap_limit == "128m"
    assert runner.nano_cpus == 1_000_000_000
    assert runner.pids_limit == 64


def test_celery_serialization_security():
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.task_time_limit == 60
    assert celery_app.conf.task_soft_time_limit == 30
