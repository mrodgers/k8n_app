"""
Unit Tests for the Ollama server.

This module contains basic unit tests for the Ollama server implementation.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.research_system.llm.ollama_server import OllamaServer
from src.research_system.core.server import FastMCPServer

# Test data
SAMPLE_VERSION = {"version": "0.1.17"}
SAMPLE_MODELS = {
    "models": [
        {
            "name": "gemma3:1b",
            "modified_at": "2024-04-21T09:17:32.277302595-07:00",
            "size": 1765960935,
        }
    ]
}

class TestOllamaServerBasic:
    """Basic tests for the OllamaServer class."""
    
    def test_initialization(self):
        """Test basic initialization of the Ollama server."""
        # Create mock objects
        mock_server = MagicMock(spec=FastMCPServer)
        
        # Create patches
        with patch('src.research_system.llm.ollama_server.SyncOllamaClient') as mock_sync_client, \
             patch('src.research_system.llm.ollama_server.OllamaClient') as mock_async_client:
            
            # Configure mocks
            mock_sync_client_instance = MagicMock()
            mock_async_client_instance = MagicMock()
            mock_sync_client.return_value = mock_sync_client_instance
            mock_async_client.return_value = mock_async_client_instance
            
            # Initialize server
            server = OllamaServer(
                name="test-ollama",
                server=mock_server,
                config={
                    "model": "gemma3:1b",
                    "url": "http://localhost:11434",
                    "timeout": 30
                }
            )
            
            # Assert initialization
            assert server.name == "test-ollama"
            assert server.default_model == "gemma3:1b"
            assert server.base_url == "http://localhost:11434"
            assert server.timeout == 30
            
            # Verify clients were created
            mock_sync_client.assert_called_once_with(
                base_url="http://localhost:11434", 
                timeout=30
            )
            mock_async_client.assert_called_once_with(
                base_url="http://localhost:11434", 
                timeout=30
            )
    
    def test_register_tools(self):
        """Test registration of tools."""
        # Create mock objects
        mock_server = MagicMock(spec=FastMCPServer)
        
        # Create patches
        with patch('src.research_system.llm.ollama_server.SyncOllamaClient'), \
             patch('src.research_system.llm.ollama_server.OllamaClient'):
            
            # Initialize server
            server = OllamaServer(
                name="test-ollama",
                server=mock_server,
                config={
                    "model": "gemma3:1b"
                }
            )
            
            # Verify that register_tool was called for essential tools
            assert mock_server.register_tool.call_count > 0
            
            # Check a few specific tools that should be registered
            tool_names = [call[0][0] for call in mock_server.register_tool.call_args_list]
            essential_tools = [
                "generate_completion",
                "generate_chat_completion",
                "get_version"
            ]
            
            for tool in essential_tools:
                assert tool in tool_names