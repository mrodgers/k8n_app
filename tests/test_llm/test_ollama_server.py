"""
Tests for the Ollama server.

This module contains tests for the Ollama server implementation.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import httpx
from fastapi.testclient import TestClient
from src.research_system.llm.ollama_server import OllamaServer
from src.research_system.core.server import FastMCPServer

# Test data
SAMPLE_VERSION = {"version": "0.1.17"}
SAMPLE_MODELS = {
    "models": [
        {
            "name": "mistral:latest",
            "modified_at": "2023-11-04T14:56:49.277302595-07:00",
            "size": 7365960935,
            "digest": "9f438cb9cd581fc025612d27f7c1a6669ff83a8bb0ed86c94fcf4c5440555697",
            "details": {
                "format": "gguf",
                "family": "llama",
                "parameter_size": "7B",
                "quantization_level": "Q5_K_M"
            }
        },
        {
            "name": "gemma3:1b",
            "modified_at": "2024-04-21T09:17:32.277302595-07:00",
            "size": 1765960935,
            "digest": "cf438cb9cd581fc025612d27f7c1a6669ff83a8bb0ed86c94fcf4c5440555123",
            "details": {
                "format": "gguf",
                "family": "gemma",
                "parameter_size": "1B",
                "quantization_level": "Q4_K_M"
            }
        }
    ]
}
SAMPLE_COMPLETION = {
    "model": "gemma3:1b",
    "created_at": "2023-11-04T16:23:00Z",
    "message": {
        "role": "assistant",
        "content": "This is a sample response from the LLM."
    },
    "done": True,
    "total_duration": 890254000,
    "load_duration": 360189000,
    "prompt_eval_count": 22,
    "prompt_eval_duration": 83238000,
    "eval_count": 28,
    "eval_duration": 446336000
}

class TestOllamaServer:
    """Tests for the OllamaServer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock FastMCP server
        self.mock_server = MagicMock(spec=FastMCPServer)
        self.mock_server.register_tool = MagicMock()
        
        # Patch the SyncOllamaClient and OllamaClient
        self.sync_client_patch = patch("src.research_system.llm.ollama_server.SyncOllamaClient")
        self.async_client_patch = patch("src.research_system.llm.ollama_server.OllamaClient")
        
        self.mock_sync_client = self.sync_client_patch.start()
        self.mock_async_client = self.async_client_patch.start()
        
        # Configure the mock clients
        self.mock_sync_client_instance = MagicMock()
        self.mock_async_client_instance = MagicMock()
        
        self.mock_sync_client.return_value = self.mock_sync_client_instance
        self.mock_async_client.return_value = self.mock_async_client_instance
        
        # Set up mock responses for common methods
        self.mock_sync_client_instance.get_version.return_value = SAMPLE_VERSION
        self.mock_sync_client_instance.list_models.return_value = SAMPLE_MODELS
        self.mock_sync_client_instance.generate_chat_completion.return_value = SAMPLE_COMPLETION
        
        # Create the server instance
        self.server = OllamaServer(
            name="test-ollama",
            server=self.mock_server,
            config={
                "model": "gemma3:1b",
                "url": "http://localhost:11434",
                "timeout": 30
            }
        )
    
    def teardown_method(self):
        """Tear down test fixtures."""
        self.sync_client_patch.stop()
        self.async_client_patch.stop()
    
    def test_initialization(self):
        """Test server initialization."""
        assert self.server.name == "test-ollama"
        assert self.server.default_model == "gemma3:1b"
        assert self.server.base_url == "http://localhost:11434"
        assert self.server.timeout == 30
        
        # Verify client initialization
        self.mock_sync_client.assert_called_once_with(
            base_url="http://localhost:11434", 
            timeout=30
        )
        self.mock_async_client.assert_called_once_with(
            base_url="http://localhost:11434", 
            timeout=30
        )
    
    def test_register_tools(self):
        """Test tool registration."""
        # The tools should have been registered during initialization
        # Verify that register_tool was called for each expected tool
        expected_tools = [
            "generate_completion",
            "generate_chat_completion",
            "generate_embeddings",
            "extract_content",
            "assess_relevance",
            "generate_plan",
            "list_models",
            "preload_model",
            "pull_model",
            "get_version"
        ]
        
        # Verify each tool was registered
        actual_calls = [call[0][0] for call in self.mock_server.register_tool.call_args_list]
        for tool in expected_tools:
            assert tool in actual_calls
    
    def test_get_version(self):
        """Test get_version method."""
        # Call the method
        result = self.server.get_version()
        
        # Verify the client method was called
        self.mock_sync_client_instance.get_version.assert_called_once()
        
        # Verify the result includes expected fields
        assert "version" in result
        assert result["version"] == "0.1.17"
        assert "default_model" in result
        assert result["default_model"] == "gemma3:1b"
    
    def test_list_models(self):
        """Test list_models method."""
        # Call the method
        result = self.server.list_models()
        
        # Verify the client method was called
        self.mock_sync_client_instance.list_models.assert_called_once()
        
        # Verify the result is correct
        assert result == SAMPLE_MODELS
    
    def test_generate_chat_completion(self):
        """Test generate_chat_completion method."""
        # Prepare test data
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Call the method
        result = self.server.generate_chat_completion(
            messages=messages,
            model="gemma3:1b"
        )
        
        # Verify the client method was called with correct args
        self.mock_sync_client_instance.generate_chat_completion.assert_called_once_with(
            model="gemma3:1b",
            messages=messages,
            stream=False,
            options=None,
            tools=None
        )
        
        # Verify the result is correct
        assert result == SAMPLE_COMPLETION
    
    def test_extract_content(self):
        """Test extract_content method."""
        # Configure the mock to return a specific result
        self.mock_sync_client_instance.generate_chat_completion.return_value = {
            "message": {"content": "This is the extracted content."}
        }
        
        # Call the method
        result = self.server.extract_content(
            raw_text="Sample text to extract content from.",
            extraction_type="summary",
            max_length=500
        )
        
        # Verify the client method was called
        self.mock_sync_client_instance.generate_chat_completion.assert_called_once()
        
        # Verify the call arguments
        args, kwargs = self.mock_sync_client_instance.generate_chat_completion.call_args
        assert kwargs["model"] == "gemma3:1b"  # Should use default model
        assert len(kwargs["messages"]) == 2  # Should have system and user messages
        assert kwargs["stream"] == False
        
        # Verify the result contains expected fields
        assert "content" in result
        assert result["extraction_type"] == "summary"
        assert result["model"] == "gemma3:1b"
        assert "timestamp" in result
    
    def test_assess_relevance(self):
        """Test assess_relevance method."""
        # Configure the mock to return a specific result
        self.mock_sync_client_instance.generate_chat_completion.return_value = {
            "message": {"content": '{"relevance_score": 0.75, "justification": "Matches query well.", "key_matches": ["keyword1", "keyword2"]}'}
        }
        
        # Call the method
        result = self.server.assess_relevance(
            content="Sample content to assess relevance.",
            query="test query"
        )
        
        # Verify the client method was called
        self.mock_sync_client_instance.generate_chat_completion.assert_called_once()
        
        # Verify the call arguments
        args, kwargs = self.mock_sync_client_instance.generate_chat_completion.call_args
        assert kwargs["model"] == "gemma3:1b"  # Should use default model
        assert len(kwargs["messages"]) == 2  # Should have system and user messages
        assert kwargs["stream"] == False
        
        # The JSON extraction can be complex to test directly, so we'll just verify the result has expected fields
        assert "relevance_score" in result
        assert "justification" in result
        assert "query" in result
        assert result["model"] == "gemma3:1b"
        assert "timestamp" in result
    
    def test_generate_plan(self):
        """Test generate_plan method."""
        # Configure the mock to return a specific result with plan steps
        sample_steps = [
            {
                "id": 1,
                "type": "search",
                "name": "Initial Information Gathering",
                "description": "Gather information on the topic",
                "status": "pending"
            },
            {
                "id": 2,
                "type": "analysis",
                "name": "Information Analysis",
                "description": "Analyze the gathered information",
                "status": "pending",
                "depends_on": [1]
            }
        ]
        self.mock_sync_client_instance.generate_chat_completion.return_value = {
            "message": {"content": json.dumps(sample_steps)}
        }
        
        # Call the method
        result = self.server.generate_plan(
            title="Test Plan",
            description="This is a test plan",
            tags=["test", "plan"],
            num_steps=5
        )
        
        # Verify the client method was called
        self.mock_sync_client_instance.generate_chat_completion.assert_called_once()
        
        # Verify the call arguments
        args, kwargs = self.mock_sync_client_instance.generate_chat_completion.call_args
        assert kwargs["model"] == "gemma3:1b"  # Should use default model
        assert len(kwargs["messages"]) == 2  # Should have system and user messages
        
        # Verify the result contains expected fields
        assert result["title"] == "Test Plan"
        assert result["description"] == "This is a test plan"
        assert "tags" in result
        assert "steps" in result
        assert result["model"] == "gemma3:1b"
        assert "timestamp" in result

