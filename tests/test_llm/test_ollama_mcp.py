#!/usr/bin/env python
"""
Test script for the Ollama server MCP implementation.

This script manually tests the functionality of the Ollama server
without relying on the test framework.
"""

import os
import sys
import logging

# Add project root to path
sys.path.append('/Users/matthewrodgers/Git/mcp_servers/k8s-python-app-new')
from src.research_system.core.server import FastMCPServer
from src.research_system.llm.ollama_server import OllamaServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run a simple test of the Ollama server functionality."""
    try:
        # Create a FastMCP server
        server = FastMCPServer("Test Server")
        logger.info("Created FastMCP server")
        
        # Create an Ollama server with the FastMCP server
        ollama_server = OllamaServer(
            name="ollama",
            server=server,
            config={
                "model": "gemma3:1b",
                "url": os.environ.get("OLLAMA_URL", "http://localhost:11434"),
                "timeout": 30
            }
        )
        logger.info("Created Ollama server with default model: %s", ollama_server.default_model)
        
        # Test version information
        try:
            version_info = ollama_server.get_version()
            logger.info("Ollama version: %s", version_info.get("version", "Unknown"))
            logger.info("✅ Version check passed")
        except Exception as e:
            logger.error("❌ Version check failed: %s", e)
        
        # Test listing models
        try:
            models = ollama_server.list_models()
            model_names = [model.get("name") for model in models.get("models", [])]
            logger.info("Available models: %s", ", ".join(model_names) if model_names else "None")
            logger.info("✅ Model listing passed")
        except Exception as e:
            logger.error("❌ Model listing failed: %s", e)
        
        # Test content extraction
        sample_text = """
        # FastMCP Protocol
        
        FastMCP is a protocol for agent communication that standardizes tool invocation
        and resource sharing between agents. It provides a simple API for registering
        and calling tools across different services.
        
        ## Key Features
        
        - Tool registration
        - Tool invocation
        - Resource sharing
        - Context tracking
        """
        
        try:
            result = ollama_server.extract_content(
                raw_text=sample_text,
                extraction_type="summary",
                max_length=100
            )
            logger.info("Extracted content: %s", result.get("content", ""))
            logger.info("✅ Content extraction passed")
        except Exception as e:
            logger.error("❌ Content extraction failed: %s", e)
        
        # Test generating a plan
        try:
            plan = ollama_server.generate_plan(
                title="Test Research Project",
                description="Research the impact of FastMCP protocol on agent communication",
                tags=["research", "agents", "communication"]
            )
            logger.info("Generated plan with %d steps", len(plan.get("steps", [])))
            logger.info("✅ Plan generation passed")
        except Exception as e:
            logger.error("❌ Plan generation failed: %s", e)
        
        logger.info("All tests completed")
        
    except Exception as e:
        logger.error("Error during testing: %s", e)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())