#!/usr/bin/env python
"""
Simple test script for OllamaServer.

This script directly instantiates and tests the OllamaServer class
without relying on the full application.
"""

import os
import sys
import time
import logging
from fastapi import FastAPI
import uvicorn

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
            "timeout": 30
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
        
        # Run a simple test with generate_plan
        try:
            logger.info("Testing generate_plan")
            plan = ollama_server.generate_plan(
                title="Test Plan",
                description="This is a test plan",
                tags=["test"]
            )
            logger.info("Generated plan with %d steps", len(plan.get("steps", [])))
            for i, step in enumerate(plan.get("steps", [])):
                logger.info("Step %d: %s - %s", i+1, step.get("name"), step.get("type"))
        except Exception as e:
            logger.error("Error testing generate_plan: %s", e)
        
        # Start the FastAPI server
        app = server.app
        
        # Add a test endpoint
        @app.get("/test")
        async def test_endpoint():
            return {"message": "Test endpoint is working!"}
        
        # Run the server
        logger.info("Starting FastAPI server at http://localhost:8181")
        uvicorn.run(app, host="0.0.0.0", port=8181)
        
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