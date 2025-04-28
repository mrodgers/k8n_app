"""
Tests for the Ollama client.

This module contains tests for the Ollama client implementation.
"""

import json
import pytest
import asyncio
from unittest.mock import MagicMock, patch
import httpx
from src.research_system.llm.ollama_client import (
    OllamaClient, 
    SyncOllamaClient,
    create_ollama_client, 
    Message
)

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
                "families": None,
                "parameter_size": "7B",
                "quantization_level": "Q4_0"
            }
        }
    ]
}
SAMPLE_RUNNING_MODELS = {
    "models": [
        {
            "name": "mistral:latest",
            "model": "mistral:latest",
            "size": 5137025024,
            "digest": "2ae6f6dd7a3dd734790bbbf58b8909a606e0e7e97e94b7604e0aa7ae4490e6d8",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "llama",
                "families": ["llama"],
                "parameter_size": "7.2B",
                "quantization_level": "Q4_0"
            },
            "expires_at": "2024-06-04T14:38:31.83753-07:00",
            "size_vram": 5137025024
        }
    ]
}
SAMPLE_COMPLETION = {
    "model": "mistral:latest",
    "created_at": "2023-08-04T19:22:45.499127Z",
    "response": "The sky is blue because of Rayleigh scattering.",
    "done": True,
    "context": [1, 2, 3],
    "total_duration": 4935886791,
    "load_duration": 534986708,
    "prompt_eval_count": 26,
    "prompt_eval_duration": 107345000,
    "eval_count": 237,
    "eval_duration": 4289432000
}
SAMPLE_CHAT_COMPLETION = {
    "model": "mistral:latest",
    "created_at": "2023-12-12T14:13:43.416799Z",
    "message": {
        "role": "assistant",
        "content": "The sky is blue because of Rayleigh scattering."
    },
    "done": True,
    "total_duration": 5191566416,
    "load_duration": 2154458,
    "prompt_eval_count": 26,
    "prompt_eval_duration": 383809000,
    "eval_count": 298,
    "eval_duration": 4799921000
}
SAMPLE_EMBEDDINGS = {
    "model": "all-minilm",
    "embeddings": [[
        0.010071029, -0.0017594862, 0.05007221, 0.04692972, 0.054916814
    ]],
    "total_duration": 14143917,
    "load_duration": 1019500,
    "prompt_eval_count": 8
}
SAMPLE_PULL_RESULT = {
    "status": "success"
}

