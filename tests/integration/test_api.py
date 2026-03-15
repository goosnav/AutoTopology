"""Integration tests for FastAPI application."""

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_expected_json():
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["app_name"] == "AutoTopology"
