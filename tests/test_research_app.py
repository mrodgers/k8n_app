import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.app import app as fastapi_app

@pytest.fixture
def client():
    return TestClient(fastapi_app)

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_enhanced_root_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data
    assert "components" in data
    assert "agents" in data["components"]
    assert "services" in data["components"]

def test_api_tasks_endpoint(client):
    response = client.get('/api/tasks')
    assert response.status_code == 200
    assert "tasks" in response.json()

@patch('src.app.planner.create_research_task')
def test_api_create_task(mock_create_task, client):
    mock_create_task.return_value = {
        "id": "test_task_1",
        "title": "Test Task",
        "description": "Test description",
        "tags": ["test", "research"],
        "status": "pending"
    }
    
    response = client.post('/api/tasks', json={
        "title": "Test Task",
        "description": "Test description",
        "tags": ["test", "research"]
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "task" in data
    assert data["task"]["id"] == "test_task_1"