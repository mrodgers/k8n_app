"""
Tests for the CLI command parsing functionality.

This module contains tests for the CLI's ability to parse and validate
command-line arguments.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the CLI module
from src.research_system.cli.main import parse_args, validate_args


class TestCommandParsing:
    """Test suite for CLI command parsing."""

    def test_parse_search_command(self):
        """Test parsing a search command."""
        with patch('sys.argv', ['cli.py', 'search', '--query', 'test query', '--max-results', '5']):
            args = parse_args()
            
            assert args.command == 'search'
            assert args.query == 'test query'
            assert args.max_results == 5

    def test_parse_task_command(self):
        """Test parsing a task command."""
        with patch('sys.argv', ['cli.py', 'task', 'create', '--title', 'Test Task', 
                              '--description', 'Test description']):
            args = parse_args()
            
            assert args.command == 'task'
            assert args.subcommand == 'create'
            assert args.title == 'Test Task'
            assert args.description == 'Test description'

    def test_parse_task_list_command(self):
        """Test parsing a task list command."""
        with patch('sys.argv', ['cli.py', 'task', 'list', '--status', 'pending']):
            args = parse_args()
            
            assert args.command == 'task'
            assert args.subcommand == 'list'
            assert args.status == 'pending'

    def test_parse_result_command(self):
        """Test parsing a result command."""
        with patch('sys.argv', ['cli.py', 'result', 'get', '--id', 'test_result_1']):
            args = parse_args()
            
            assert args.command == 'result'
            assert args.subcommand == 'get'
            assert args.id == 'test_result_1'

    def test_validate_search_args_valid(self):
        """Test validating valid search args."""
        args = MagicMock()
        args.command = 'search'
        args.query = 'test query'
        args.max_results = 5
        
        # Should not raise any exceptions
        validate_args(args)

    def test_validate_search_args_invalid(self):
        """Test validating invalid search args."""
        args = MagicMock()
        args.command = 'search'
        args.query = ''  # Empty query
        args.max_results = 5
        
        with pytest.raises(ValueError) as excinfo:
            validate_args(args)
        
        assert "Query cannot be empty" in str(excinfo.value)

    def test_validate_task_create_args_invalid(self):
        """Test validating invalid task create args."""
        args = MagicMock()
        args.command = 'task'
        args.subcommand = 'create'
        args.title = ''  # Empty title
        args.description = 'Test description'
        
        with pytest.raises(ValueError) as excinfo:
            validate_args(args)
        
        assert "Title cannot be empty" in str(excinfo.value)
