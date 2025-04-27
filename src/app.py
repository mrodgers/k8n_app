"""
Main application entry point for the Research System.

This module integrates the FastAPI app with the Research System core components,
providing both HTTP endpoints and a foundation for the FastMCP servers.
"""

import logging
import os
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yaml

# Import research system components
from src.research_system.core.server import FastMCPServer, Context
from src.research_system.core.coordinator import Coordinator, default_coordinator
from src.research_system.agents.planner import PlannerAgent, default_planner
from src.research_system.agents.search import SearchAgent, default_search
from src.research_system.models.db import Database, default_db
from src.research_system.models.db_config import load_config as load_db_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load configuration from config.yaml file."""
    try:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        # Return default configuration
        return {
            "app": {"port": 8080, "max_workers": 4},
            "logging": {"level": "INFO"},
            "environment": "development"
        }

config = load_config()

# Initialize FastAPI app
app = FastAPI(
    title="Research System API",
    description="API for the Research System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up core components
main_server = FastMCPServer("Research System API", config)
coordinator = default_coordinator
planner = default_planner
search = default_search

# Register agents with the coordinator
coordinator.register_agent({
    "name": planner.name,
    "server_url": "http://localhost:8080",
    "description": "Research planning agent",
    "tools": ["create_research_task", "create_research_plan", "generate_plan_for_task"]
})

coordinator.register_agent({
    "name": search.name,
    "server_url": "http://localhost:8080",
    "description": "Search agent",
    "tools": ["execute_search", "extract_content_from_url", "filter_results"]
})

# Pydantic models for request/response
class TaskCreate(BaseModel):
    title: str
    description: str
    tags: list[str] = []
    assigned_to: str | None = None

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10

# FastAPI routes
@app.get("/healthz")
async def liveness_probe():
    """
    Liveness probe endpoint for Kubernetes.
    
    This endpoint checks if the application is running and can respond to requests.
    It does not check if dependent services are available.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "research-system"
    }

@app.get("/readyz")
async def readiness_probe():
    """
    Readiness probe endpoint for Kubernetes.
    
    This endpoint verifies that the application is ready to handle requests
    by checking connectivity to dependent services like the database.
    """
    services_status = {
        "api": True,
        "database": False,
    }
    
    # Check database connectivity
    try:
        # Use a simple operation that requires database access
        default_db.list_tasks(status=None, assigned_to=None, tag=None)
        services_status["database"] = True
    except Exception as e:
        logger.error(f"Database readiness check failed: {str(e)}")
        services_status["database"] = False
    
    # Determine overall status
    all_ready = all(services_status.values())
    
    status_code = 200 if all_ready else 503
    response = {
        "status": "ready" if all_ready else "not_ready",
        "timestamp": time.time(),
        "service": "research-system",
        "dependencies": services_status
    }
    
    # FastAPI will automatically set the status code
    if not all_ready:
        raise HTTPException(status_code=status_code, detail=response)
    
    return response

@app.get("/health")
async def health_check():
    """Legacy health check endpoint for backward compatibility."""
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint with basic system info."""
    return {
        "message": "Research System API",
        "version": "1.0.0",
        "environment": config.get("environment", "development"),
        "components": {
            "agents": coordinator.list_agents(),
            "services": ["planner", "search", "coordinator"]
        }
    }

@app.get("/api/tasks")
async def list_tasks():
    """List all research tasks."""
    tasks = planner.list_research_tasks()
    return {"tasks": tasks}

@app.post("/api/tasks", status_code=201)
async def create_task(task: TaskCreate):
    """Create a new research task."""
    try:
        created_task = planner.create_research_task(
            title=task.title,
            description=task.description,
            tags=task.tags,
            assigned_to=task.assigned_to
        )
        return {"task": created_task}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a research task by ID."""
    task = default_db.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.model_dump()}

@app.post("/api/tasks/{task_id}/plan", status_code=201)
async def create_plan(task_id: str):
    """Create a research plan for a task."""
    try:
        plan = planner.generate_plan_for_task(task_id)
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tasks/{task_id}/search")
async def task_search(task_id: str, search_request: SearchRequest):
    """Execute a search for a task."""
    try:
        results = search.execute_search(
            task_id=task_id,
            query=search_request.query,
            max_results=search_request.max_results
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/results/{result_id}")
async def get_result(result_id: str):
    """Get a research result by ID."""
    result = default_db.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"result": result.to_dict()}

if __name__ == '__main__':
    import uvicorn
    # Get port from config or environment
    port = int(os.getenv("PORT", config.get("app", {}).get("port", 8080)))
    
    # Start the FastAPI app
    logger.info(f"Starting Research System API on port {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)
