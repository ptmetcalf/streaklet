"""Tests for main app web routes."""
from fastapi.testclient import TestClient


def test_home_route(client: TestClient):
    """Test the home page route renders successfully."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_settings_route(client: TestClient):
    """Test the settings page route renders successfully."""
    response = client.get("/settings")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_fitbit_route(client: TestClient):
    """Test the Fitbit metrics page route renders successfully."""
    response = client.get("/fitbit")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_profiles_route(client: TestClient):
    """Test the profiles page route renders successfully."""
    response = client.get("/profiles")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_health_endpoint(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
