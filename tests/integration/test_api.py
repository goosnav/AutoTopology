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


def test_root_returns_landing_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "AutoTopology" in response.text
    assert "text/html" in response.headers["content-type"]


def test_generate_endpoint_returns_candidate():
    response = client.get("/api/generate", params={"family": "table_family", "seed": 42})
    assert response.status_code == 200
    data = response.json()
    assert "genome_id" in data
    assert data["family"] == "table_family"
    assert data["seed"] == 42
    assert data["mesh_report"]["is_acceptable"] is True
    assert data["mesh_report"]["vertex_count"] > 0