# Helper for async tests
async def mock_response(status_code=200, json_data=None, text=None, is_stream=False):
    """Create a mock response for httpx."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    
    if status_code >= 400:
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP Error {status_code}",
            request=MagicMock(),
            response=mock_resp
        )
    
    if json_data:
        mock_resp.json.return_value = json_data
    
    if text:
        mock_resp.text = text
    
    if is_stream:
        mock_resp.iter_lines.return_value = [json.dumps(line) for line in (json_data or [])]
    
    return mock_resp

# Synchronous client tests
class TestSyncOllamaClient:
    """Tests for the synchronous Ollama client."""
    
    @pytest.fixture
    def client(self):
        """Create a client fixture."""
        with patch('httpx.Client'):
            client = SyncOllamaClient(base_url="http://test-ollama:11434")
            return client
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == "http://test-ollama:11434"
        assert client.timeout == 120
    
    def test_get_version(self, client):
        """Test getting the Ollama version."""
        with patch.object(client.client, 'get', return_value=mock_response(json_data=SAMPLE_VERSION)):
            version = client.get_version()
            assert version == SAMPLE_VERSION
            client.client.get.assert_called_once_with(f"{client.base_url}/api/version")
    
    def test_list_models(self, client):
        """Test listing available models."""
        with patch.object(client.client, 'get', return_value=mock_response(json_data=SAMPLE_MODELS)):
            models = client.list_models()
            assert models == SAMPLE_MODELS
            client.client.get.assert_called_once_with(f"{client.base_url}/api/tags")
    
    def test_list_running_models(self, client):
        """Test listing running models."""
        with patch.object(client.client, 'get', return_value=mock_response(json_data=SAMPLE_RUNNING_MODELS)):
            models = client.list_running_models()
            assert models == SAMPLE_RUNNING_MODELS
            client.client.get.assert_called_once_with(f"{client.base_url}/api/ps")
    
    def test_generate_completion(self, client):
        """Test generating a completion."""
        with patch.object(client.client, 'post', return_value=mock_response(json_data=SAMPLE_COMPLETION)):
            result = client.generate_completion(
                model="mistral:latest",
                prompt="Why is the sky blue?",
                stream=False
            )
            assert result == SAMPLE_COMPLETION
            client.client.post.assert_called_once()
    
    def test_generate_chat_completion(self, client):
        """Test generating a chat completion."""
        with patch.object(client.client, 'post', return_value=mock_response(json_data=SAMPLE_CHAT_COMPLETION)):
            result = client.generate_chat_completion(
                model="mistral:latest",
                messages=[{"role": "user", "content": "Why is the sky blue?"}],
                stream=False
            )
            assert result == SAMPLE_CHAT_COMPLETION
            client.client.post.assert_called_once()
    
    def test_generate_embeddings(self, client):
        """Test generating embeddings."""
        with patch.object(client.client, 'post', return_value=mock_response(json_data=SAMPLE_EMBEDDINGS)):
            result = client.generate_embeddings(
                model="all-minilm",
                input_text="Why is the sky blue?"
            )
            assert result == SAMPLE_EMBEDDINGS
            client.client.post.assert_called_once()
    
    def test_pull_model(self, client):
        """Test pulling a model."""
        with patch.object(client.client, 'post', return_value=mock_response(json_data=SAMPLE_PULL_RESULT)):
            result = client.pull_model(model="mistral:latest")
            assert result == SAMPLE_PULL_RESULT
            client.client.post.assert_called_once()
    
    def test_is_model_available(self, client):
        """Test checking if a model is available."""
        with patch.object(client.client, 'get', return_value=mock_response(json_data=SAMPLE_MODELS)):
            result = client.is_model_available("mistral:latest")
            assert result is True
            
            result = client.is_model_available("nonexistent-model")
            assert result is False
    
    def test_preload_model(self, client):
        """Test preloading a model."""
        with patch.object(client.client, 'post', return_value=mock_response(json_data={"result": "success"})):
            result = client.preload_model(model="mistral:latest")
            assert result is True
            client.client.post.assert_called_once()
    
    def test_unload_model(self, client):
        """Test unloading a model."""
        with patch.object(client.client, 'post', return_value=mock_response(json_data={"result": "success"})):
            result = client.unload_model(model="mistral:latest")
            assert result is True
            client.client.post.assert_called_once()
    
    def test_http_error_handling(self, client):
        """Test HTTP error handling."""
        with patch.object(client.client, 'get', return_value=mock_response(status_code=404)):
            with pytest.raises(httpx.HTTPStatusError):
                client.get_version()

# Asynchronous client tests
class TestAsyncOllamaClient:
    """Tests for the asynchronous Ollama client."""
    
    @pytest.fixture
    async def client(self):
        """Create an async client fixture."""
        with patch('httpx.AsyncClient'):
            client = OllamaClient(base_url="http://test-ollama:11434")
            yield client
            await client.close()
    
    @pytest.mark.asyncio
    async def test_init(self, client):
        """Test async client initialization."""
        assert client.base_url == "http://test-ollama:11434"
        assert client.timeout == 120
    
    @pytest.mark.asyncio
    async def test_get_version(self, client):
        """Test getting the Ollama version."""
        response = await mock_response(json_data=SAMPLE_VERSION)
        with patch.object(client.client, 'get', return_value=response):
            version = await client.get_version()
            assert version == SAMPLE_VERSION
            client.client.get.assert_called_once_with(f"{client.base_url}/api/version")
    
    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """Test listing available models."""
        response = await mock_response(json_data=SAMPLE_MODELS)
        with patch.object(client.client, 'get', return_value=response):
            models = await client.list_models()
            assert models == SAMPLE_MODELS
            client.client.get.assert_called_once_with(f"{client.base_url}/api/tags")
    
    @pytest.mark.asyncio
    async def test_list_running_models(self, client):
        """Test listing running models."""
        response = await mock_response(json_data=SAMPLE_RUNNING_MODELS)
        with patch.object(client.client, 'get', return_value=response):
            models = await client.list_running_models()
            assert models == SAMPLE_RUNNING_MODELS
            client.client.get.assert_called_once_with(f"{client.base_url}/api/ps")
    
    @pytest.mark.asyncio
    async def test_generate_completion(self, client):
        """Test generating a completion."""
        response = await mock_response(json_data=SAMPLE_COMPLETION)
        with patch.object(client.client, 'post', return_value=response):
            result = await client.generate_completion(
                model="mistral:latest",
                prompt="Why is the sky blue?",
                stream=False
            )
            assert result == SAMPLE_COMPLETION
            client.client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_completion_streaming(self, client):
        """Test generating a streaming completion."""
        stream_data = [
            {"model": "mistral", "response": "The", "done": False},
            {"model": "mistral", "response": " sky", "done": False},
            {"model": "mistral", "response": " is", "done": False},
            {"model": "mistral", "response": " blue", "done": True}
        ]
        response = await mock_response(json_data=stream_data, is_stream=True)
        
        with patch.object(client.client, 'post', return_value=response):
            results = await client.generate_completion(
                model="mistral:latest",
                prompt="Why is the sky blue?",
                stream=True
            )
            assert len(results) == 4
            client.client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_chat_completion(self, client):
        """Test generating a chat completion."""
        response = await mock_response(json_data=SAMPLE_CHAT_COMPLETION)
        with patch.object(client.client, 'post', return_value=response):
            result = await client.generate_chat_completion(
                model="mistral:latest",
                messages=[{"role": "user", "content": "Why is the sky blue?"}],
                stream=False
            )
            assert result == SAMPLE_CHAT_COMPLETION
            client.client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(self, client):
        """Test generating embeddings."""
        response = await mock_response(json_data=SAMPLE_EMBEDDINGS)
        with patch.object(client.client, 'post', return_value=response):
            result = await client.generate_embeddings(
                model="all-minilm",
                input_text="Why is the sky blue?"
            )
            assert result == SAMPLE_EMBEDDINGS
            client.client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pull_model(self, client):
        """Test pulling a model."""
        response = await mock_response(json_data=SAMPLE_PULL_RESULT)
        with patch.object(client.client, 'post', return_value=response):
            result = await client.pull_model(model="mistral:latest")
            assert result == SAMPLE_PULL_RESULT
            client.client.post.assert_called_once()

# Test factory function
def test_create_ollama_client():
    """Test the create_ollama_client factory function."""
    with patch('httpx.Client'):
        with patch('httpx.AsyncClient'):
            sync_client = create_ollama_client(async_client=False)
            assert isinstance(sync_client, SyncOllamaClient)
            
            async_client = create_ollama_client(async_client=True)
            assert isinstance(async_client, OllamaClient)

# Test Message model
def test_message_model():
    """Test the Message model."""
    # Test with required fields only
    message = Message(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.images is None
    assert message.tool_calls is None
    
    # Test with all fields
    message = Message(
        role="user",
        content="Hello",
        images=["base64_image_data"],
        tool_calls=[{"function": {"name": "get_weather", "arguments": {"location": "New York"}}}]
    )
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.images == ["base64_image_data"]
    assert len(message.tool_calls) == 1
    assert message.tool_calls[0]["function"]["name"] == "get_weather"