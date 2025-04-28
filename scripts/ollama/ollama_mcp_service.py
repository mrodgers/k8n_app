#!/usr/bin/env python
"""
Ollama MCP Service.

A simple FastAPI microservice that exposes the Ollama LLM as a FastMCP server.
"""

import os
import sys
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import FastMCP components
from src.research_system.core.server import FastMCPServer
from src.research_system.llm.ollama_server import OllamaServer

def create_app():
    """Create and configure the FastAPI application."""
    # Create the FastMCP server
    fastmcp_server = FastMCPServer("Ollama MCP Server")
    
    # Configure Ollama
    ollama_config = {
        "model": os.environ.get("OLLAMA_MODEL", "gemma3:1b"),
        "url": os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        "timeout": int(os.environ.get("OLLAMA_TIMEOUT", "30"))
    }
    
    # Create the OllamaServer
    ollama_server = OllamaServer(
        name="ollama",
        server=fastmcp_server,
        config=ollama_config
    )
    
    # Log registered tools
    logger.info("Registered FastMCP tools: %s", ", ".join(fastmcp_server.tools.keys()))
    
    # Create a FastAPI app
    app = fastmcp_server.app
    
    # Add some custom endpoints
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "Ollama MCP Server",
            "version": "1.0.0",
            "model": ollama_config["model"],
            "tools": list(fastmcp_server.tools.keys())
        }
    
    @app.get("/models")
    async def list_models():
        """List available models."""
        try:
            models = ollama_server.list_models()
            return models
        except Exception as e:
            logger.error("Error listing models: %s", e)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/generate")
    async def generate(request: Request):
        """Generate text from prompt."""
        try:
            data = await request.json()
            prompt = data.get("prompt")
            model = data.get("model", ollama_config["model"])
            
            if not prompt:
                raise HTTPException(status_code=400, detail="Prompt is required")
            
            result = ollama_server.generate_completion(
                prompt=prompt,
                model=model
            )
            
            return result
        except Exception as e:
            logger.error("Error generating text: %s", e)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/chat")
    async def chat(request: Request):
        """Generate chat completion."""
        try:
            data = await request.json()
            messages = data.get("messages")
            model = data.get("model", ollama_config["model"])
            
            if not messages:
                raise HTTPException(status_code=400, detail="Messages are required")
            
            result = ollama_server.generate_chat_completion(
                messages=messages,
                model=model
            )
            
            return result
        except Exception as e:
            logger.error("Error generating chat completion: %s", e)
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

def main():
    """Run the Ollama MCP server."""
    try:
        # Get port from environment or use default
        port = int(os.environ.get("PORT", "8181"))
        
        # Create the app
        app = create_app()
        
        # Run the server
        logger.info("Starting Ollama MCP Server on port %s", port)
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error("Error starting Ollama MCP Server: %s", e)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())