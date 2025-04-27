"""
Tests for the Search Agent's API connection functionality.

This module contains tests for the Search Agent's ability to connect to
and retrieve results from the Brave Search API.
"""

import pytest
import json
from unittest.mock import MagicMock, patch

# Import the search agent implementation
from src.research_system.agents.search import SearchAgent, SearchQuery, SearchResult


class TestSearchApiConnection:
    """Test suite for the Search Agent's API connection."""

    def test_init_with_config(self, mock_config):
        """Test initializing the search agent with configuration."""
        search_agent = SearchAgent(config=mock_config)
        assert search_agent.api_key == "test_api_key"
        assert search_agent.endpoint == "https://api.search.brave.com/res/v1/web/search"
        assert search_agent.max_results == 5

    def test_search_query_construction(self, mock_config):
        """Test constructing a search query."""
        search_agent = SearchAgent(config=mock_config)
        query = "test query"
        task_id = "test_task_1"
        
        search_query = search_agent.create_search_query(task_id=task_id, query=query)
        
        assert search_query.task_id == task_id
        assert search_query.query == query
        assert search_query.max_results == 5

    def test_execute_search_success(self, mock_config, mock_requests, mock_brave_search_response):
        """Test executing a search with a successful API response."""
        # Configure the mock response
        mock_requests['get'].return_value.status_code = 200
        mock_requests['get'].return_value.json.return_value = mock_brave_search_response
        
        search_agent = SearchAgent(config=mock_config)
        task_id = "test_task_1"
        query = "test query"
        
        results = search_agent.execute_search(task_id=task_id, query=query)
        
        assert len(results) == 3
        assert results[0]['title'] == "Test Result 1"
        assert results[0]['url'] == "https://example.com/1"
        assert results[0]['snippet'] == "This is test result 1."

    def test_execute_search_api_error(self, mock_config, mock_requests):
        """Test handling API errors during search execution."""
        # Configure the mock response for an error
        mock_requests['get'].return_value.status_code = 401
        mock_requests['get'].return_value.text = "Unauthorized"
        
        search_agent = SearchAgent(config=mock_config)
        task_id = "test_task_1"
        query = "test query"
        
        # The function should raise an exception for API errors
        with pytest.raises(Exception) as excinfo:
            search_agent.execute_search(task_id=task_id, query=query)
        
        assert "API error" in str(excinfo.value)

    def test_retry_on_rate_limit(self, mock_config, mock_requests, mock_brave_search_response):
        """Test retry logic when encountering rate limits."""
        # First attempt returns a rate limit error, second succeeds
        response1 = MagicMock()
        response1.status_code = 429
        response1.text = "Rate limit exceeded"
        
        response2 = MagicMock()
        response2.status_code = 200
        response2.json.return_value = mock_brave_search_response
        
        mock_requests['get'].side_effect = [response1, response2]
        
        search_agent = SearchAgent(config=mock_config)
        task_id = "test_task_1"
        query = "test query"
        
        results = search_agent.execute_search(task_id=task_id, query=query)
        
        assert len(results) == 3
        assert mock_requests['get'].call_count == 2
