"""
Ollama API Client for the Research System.

This module provides a client for interacting with the Ollama API server,
enabling the research system to use local LLM models for various tasks.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
import httpx
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Message(BaseModel):
    """Model representing a chat message."""
    role: str  # 'system', 'user', 'assistant', or 'tool'
    content: str
    images: Optional[List[str]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class OllamaCompletionRequest(BaseModel):
    """Model representing a completion request to Ollama."""
    model: str
    prompt: str
    suffix: Optional[str] = None
    images: Optional[List[str]] = None
    format: Optional[Union[str, Dict[str, Any]]] = None
    options: Optional[Dict[str, Any]] = None
    system: Optional[str] = None
    template: Optional[str] = None
    stream: bool = True
    raw: Optional[bool] = None
    keep_alive: Optional[str] = None
    context: Optional[List[int]] = None

class OllamaChatRequest(BaseModel):
    """Model representing a chat request to Ollama."""
    model: str
    messages: List[Message]
    format: Optional[Union[str, Dict[str, Any]]] = None
    options: Optional[Dict[str, Any]] = None
    stream: bool = True
    keep_alive: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None

class OllamaEmbedRequest(BaseModel):
    """Model representing an embedding request to Ollama."""
    model: str
    input: Union[str, List[str]]
    truncate: Optional[bool] = None
    options: Optional[Dict[str, Any]] = None
    keep_alive: Optional[str] = None

class OllamaClient:
    """
    Client for interacting with the Ollama API server.
    
    This client provides methods for generating completions, chat responses,
    and embeddings using Ollama's local LLM models.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: The base URL of the Ollama API server.
            timeout: Timeout in seconds for API requests.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"Initialized Ollama client with base URL: {base_url}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get_version(self) -> Dict[str, str]:
        """
        Get the Ollama server version.
        
        Returns:
            A dictionary containing the version information.
        """
        url = f"{self.base_url}/api/version"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error getting Ollama version: {e}")
            raise
    
    async def list_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List models available on the Ollama server.
        
        Returns:
            A dictionary containing a list of available models.
        """
        url = f"{self.base_url}/api/tags"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error listing models: {e}")
            raise
    
    async def list_running_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List models that are currently loaded into memory.
        
        Returns:
            A dictionary containing a list of running models.
        """
        url = f"{self.base_url}/api/ps"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error listing running models: {e}")
            raise
    
    async def generate_completion(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        format: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate a completion for a given prompt.
        
        Args:
            model: The name of the model to use.
            prompt: The prompt to generate a completion for.
            stream: Whether to stream the response.
            system: Optional system message to override the model's default.
            options: Optional model parameters such as 'temperature'.
            format: Optional response format specification.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            If stream is False, a single response object.
            If stream is True, a list of response objects.
        """
        url = f"{self.base_url}/api/generate"
        
        request_data = OllamaCompletionRequest(
            model=model,
            prompt=prompt,
            stream=stream,
            system=system,
            options=options,
            format=format,
            **kwargs
        )
        
        try:
            response = await self.client.post(url, json=request_data.model_dump(exclude_none=True))
            response.raise_for_status()
            
            if stream:
                # Parse streaming response
                results = []
                for line in response.iter_lines():
                    if line.strip():
                        results.append(json.loads(line))
                return results
            else:
                # Parse single response
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    async def generate_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
        format: Optional[Union[str, Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate a chat completion for a conversation.
        
        Args:
            model: The name of the model to use.
            messages: List of message objects with 'role' and 'content'.
            stream: Whether to stream the response.
            options: Optional model parameters such as 'temperature'.
            format: Optional response format specification.
            tools: Optional list of tool specifications.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            If stream is False, a single response object.
            If stream is True, a list of response objects.
        """
        url = f"{self.base_url}/api/chat"
        
        # Convert dict messages to Message objects
        parsed_messages = [Message(**msg) if isinstance(msg, dict) else msg for msg in messages]
        
        request_data = OllamaChatRequest(
            model=model,
            messages=parsed_messages,
            stream=stream,
            options=options,
            format=format,
            tools=tools,
            **kwargs
        )
        
        try:
            response = await self.client.post(url, json=request_data.model_dump(exclude_none=True))
            response.raise_for_status()
            
            if stream:
                # Parse streaming response
                results = []
                for line in response.iter_lines():
                    if line.strip():
                        results.append(json.loads(line))
                return results
            else:
                # Parse single response
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error generating chat completion: {e}")
            raise
    
    async def generate_embeddings(
        self,
        model: str,
        input_text: Union[str, List[str]],
        truncate: Optional[bool] = None,
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text input.
        
        Args:
            model: The name of the model to use.
            input_text: Text or list of texts to generate embeddings for.
            truncate: Whether to truncate inputs to fit context length.
            options: Optional model parameters.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            A dictionary containing the embeddings.
        """
        url = f"{self.base_url}/api/embed"
        
        request_data = OllamaEmbedRequest(
            model=model,
            input=input_text,
            truncate=truncate,
            options=options,
            **kwargs
        )
        
        try:
            response = await self.client.post(url, json=request_data.model_dump(exclude_none=True))
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def pull_model(self, model: str) -> Dict[str, Any]:
        """
        Pull a model from the Ollama library.
        
        Args:
            model: The name of the model to pull.
            
        Returns:
            A dictionary containing the result of the pull operation.
        """
        url = f"{self.base_url}/api/pull"
        
        request_data = {
            "model": model,
            "stream": False
        }
        
        try:
            response = await self.client.post(url, json=request_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error pulling model: {e}")
            raise
    
    async def is_model_available(self, model_name: str) -> bool:
        """
        Check if a model is available on the Ollama server.
        
        Args:
            model_name: The name of the model to check.
            
        Returns:
            True if the model is available, False otherwise.
        """
        try:
            models = await self.list_models()
            for model in models.get("models", []):
                if model.get("name") == model_name:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    async def preload_model(self, model: str) -> bool:
        """
        Preload a model into memory.
        
        Args:
            model: The name of the model to preload.
            
        Returns:
            True if successful, False otherwise.
        """
        url = f"{self.base_url}/api/generate"
        
        request_data = {
            "model": model,
            "prompt": ""  # Empty prompt just loads the model
        }
        
        try:
            response = await self.client.post(url, json=request_data)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Error preloading model: {e}")
            return False
    
    async def unload_model(self, model: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model: The name of the model to unload.
            
        Returns:
            True if successful, False otherwise.
        """
        url = f"{self.base_url}/api/generate"
        
        request_data = {
            "model": model,
            "prompt": "",
            "keep_alive": 0  # Setting keep_alive to 0 unloads the model
        }
        
        try:
            response = await self.client.post(url, json=request_data)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Error unloading model: {e}")
            return False


# Create a non-async client for simpler use cases
class SyncOllamaClient:
    """
    Synchronous client for interacting with the Ollama API server.
    
    This client provides synchronous methods for generating completions, chat responses,
    and embeddings using Ollama's local LLM models.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120):
        """
        Initialize the synchronous Ollama client.
        
        Args:
            base_url: The base URL of the Ollama API server.
            timeout: Timeout in seconds for API requests.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
        logger.info(f"Initialized synchronous Ollama client with base URL: {base_url}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def get_version(self) -> Dict[str, str]:
        """
        Get the Ollama server version.
        
        Returns:
            A dictionary containing the version information.
        """
        url = f"{self.base_url}/api/version"
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error getting Ollama version: {e}")
            raise
    
    def list_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List models available on the Ollama server.
        
        Returns:
            A dictionary containing a list of available models.
        """
        url = f"{self.base_url}/api/tags"
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error listing models: {e}")
            raise
    
    def list_running_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List models that are currently loaded into memory.
        
        Returns:
            A dictionary containing a list of running models.
        """
        url = f"{self.base_url}/api/ps"
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error listing running models: {e}")
            raise
    
    def generate_completion(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        format: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate a completion for a given prompt.
        
        Args:
            model: The name of the model to use.
            prompt: The prompt to generate a completion for.
            stream: Whether to stream the response.
            system: Optional system message to override the model's default.
            options: Optional model parameters such as 'temperature'.
            format: Optional response format specification.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            If stream is False, a single response object.
            If stream is True, a list of response objects.
        """
        url = f"{self.base_url}/api/generate"
        
        request_data = OllamaCompletionRequest(
            model=model,
            prompt=prompt,
            stream=stream,
            system=system,
            options=options,
            format=format,
            **kwargs
        )
        
        try:
            response = self.client.post(url, json=request_data.model_dump(exclude_none=True))
            response.raise_for_status()
            
            if stream:
                # Parse streaming response
                results = []
                for line in response.iter_lines():
                    if line.strip():
                        results.append(json.loads(line))
                return results
            else:
                # Parse single response
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error generating completion: {e}")
            raise
    
    def generate_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
        format: Optional[Union[str, Dict[str, Any]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate a chat completion for a conversation.
        
        Args:
            model: The name of the model to use.
            messages: List of message objects with 'role' and 'content'.
            stream: Whether to stream the response.
            options: Optional model parameters such as 'temperature'.
            format: Optional response format specification.
            tools: Optional list of tool specifications.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            If stream is False, a single response object.
            If stream is True, a list of response objects.
        """
        url = f"{self.base_url}/api/chat"
        
        # Convert dict messages to Message objects
        parsed_messages = [Message(**msg) if isinstance(msg, dict) else msg for msg in messages]
        
        request_data = OllamaChatRequest(
            model=model,
            messages=parsed_messages,
            stream=stream,
            options=options,
            format=format,
            tools=tools,
            **kwargs
        )
        
        try:
            response = self.client.post(url, json=request_data.model_dump(exclude_none=True))
            response.raise_for_status()
            
            if stream:
                # Parse streaming response
                results = []
                for line in response.iter_lines():
                    if line.strip():
                        results.append(json.loads(line))
                return results
            else:
                # Parse single response
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error generating chat completion: {e}")
            raise
    
    def generate_embeddings(
        self,
        model: str,
        input_text: Union[str, List[str]],
        truncate: Optional[bool] = None,
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text input.
        
        Args:
            model: The name of the model to use.
            input_text: Text or list of texts to generate embeddings for.
            truncate: Whether to truncate inputs to fit context length.
            options: Optional model parameters.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            A dictionary containing the embeddings.
        """
        url = f"{self.base_url}/api/embed"
        
        request_data = OllamaEmbedRequest(
            model=model,
            input=input_text,
            truncate=truncate,
            options=options,
            **kwargs
        )
        
        try:
            response = self.client.post(url, json=request_data.model_dump(exclude_none=True))
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def pull_model(self, model: str) -> Dict[str, Any]:
        """
        Pull a model from the Ollama library.
        
        Args:
            model: The name of the model to pull.
            
        Returns:
            A dictionary containing the result of the pull operation.
        """
        url = f"{self.base_url}/api/pull"
        
        request_data = {
            "model": model,
            "stream": False
        }
        
        try:
            response = self.client.post(url, json=request_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error pulling model: {e}")
            raise
    
    def is_model_available(self, model_name: str) -> bool:
        """
        Check if a model is available on the Ollama server.
        
        Args:
            model_name: The name of the model to check.
            
        Returns:
            True if the model is available, False otherwise.
        """
        try:
            models = self.list_models()
            for model in models.get("models", []):
                if model.get("name") == model_name:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    def preload_model(self, model: str) -> bool:
        """
        Preload a model into memory.
        
        Args:
            model: The name of the model to preload.
            
        Returns:
            True if successful, False otherwise.
        """
        url = f"{self.base_url}/api/generate"
        
        request_data = {
            "model": model,
            "prompt": ""  # Empty prompt just loads the model
        }
        
        try:
            response = self.client.post(url, json=request_data)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Error preloading model: {e}")
            return False
    
    def unload_model(self, model: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model: The name of the model to unload.
            
        Returns:
            True if successful, False otherwise.
        """
        url = f"{self.base_url}/api/generate"
        
        request_data = {
            "model": model,
            "prompt": "",
            "keep_alive": 0  # Setting keep_alive to 0 unloads the model
        }
        
        try:
            response = self.client.post(url, json=request_data)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Error unloading model: {e}")
            return False


# Factory function to create the appropriate client
def create_ollama_client(async_client: bool = False, base_url: str = "http://localhost:11434", timeout: int = 120):
    """
    Create an Ollama client.
    
    Args:
        async_client: Whether to create an async client.
        base_url: The base URL of the Ollama API server.
        timeout: Timeout in seconds for API requests.
        
    Returns:
        An instance of OllamaClient or SyncOllamaClient.
    """
    if async_client:
        return OllamaClient(base_url=base_url, timeout=timeout)
    else:
        return SyncOllamaClient(base_url=base_url, timeout=timeout)