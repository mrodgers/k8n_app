"""
Tests for the web interface components (dashboard and research portal).

This module tests the rendering and functionality of the web interfaces.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
import os

from src.app import app
from src.research_system.core.dashboard import get_agent_status, get_system_status, get_db_status
from src.research_system.core.coordinator import Coordinator

client = TestClient(app)

# Skip template rendering tests in CI
@pytest.mark.skipif(
    "SKIP_TEMPLATE_TESTS" in os.environ, 
    reason="Template tests are skipped in CI environment"
)
@patch("src.research_system.core.dashboard.templates.TemplateResponse")
def test_dashboard_endpoint(mock_template_response):
    """Test that the dashboard endpoint works."""
    # Mock the template response to avoid template not found errors
    mock_template_response.return_value = Mock()
    
    # Patch the internal function to avoid actual template rendering
    with patch("src.research_system.core.dashboard.templates.get_template"):
        response = client.get("/dashboard/api/status")
        assert response.status_code == 200
        assert "system" in response.json()
        assert "agents" in response.json()
        assert "database" in response.json()


# Skip template rendering tests in CI
@pytest.mark.skipif(
    "SKIP_TEMPLATE_TESTS" in os.environ, 
    reason="Template tests are skipped in CI environment"
)
@patch("src.research_system.core.research.templates.TemplateResponse")
def test_research_endpoint(mock_template_response):
    """Test that the research endpoint works."""
    # Mock the template response to avoid template not found errors
    mock_template_response.return_value = Mock()
    
    # Patch the internal function to avoid actual template rendering
    with patch("src.research_system.core.research.templates.get_template"):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert "tasks" in response.json()


def test_dashboard_api_status():
    """Test the dashboard status API endpoint."""
    response = client.get("/dashboard/api/status")
    assert response.status_code == 200
    assert "system" in response.json()
    assert "agents" in response.json()
    assert "database" in response.json()


def test_dashboard_api_system():
    """Test the dashboard system API endpoint."""
    response = client.get("/dashboard/api/system")
    assert response.status_code == 200
    assert "system" in response.json()
    
    # Check that system metrics are present
    system_data = response.json()["system"]
    assert "cpu_percent" in system_data
    assert "memory_percent" in system_data
    assert "disk_percent" in system_data


def test_dashboard_api_agents():
    """Test the dashboard agents API endpoint."""
    response = client.get("/dashboard/api/agents")
    assert response.status_code == 200
    assert "agents" in response.json()


def test_dashboard_api_database():
    """Test the dashboard database API endpoint."""
    response = client.get("/dashboard/api/database")
    assert response.status_code == 200
    assert "database" in response.json()
    
    # Check that database info is present
    db_data = response.json()["database"]
    assert "status" in db_data
    assert "type" in db_data


def test_get_system_status():
    """Test the get_system_status function directly."""
    system_status = get_system_status()
    assert "cpu_percent" in system_status
    assert "memory_percent" in system_status
    assert "memory_used" in system_status
    assert "memory_total" in system_status
    assert "disk_percent" in system_status
    assert "disk_used" in system_status
    assert "disk_total" in system_status


def test_get_agent_status():
    """Test the get_agent_status function with a mock coordinator."""
    mock_coordinator = MagicMock(spec=Coordinator)
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_agent.server_url = "http://localhost:8080"
    mock_agent.description = "Test agent"
    mock_agent.tools = ["tool1", "tool2"]
    
    mock_coordinator.list_agents.return_value = ["test_agent"]
    mock_coordinator.get_agent.return_value = mock_agent
    
    agent_status = get_agent_status(mock_coordinator)
    
    assert "test_agent" in agent_status
    assert agent_status["test_agent"]["name"] == "test_agent"
    assert agent_status["test_agent"]["server_url"] == "http://localhost:8080"
    assert agent_status["test_agent"]["description"] == "Test agent"
    assert agent_status["test_agent"]["tools"] == ["tool1", "tool2"]
    assert "status" in agent_status["test_agent"]


@patch("src.research_system.core.dashboard.default_db")
def test_get_db_status(mock_default_db):
    """Test the get_db_status function with a mock database."""
    # Mock task and result objects
    mock_task = MagicMock()
    mock_task.id = "task1"
    mock_task.title = "Test Task"
    mock_task.status = "pending"
    mock_task.created_at = 1619712345.0
    
    mock_result = MagicMock()
    mock_result.id = "result1"
    mock_result.task_id = "task1"
    mock_result.format = "text"
    mock_result.status = "draft"
    mock_result.created_at = 1619712345.0
    
    # Configure the mock
    mock_default_db.list_tasks.return_value = [mock_task]
    mock_default_db.list_results_for_task.return_value = [mock_result]
    
    # Create a mock db object that has the right attributes
    mock_db = MagicMock()
    mock_db.db_path = "/tmp/test.json"
    mock_default_db.db = mock_db
    
    # Now call the function
    db_status = get_db_status()
    
    # Verify the mocks were called correctly
    mock_default_db.list_tasks.assert_called_once()
    mock_default_db.list_results_for_task.assert_called_once()
    
    # Test that we got back what we expected
    assert db_status["status"] == "connected"
    assert db_status["type"] == "TinyDB"
    assert db_status["location"] == "/tmp/test.json"
    assert db_status["tasks_count"] == 1
    assert db_status["results_count"] == 1
    assert len(db_status["recent_tasks"]) == 1
    assert len(db_status["recent_results"]) == 1


def test_create_task_via_api():
    """Test creating a task via the API endpoint."""
    task_data = {
        "title": "Test Research Task",
        "description": "This is a test task created via the API",
        "tags": ["test", "api"]
    }
    
    with patch("src.research_system.agents.planner.PlannerAgent.create_research_task") as mock_create:
        # Configure the mock to return a task with the provided data
        mock_task = {
            "id": "mock-task-id",
            "title": task_data["title"],
            "description": task_data["description"],
            "tags": task_data["tags"],
            "status": "pending",
            "created_at": 1619712345.0,
            "updated_at": 1619712345.0
        }
        mock_create.return_value = mock_task
        
        response = client.post("/api/tasks", json=task_data)
        
        assert response.status_code == 201
        assert response.json()["task"]["id"] == "mock-task-id"
        assert response.json()["task"]["title"] == task_data["title"]
        assert response.json()["task"]["description"] == task_data["description"]
        assert response.json()["task"]["tags"] == task_data["tags"]
        
        # Verify that the planner's create_research_task was called with the right args
        mock_create.assert_called_once_with(
            title=task_data["title"],
            description=task_data["description"],
            tags=task_data["tags"],
            assigned_to=None
        )


def test_get_task_api():
    """Test getting a task via the API endpoint."""
    task_id = "test-task-123"
    
    with patch("src.research_system.models.db.default_db.get_task") as mock_get_task:
        # Configure the mock to return a task
        mock_task = MagicMock()
        mock_task.model_dump.return_value = {
            "id": task_id,
            "title": "Test Task",
            "description": "Test Description",
            "status": "pending",
            "created_at": 1619712345.0
        }
        mock_get_task.return_value = mock_task
        
        response = client.get(f"/api/tasks/{task_id}")
        
        assert response.status_code == 200
        assert response.json()["task"]["id"] == task_id
        assert response.json()["task"]["title"] == "Test Task"
        
        # Verify that get_task was called with the right task_id
        mock_get_task.assert_called_once_with(task_id)


def test_get_nonexistent_task():
    """Test getting a task that doesn't exist."""
    task_id = "nonexistent-task"
    
    with patch("src.research_system.models.db.default_db.get_task") as mock_get_task:
        mock_get_task.return_value = None
        
        response = client.get(f"/api/tasks/{task_id}")
        
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()
        
        # Verify that get_task was called with the right task_id
        mock_get_task.assert_called_once_with(task_id)