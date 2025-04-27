"""
Tests for the CLI workflow functionality.

This module contains tests for the CLI's ability to execute commands
and interact with the research system components.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Import the CLI module
from src.research_system.cli.main import (
    execute_search_command, 
    execute_task_command, 
    execute_result_command,
    execute_plan_command,
    main
)

class TestCLIWorkflow:
    """Test suite for CLI workflow execution."""
    
    def test_search_command_execution(self, mock_config, mock_requests, mock_brave_search_response):
        """Test executing a search command."""
        # Mock the requests response
        mock_requests['get'].return_value.status_code = 200
        mock_requests['get'].return_value.json.return_value = mock_brave_search_response
        
        # Create a mock args object
        args = MagicMock()
        args.query = "test query"
        args.task_id = None  # Will create a temporary task
        args.max_results = 5
        args.output = "text"
        
        # Create a mock database
        db = MagicMock()
        db.create_task.return_value = MagicMock(id="temp_123")
        
        # Create a mock search agent
        search_agent = MagicMock()
        search_agent.create_search_query.return_value = MagicMock(id="query_1")
        search_agent.execute_search.return_value = [
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "snippet": "This is test result 1."
            }
        ]
        
        # Execute the search command
        with patch('src.research_system.cli.main.console.print'), \
             patch('src.research_system.cli.main.Progress'), \
             patch('sys.exit') as mock_exit:
            execute_search_command(args, search_agent=search_agent, db=db)
            
            # Verify the search agent methods were called
            search_agent.execute_search.assert_called_once()
            search_agent.store_search_results.assert_called_once()
            mock_exit.assert_not_called()  # Should not exit
    
    def test_task_create_command(self):
        """Test executing a task create command."""
        # Create a mock args object
        args = MagicMock()
        args.subcommand = "create"
        args.title = "Test Task"
        args.description = "This is a test task"
        args.tags = ["test", "cli"]
        
        # Create a mock planner agent
        planner_agent = MagicMock()
        planner_agent.create_research_task.return_value = {
            "id": "task_1",
            "title": "Test Task",
            "description": "This is a test task",
            "tags": ["test", "cli"]
        }
        
        # Execute the task command
        with patch('src.research_system.cli.main.console.print'), \
             patch('src.research_system.cli.main.Progress'), \
             patch('sys.exit') as mock_exit:
            execute_task_command(args, planner_agent=planner_agent)
            
            # Verify the planner agent method was called
            planner_agent.create_research_task.assert_called_once_with(
                title="Test Task",
                description="This is a test task",
                tags=["test", "cli"]
            )
            mock_exit.assert_not_called()  # Should not exit
    
    def test_execute_task_list_command(self):
        """Test executing a task list command."""
        # Create a mock args object
        args = MagicMock()
        args.subcommand = "list"
        args.status = "pending"
        args.assigned_to = None
        args.tag = None
        
        # Create a mock planner agent
        planner_agent = MagicMock()
        planner_agent.list_research_tasks.return_value = [
            {
                "id": "test_task_1",
                "title": "Test Task 1",
                "description": "Test description 1",
                "tags": ["test"],
                "status": "pending"
            },
            {
                "id": "test_task_2",
                "title": "Test Task 2",
                "description": "Test description 2",
                "tags": ["research"],
                "status": "pending"
            }
        ]
        
        # Execute the task command
        with patch('src.research_system.cli.main.console.print'), \
             patch('src.research_system.cli.main.Progress'), \
             patch('src.research_system.cli.main.Table'), \
             patch('sys.exit') as mock_exit:
            execute_task_command(args, planner_agent=planner_agent)
            
            # Verify the planner agent was called with the right parameters
            planner_agent.list_research_tasks.assert_called_once_with(
                status="pending",
                assigned_to=None,
                tag=None
            )
            mock_exit.assert_not_called()  # Should not exit
    
    def test_execute_result_get_command(self):
        """Test executing a result get command."""
        # Create a mock args object
        args = MagicMock()
        args.subcommand = "get"
        args.id = "test_result_1"
        
        # Create a mock result
        mock_result = MagicMock()
        mock_result.id = "test_result_1"
        mock_result.task_id = "test_task_1"
        mock_result.content = "This is test result content."
        mock_result.format = "text"
        mock_result.status = "draft"
        mock_result.created_at = 1619712000.0  # Example timestamp
        mock_result.updated_at = 1619712000.0  # Example timestamp
        mock_result.created_by = "test_agent"
        mock_result.tags = ["test", "result"]
        
        # Create a mock database
        db = MagicMock()
        db.get_result.return_value = mock_result
        
        # Execute the result command
        with patch('src.research_system.cli.main.console.print'), \
             patch('src.research_system.cli.main.Progress'), \
             patch('src.research_system.cli.main.Table'), \
             patch('sys.exit') as mock_exit:
            execute_result_command(args, db=db)
            
            # Verify the database was called with the right parameters
            db.get_result.assert_called_once_with("test_result_1")
            mock_exit.assert_not_called()  # Should not exit
    
    def test_plan_create_command(self):
        """Test executing a plan create command."""
        # Create a mock args object
        args = MagicMock()
        args.subcommand = "create"
        args.task_id = "task_1"
        
        # Create a mock planner agent
        planner_agent = MagicMock()
        planner_agent.generate_plan_for_task.return_value = {
            "id": "plan_1",
            "task_id": "task_1",
            "steps": [
                {
                    "id": 1,
                    "name": "Test Step",
                    "type": "search",
                    "status": "pending",
                    "description": "A test step"
                }
            ],
            "status": "draft"
        }
        
        # Execute the plan command
        with patch('src.research_system.cli.main.console.print'), \
             patch('src.research_system.cli.main.Progress'), \
             patch('src.research_system.cli.main.Table'), \
             patch('sys.exit') as mock_exit:
            execute_plan_command(args, planner_agent=planner_agent)
            
            # Verify the planner agent method was called
            planner_agent.generate_plan_for_task.assert_called_once()
            mock_exit.assert_not_called()  # Should not exit
    
    def test_main_function_args_parsing(self):
        """Test the main function's argument parsing."""
        # Mock sys.argv
        test_args = ['cli.py', 'search', '--query', 'test query']
        with patch('sys.argv', test_args), \
             patch('src.research_system.cli.main.console.print'), \
             patch('src.research_system.cli.main.execute_search_command') as mock_search, \
             patch('sys.exit') as mock_exit:
                
            # Run the main function
            main()
            
            # Verify execute_search_command was called
            mock_search.assert_called_once()
            mock_exit.assert_not_called()  # Should not exit
    
    def test_main_function_error_handling(self):
        """Test the main function's error handling."""
        # Mock sys.argv for an invalid command (empty command)
        with patch('sys.argv', ['cli.py']), \
             patch('src.research_system.cli.main.console.print'), \
             patch('sys.exit') as mock_exit:
                
            # Run the main function
            main()
            
            # Verify error handling was triggered
            mock_exit.assert_called_once_with(1)  # Should exit with code 1
