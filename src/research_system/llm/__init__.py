"""
LLM integration package for the Research System.

This package provides integrations with various LLM providers,
including local models via Ollama.
"""

from .ollama_client import OllamaClient, SyncOllamaClient, create_ollama_client

__all__ = ["OllamaClient", "SyncOllamaClient", "create_ollama_client"]