from fastapi.testclient import TestClient
from app.main import app
from app.database import check_db_connection


def test_fastapi_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "CodeFoundry API"
        assert data["version"] == "1.0.0"
        assert data["database"] in ["connected", "disconnected"]


def test_fastapi_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


def test_postgresql_connection():
    connected = check_db_connection()
    assert connected is True, "PostgreSQL connection failed"
