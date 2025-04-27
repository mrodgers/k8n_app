"""
Shared fixtures for testing the Research System.

This module contains pytest fixtures that can be used across all test modules.
"""

import os
import sys
import pytest
import json
import tempfile
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Any

# Add the project root to Python path to resolve module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.research_system.core.server import FastMCPServer, Context
from src.research_system.models.db import Database, ResearchTask, ResearchResult
from src.research_system.agents.planner import PlannerAgent


@pytest.fixture
def mock_config():
    """Return a mock configuration for testing."""
    return {
        "app": {"port": 8080, "max_workers": 4},
        "logging": {"level": "INFO"},
        "environment": "test",
        "brave_search": {
            "api_key": "test_api_key",
            "endpoint": "https://api.search.brave.com/res/v1/web/search",
            "max_results": 5
        }
    }


@pytest.fixture
def mock_brave_search_response():
    """Return a mock Brave Search API response."""
    return {
        "web": {
            "results": [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/1",
                    "description": "This is test result 1."
                },
                {
                    "title": "Test Result 2",
                    "url": "https://example.com/2",
                    "description": "This is test result 2."
                },
                {
                    "title": "Test Result 3",
                    "url": "https://example.com/3",
                    "description": "This is test result 3."
                }
            ],
            "meta": {
                "total_results": 3,
                "next_offset": 0
            }
        }
    }


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path for testing."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    # Clean up the temp file after the test
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def test_db(temp_db_path, monkeypatch):
    """Create a test database with a temporary file."""
    # Force TinyDB for testing to avoid PostgreSQL connection issues
    monkeypatch.setenv("USE_POSTGRES", "false")
    return Database(db_path=temp_db_path)


@pytest.fixture
def test_server():
    """Create a test FastMCP server."""
    server = FastMCPServer("Test Server")
    return server


@pytest.fixture
def test_context():
    """Create a test context for progress tracking."""
    return Context(task_id="test_task")


@pytest.fixture
def mock_requests():
    """Mock the requests library for testing API calls."""
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        yield {
            'get': mock_get,
            'post': mock_post
        }


@pytest.fixture
def sample_task():
    """Create a sample research task for testing."""
    return ResearchTask(
        id="test_task_1",
        title="Test Task",
        description="This is a test task for testing.",
        tags=["test", "research"]
    )


@pytest.fixture
def sample_result():
    """Create a sample research result for testing."""
    return ResearchResult(
        id="test_result_1",
        task_id="test_task_1",
        content="This is a test result content.",
        format="text",
        created_by="test_agent"
    )


@pytest.fixture
def test_planner(test_server, test_db):
    """Create a test planner agent."""
    return PlannerAgent(name="test_planner", server=test_server, db=test_db)
