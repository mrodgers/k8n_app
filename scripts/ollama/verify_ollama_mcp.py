#!/usr/bin/env python
"""
Verification script for Ollama MCP implementation.

This script checks that the Ollama server can be created, initialized,
and that the client works correctly.
"""

import os
import sys
import json
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run a verification of the Ollama MCP implementation."""
    # Import local modules
    try:
        from src.research_system.core.server import FastMCPServer
        from src.research_system.llm.ollama_server import OllamaServer
    except ImportError:
        # Try adding the project root to sys.path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        try:
            from src.research_system.core.server import FastMCPServer
            from src.research_system.llm.ollama_server import OllamaServer
        except ImportError as e:
            logger.error("Could not import required modules: %s", e)
            return 1
    
    # Create a FastMCP server
    server = FastMCPServer("Test Server")
    logger.info("Created FastMCP server")
    
    # Create an Ollama server
    ollama_config = {
        "model": os.environ.get("OLLAMA_MODEL", "gemma3:1b"),
        "url": os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        "timeout": int(os.environ.get("OLLAMA_TIMEOUT", "60"))
    }
    
    try:
        logger.info("Creating Ollama server with config: %s", json.dumps(ollama_config))
        ollama_server = OllamaServer(
            name="test-ollama",
            server=server,
            config=ollama_config
        )
        logger.info("✅ Ollama server created successfully")
    except Exception as e:
        logger.error("❌ Failed to create Ollama server: %s", e)
        return 1
    
    # Check if tools were registered
    tool_count = len(server.tools)
    logger.info("Server has %d registered tools", tool_count)
    if tool_count > 0:
        logger.info("✅ Tools registered successfully")
        logger.info("Registered tools: %s", ", ".join(server.tools.keys()))
    else:
        logger.error("❌ No tools registered")
        return 1
    
    # Create a FastAPI test client
    client = TestClient(server.app)
    
    # Test the tools endpoint
    response = client.get("/tools")
    if response.status_code == 200:
        logger.info("✅ Tools endpoint works")
        logger.info("Available tools: %s", response.json().get("tools", []))
    else:
        logger.error("❌ Tools endpoint failed: %s", response.text)
        return 1
    
    # Try calling a simple tool like get_version
    try:
        response = client.post("/tools/get_version")
        if response.status_code == 200:
            logger.info("✅ get_version tool works")
            logger.info("Version info: %s", json.dumps(response.json()))
        else:
            logger.error("❌ get_version tool failed: %s", response.text)
    except Exception as e:
        logger.error("❌ Error calling get_version: %s", e)
    
    logger.info("Verification completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())