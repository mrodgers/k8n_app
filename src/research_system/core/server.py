"""
FastMCP Server Implementation for the Research System.

This module contains the main server implementation for the research system,
including system-level tools and resources. It serves as the entry point
for the research system functionality.
"""

import logging
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import yaml
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import centralized configuration
from research_system.config import load_config

# Load configuration
config = load_config()

# FastMCP Server class
class FastMCPServer:
    """
    Main FastMCP server implementation for the research system.
    
    This server provides the core functionality for the research system,
    including system-level tools and resources.
    """
    
    def __init__(self, name: str, config: Dict = None):
        """
        Initialize the FastMCP server.
        
        Args:
            name: The name of the server.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.config = config or {}
        self.app = FastAPI(title=f"FastMCP Server - {name}")
        self.tools = {}
        self.resources = {}
        self.setup_middleware()
        self.setup_routes()
        logger.info(f"FastMCP Server '{name}' initialized")
    
    def setup_middleware(self):
        """Set up middleware for the FastAPI application."""
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # For development; restrict in production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Set up routes for the FastAPI application."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint that provides basic server information."""
            return {
                "server": self.name,
                "status": "running",
                "version": "1.0.0"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for the server."""
            return {"status": "healthy"}
        
        @self.app.get("/tools")
        async def list_tools():
            """List all available tools in the server."""
            return {"tools": list(self.tools.keys())}
        
        @self.app.get("/resources")
        async def list_resources():
            """List all available resources in the server."""
            return {"resources": list(self.resources.keys())}
    
    def register_tool(self, name: str, tool_func, description: str = ""):
        """
        Register a new tool with the server.
        
        Args:
            name: The name of the tool.
            tool_func: The function that implements the tool.
            description: Optional description of the tool.
        """
        self.tools[name] = {
            "function": tool_func,
            "description": description
        }
        
        # Create a FastAPI endpoint for the tool
        @self.app.post(f"/tools/{name}")
        async def tool_endpoint(request: Request):
            try:
                # Parse request body
                body = await request.json()
                # Call the tool function
                result = self.tools[name]["function"](**body)
                return {"result": result}
            except Exception as e:
                logger.error(f"Error executing tool '{name}': {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        logger.info(f"Registered tool: {name}")
    
    def register_resource(self, name: str, resource, description: str = ""):
        """
        Register a new resource with the server.
        
        Args:
            name: The name of the resource.
            resource: The resource to register.
            description: Optional description of the resource.
        """
        self.resources[name] = {
            "resource": resource,
            "description": description
        }
        
        # Create a FastAPI endpoint for the resource
        @self.app.get(f"/resources/{name}")
        async def resource_endpoint():
            try:
                return {"resource": self.resources[name]["resource"]}
            except Exception as e:
                logger.error(f"Error accessing resource '{name}': {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        logger.info(f"Registered resource: {name}")
    
    def run(self, host: str = "0.0.0.0", port: int = None):
        """
        Run the FastMCP server.
        
        Args:
            host: The host address to run the server on.
            port: The port to run the server on.
        """
        # Use config port if not specified
        if port is None:
            port = self.config.get("app", {}).get("port", 8080)
        
        import uvicorn
        logger.info(f"Starting FastMCP Server '{self.name}' on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

# Context class for progress reporting
class Context:
    """
    Context for tracking the state of operations and reporting progress.
    
    This class provides a way to track progress and share state between
    different components of the system.
    """
    
    def __init__(self, task_id: str = None):
        """
        Initialize a new context.
        
        Args:
            task_id: Optional task ID to associate with this context.
        """
        self.task_id = task_id or f"task_{int(time.time())}"
        self.state = {}
        self.progress = 0.0
        self.status = "initialized"
        self.logs = []
    
    def update_progress(self, progress: float, status: str = None):
        """
        Update the progress of the current operation.
        
        Args:
            progress: The new progress value (0.0 to 1.0).
            status: Optional status message.
        """
        self.progress = max(0.0, min(1.0, progress))  # Ensure progress is between 0 and 1
        if status:
            self.status = status
        self.log_info(f"Progress updated: {self.progress:.2f} - {self.status}")
    
    def log_info(self, message: str):
        """
        Log an informational message.
        
        Args:
            message: The message to log.
        """
        logger.info(f"[{self.task_id}] {message}")
        self.logs.append({"type": "info", "message": message, "timestamp": time.time()})
    
    def log_error(self, message: str):
        """
        Log an error message.
        
        Args:
            message: The message to log.
        """
        logger.error(f"[{self.task_id}] {message}")
        self.logs.append({"type": "error", "message": message, "timestamp": time.time()})
    
    def set_state(self, key: str, value: Any):
        """
        Set a state value.
        
        Args:
            key: The state key.
            value: The state value.
        """
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None):
        """
        Get a state value.
        
        Args:
            key: The state key.
            default: Default value to return if key is not found.
            
        Returns:
            The state value, or the default if not found.
        """
        return self.state.get(key, default)
    
    def to_dict(self):
        """
        Convert the context to a dictionary.
        
        Returns:
            A dictionary representation of the context.
        """
        return {
            "task_id": self.task_id,
            "progress": self.progress,
            "status": self.status,
            "state": self.state,
            "logs": self.logs
        }

# Create a default FastMCP server instance
default_server = FastMCPServer("Research System", config)
