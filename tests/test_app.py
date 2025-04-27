import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the main app for testing
from src.app import app

@pytest.fixture
def client():
    """Create a TestClient instance for the FastAPI app."""
    return TestClient(app)

def test_health_endpoint(client):
    """Test the health endpoint used by Kubernetes probes."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint(client):
    """Test the root endpoint with basic system info."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data
    assert "components" in data
    assert "agents" in data["components"]
    assert "services" in data["components"]

def test_healthz_liveness_probe(client):
    """Test the Kubernetes liveness probe endpoint."""
    response = client.get('/healthz')
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "research-system"
