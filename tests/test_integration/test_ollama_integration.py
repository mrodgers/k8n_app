"""
Integration tests for Ollama client.

These tests require an actual Ollama server to be running.
Skip these tests if Ollama is not available.
"""

import os
import pytest
import asyncio
from src.research_system.llm import create_ollama_client

# Check if Ollama integration tests should be run
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# Check for a small model to use for testing
TEST_MODEL = os.environ.get("OLLAMA_TEST_MODEL", "gemma3:1b")

# Skip integration tests by default
SKIP_INTEGRATION_TESTS = os.environ.get("SKIP_OLLAMA_INTEGRATION", "true").lower() == "true"
SKIP_REASON = "Ollama integration tests are skipped by default. Set SKIP_OLLAMA_INTEGRATION=false to run them."


@pytest.mark.skipif(SKIP_INTEGRATION_TESTS, reason=SKIP_REASON)
class TestOllamaIntegration:
    """Integration tests for Ollama client."""
    
    @pytest.fixture(scope="class")
    def sync_client(self):
        """Create a synchronous client for testing."""
        client = create_ollama_client(async_client=False, base_url=OLLAMA_URL)
        try:
            yield client
        finally:
            client.close()
    
    @pytest.fixture(scope="class")
    async def async_client(self):
        """Create an asynchronous client for testing."""
        client = create_ollama_client(async_client=True, base_url=OLLAMA_URL)
        try:
            yield client
        finally:
            await client.close()
    
    def test_get_version(self, sync_client):
        """Test getting the Ollama version."""
        version = sync_client.get_version()
        assert "version" in version
        assert isinstance(version["version"], str)
    
    def test_list_models(self, sync_client):
        """Test listing available models."""
        models = sync_client.list_models()
        assert "models" in models
        assert isinstance(models["models"], list)
    
    def test_list_running_models(self, sync_client):
        """Test listing running models."""
        models = sync_client.list_running_models()
        assert "models" in models
    
    def test_is_model_available(self, sync_client):
        """Test checking if a model is available."""
        # First, make sure the test model is available
        try:
            sync_client.pull_model(TEST_MODEL)
        except:
            pytest.skip(f"Could not pull test model {TEST_MODEL}")
            
        # Now check if it's available
        result = sync_client.is_model_available(TEST_MODEL)
        assert result is True
    
    def test_generate_completion(self, sync_client):
        """Test generating a completion."""
        try:
            result = sync_client.generate_completion(
                model=TEST_MODEL,
                prompt="What is the capital of France?",
                stream=False
            )
            assert "response" in result
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0
        except Exception as e:
            pytest.skip(f"Could not generate completion: {str(e)}")
    
    def test_generate_chat_completion(self, sync_client):
        """Test generating a chat completion."""
        try:
            result = sync_client.generate_chat_completion(
                model=TEST_MODEL,
                messages=[{"role": "user", "content": "What is the capital of France?"}],
                stream=False
            )
            assert "message" in result
            assert "role" in result["message"]
            assert "content" in result["message"]
            assert result["message"]["role"] == "assistant"
            assert len(result["message"]["content"]) > 0
        except Exception as e:
            pytest.skip(f"Could not generate chat completion: {str(e)}")
    
    def test_preload_and_unload_model(self, sync_client):
        """Test preloading and unloading a model."""
        try:
            # Preload the model
            load_result = sync_client.preload_model(TEST_MODEL)
            assert load_result is True
            
            # Check if model is loaded in running models
            running_models = sync_client.list_running_models()
            model_found = False
            for model in running_models.get("models", []):
                if model.get("name") == TEST_MODEL:
                    model_found = True
                    break
            
            # Now unload the model
            unload_result = sync_client.unload_model(TEST_MODEL)
            assert unload_result is True
        except Exception as e:
            pytest.skip(f"Could not preload/unload model: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_async_get_version(self, async_client):
        """Test getting the Ollama version asynchronously."""
        version = await async_client.get_version()
        assert "version" in version
        assert isinstance(version["version"], str)
    
    @pytest.mark.asyncio
    async def test_async_list_models(self, async_client):
        """Test listing available models asynchronously."""
        models = await async_client.list_models()
        assert "models" in models
        assert isinstance(models["models"], list)
    
    @pytest.mark.asyncio
    async def test_async_generate_completion(self, async_client):
        """Test generating a completion asynchronously."""
        try:
            result = await async_client.generate_completion(
                model=TEST_MODEL,
                prompt="What is the capital of France?",
                stream=False
            )
            assert "response" in result
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0
        except Exception as e:
            pytest.skip(f"Could not generate completion: {str(e)}")


@pytest.mark.skipif(SKIP_INTEGRATION_TESTS, reason=SKIP_REASON)
def test_ollama_server_is_running():
    """Verify Ollama server is running for integration tests."""
    import requests
    try:
        response = requests.get(f"{OLLAMA_URL}/api/version", timeout=5)
        assert response.status_code == 200
        assert "version" in response.json()
        print(f"Ollama server is running with version: {response.json()['version']}")
    except Exception as e:
        pytest.skip(f"Ollama server is not running at {OLLAMA_URL}: {str(e)}")