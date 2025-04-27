"""
Integration tests for basic workflows in the Research System.

This module contains integration tests for the end-to-end workflows
in the Research System, focusing on the interaction between components.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

# Import necessary modules
from src.research_system.core.coordinator import Coordinator, Agent
from src.research_system.core.server import Context
from src.research_system.agents.planner import PlannerAgent
from src.research_system.agents.search import SearchAgent
from src.research_system.models.db import Database, ResearchTask, ResearchResult


class TestBasicWorkflow:
    """Test suite for basic end-to-end workflows."""

    def test_create_task_and_search(self, test_db, mock_config, mock_requests, mock_brave_search_response):
        """Test creating a task and performing a search."""
        # Set up mock responses
        mock_requests['get'].return_value.status_code = 200
        mock_requests['get'].return_value.json.return_value = mock_brave_search_response
        
        # Create agents
        planner_agent = PlannerAgent(name="test_planner", db=test_db)
        search_agent = SearchAgent(name="test_search", config=mock_config, db=test_db)
        
        # Create a task using the planner agent
        task = planner_agent.create_research_task(
            title="Test Research Task",
            description="Research about testing frameworks",
            tags=["testing", "frameworks"]
        )
        
        # Convert task dictionary to ResearchTask object for assertion
        task_id = task['id']
        task_obj = test_db.get_task(task_id)
        
        # Generate a plan for the task using the planner agent
        plan = planner_agent.generate_plan_for_task(task_id)
        
        # Execute a search using the search agent
        search_results = search_agent.execute_search(
            task_id=task_id,
            query="Python testing frameworks comparison"
        )
        
        # Store results
        search_agent.store_search_results(task_id, search_results)
        
        # Verify results
        assert task_obj is not None
        assert task_obj.id == task_id
        assert task_obj.title == "Test Research Task"
        assert plan["task_id"] == task_id
        assert len(plan["steps"]) > 0
        assert len(search_results) == 3
        assert search_results[0]['title'] == "Test Result 1"
        
        # Verify the results were stored in the database
        db_results = test_db.list_results_for_task(task_id)
        assert len(db_results) > 0
        
    def test_coordinator_integration(self, test_db, mock_config, mock_requests, mock_brave_search_response):
        """Test integration between coordinator and agents."""
        # Set up mock responses
        mock_requests['get'].return_value.status_code = 200
        mock_requests['get'].return_value.json.return_value = mock_brave_search_response
        
        # Create a coordinator
        coordinator = Coordinator("Test Coordinator")
        
        # Create agents
        planner_agent = PlannerAgent(name="test_planner", db=test_db)
        search_agent = SearchAgent(name="test_search", config=mock_config, db=test_db)
        
        # Create agent representations for the coordinator
        planner_agent_info = Agent(
            name="test_planner",
            server_url="http://localhost:8080",
            description="Test planner agent",
            tools=["create_research_task", "generate_plan_for_task"]
        )
        
        search_agent_info = Agent(
            name="test_search",
            server_url="http://localhost:8080",
            description="Test search agent",
            tools=["execute_search"]
        )
        
        # Register agents with coordinator
        coordinator.register_agent(planner_agent_info)
        coordinator.register_agent(search_agent_info)
        
        # Verify agents are registered
        assert len(coordinator.list_agents()) == 2
        assert "test_planner" in coordinator.list_agents()
        assert "test_search" in coordinator.list_agents()
        
        # Verify we can get agents by name
        planner_info = coordinator.get_agent("test_planner") 
        assert planner_info.name == "test_planner"
        assert "create_research_task" in planner_info.tools
        
        search_info = coordinator.get_agent("test_search")
        assert search_info.name == "test_search"
        assert "execute_search" in search_info.tools
        
    def test_server_tool_registration(self, test_server):
        """Test tool registration with FastMCP server."""
        # Define a simple tool function
        def test_tool(arg1, arg2):
            return f"{arg1} - {arg2}"
        
        # Register the tool with the server
        test_server.register_tool(
            name="test_tool",
            tool_func=test_tool,
            description="A test tool function"
        )
        
        # Verify the tool was registered
        assert "test_tool" in test_server.tools
        assert test_server.tools["test_tool"]["description"] == "A test tool function"
        
        # Ensure we can call the tool function
        result = test_server.tools["test_tool"]["function"]("hello", "world")
        assert result == "hello - world"