# Integration test for FastAPI endpoints using the OllamaServer
class TestOllamaServerAPIIntegration:
    """Integration tests for the OllamaServer with FastAPI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Patch the OllamaServer class
        self.ollama_server_patch = patch("src.research_system.llm.default_ollama_server")
        self.mock_ollama_server = self.ollama_server_patch.start()
        
        # Configure mock methods
        self.mock_ollama_server.generate_completion.return_value = SAMPLE_COMPLETION
        self.mock_ollama_server.generate_chat_completion.return_value = SAMPLE_COMPLETION
        self.mock_ollama_server.list_models.return_value = SAMPLE_MODELS
        
        # Import app here to avoid circular imports with patched dependencies
        from src.app import app
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Tear down test fixtures."""
        self.ollama_server_patch.stop()
    
    def test_llm_completion_endpoint(self):
        """Test the LLM completion endpoint."""
        # Make the request
        response = self.client.post(
            "/api/llm/completion",
            json={"prompt": "Hello, how are you?"}
        )
        
        # Verify the response
        assert response.status_code == 200
        assert "result" in response.json()
        assert response.json()["result"] == SAMPLE_COMPLETION
        
        # Verify the server method was called
        self.mock_ollama_server.generate_completion.assert_called_once()
    
    def test_llm_chat_endpoint(self):
        """Test the LLM chat completion endpoint."""
        # Make the request
        response = self.client.post(
            "/api/llm/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ]
            }
        )
        
        # Verify the response
        assert response.status_code == 200
        assert "result" in response.json()
        assert response.json()["result"] == SAMPLE_COMPLETION
        
        # Verify the server method was called
        self.mock_ollama_server.generate_chat_completion.assert_called_once()
    
    def test_llm_models_endpoint(self):
        """Test the LLM models endpoint."""
        # Make the request
        response = self.client.get("/api/llm/models")
        
        # Verify the response
        assert response.status_code == 200
        assert "models" in response.json()
        assert len(response.json()["models"]) == 2
        assert response.json() == SAMPLE_MODELS
        
        # Verify the server method was called
        self.mock_ollama_server.list_models.assert_called_once()