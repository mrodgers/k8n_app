#!/usr/bin/env python
"""
Simple test script for OllamaServer.

This script tests only the basic functionality of the OllamaServer class.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def main():
    """Run a simple test of the OllamaServer."""
    try:
        # Import modules
        from src.research_system.core.server import FastMCPServer
        from src.research_system.llm.ollama_server import OllamaServer

        # Create a FastMCP server
        logger.info("Creating FastMCP server")
        server = FastMCPServer("Test Server")
        
        # Configure Ollama server
        ollama_config = {
            "model": "gemma3:1b",
            "url": "http://localhost:11434",
            "timeout": 5  # Short timeout for testing
        }
        
        # Create the OllamaServer
        logger.info("Creating OllamaServer with config: %s", ollama_config)
        ollama_server = OllamaServer(
            name="ollama",
            server=server,
            config=ollama_config
        )
        
        # Print registered tools
        logger.info("Registered tools: %s", ", ".join(server.tools.keys()))
        
        # Test version info
        try:
            logger.info("Testing get_version")
            version_info = ollama_server.get_version()
            logger.info("Ollama version: %s", version_info.get("version", "Unknown"))
        except Exception as e:
            logger.error("Error testing get_version: %s", e)
        
        # Test listing models 
        try:
            logger.info("Testing list_models")
            models = ollama_server.list_models()
            model_names = [model.get("name") for model in models.get("models", [])]
            logger.info("Available models: %s", ", ".join(model_names))
        except Exception as e:
            logger.error("Error testing list_models: %s", e)
            
        logger.info("Tests completed")
        
    except ImportError as e:
        logger.error("ImportError: %s", e)
        logger.error("Make sure PYTHONPATH includes the project directory")
        return 1
    except Exception as e:
        logger.error("Error: %s", e)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())