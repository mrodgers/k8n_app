"""
Main application entry point for the Research System.

This module integrates the FastAPI app with the Research System core components,
providing both HTTP endpoints and a foundation for the FastMCP servers.
"""

import logging
import os
import time
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yaml

# Import research system components
from src.research_system.core.server import FastMCPServer, Context
from src.research_system.core.coordinator import Coordinator, default_coordinator
from src.research_system.core.dashboard import setup_dashboard
from src.research_system.agents.planner import PlannerAgent, default_planner
from src.research_system.agents.search import SearchAgent, default_search
from src.research_system.models.db import Database, default_db
from src.research_system.models.db_config import load_config as load_db_config
from src.research_system.llm import create_ollama_client, OllamaServer

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
            "app": {"port": 8181, "max_workers": 4},
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

# Create static files directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

# Mount static files directory
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Set up core components
main_server = FastMCPServer("Research System API", config)
coordinator = default_coordinator

# Configure LLM settings
llm_config = config.get("llm", {})
use_llm = llm_config.get("enabled", True)
ollama_model = llm_config.get("model") or os.environ.get("OLLAMA_MODEL", "gemma3:1b")
ollama_url = llm_config.get("url") or os.environ.get("OLLAMA_URL")

# Initialize LLM services
llm_client = None
ollama_server = None
if use_llm:
    try:
        # Try to initialize LLM client
        llm_client = create_ollama_client(
            async_client=False,
            base_url=ollama_url,
            timeout=llm_config.get("timeout", 120)
        )
        
        # Initialize the Ollama FastMCP server
        ollama_server = OllamaServer(
            name="ollama",
            server=main_server,  # Register tools with the main server
            config={
                "model": ollama_model,
                "url": ollama_url,
                "timeout": llm_config.get("timeout", 120)
            }
        )
        
        logger.info(f"Initialized LLM services using model: {ollama_model}")
        
        # Register Ollama as a FastMCP agent with the coordinator
        coordinator.register_agent({
            "name": "ollama",
            "server_url": "http://localhost:8080",
            "description": "LLM agent for generating text and embeddings",
            "tools": [
                "generate_completion", 
                "generate_chat_completion", 
                "generate_embeddings",
                "extract_content",
                "assess_relevance",
                "generate_plan"
            ]
        })
        logger.info("Registered Ollama as a FastMCP agent with the coordinator")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM services: {e}")
        logger.warning("Research System will operate without LLM capabilities")
        use_llm = False

# Create agent configurations
planner_config = {
    "use_llm": use_llm,
    "ollama_model": ollama_model,
    "ollama_url": ollama_url
}

search_config = {
    "use_llm": use_llm,
    "ollama_model": ollama_model,
    "ollama_url": ollama_url,
    "brave_search": config.get("brave_search", {})
}

# Initialize agents with LLM support
planner = PlannerAgent(config=planner_config)
search = SearchAgent(config=search_config)

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
    by checking connectivity to dependent services like the database and LLM.
    """
    services_status = {
        "api": True,
        "database": False,
        "llm": False if use_llm else None  # None means not required
    }
    
    # Check database connectivity
    try:
        # Use a simple operation that requires database access
        default_db.list_tasks(status=None, assigned_to=None, tag=None)
        services_status["database"] = True
    except Exception as e:
        logger.error(f"Database readiness check failed: {str(e)}")
        services_status["database"] = False
    
    # Check LLM connectivity if enabled
    if use_llm and ollama_server:
        try:
            # Test Ollama server with a version check (lightweight operation)
            version_info = ollama_server.get_version()
            if version_info and "version" in version_info:
                services_status["llm"] = True
                logger.debug(f"LLM readiness check successful. Ollama version: {version_info['version']}")
            else:
                logger.error("LLM readiness check failed: Invalid version response")
                services_status["llm"] = False
        except Exception as e:
            logger.error(f"LLM readiness check failed: {str(e)}")
            services_status["llm"] = False
    
    # Filter out None values (services not required)
    required_services = {k: v for k, v in services_status.items() if v is not None}
    
    # Determine overall status
    all_ready = all(required_services.values())
    
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
    services = ["planner", "search", "coordinator"]
    if ollama_server:
        services.append("ollama")
    
    # Get LLM info if available
    llm_info = {
        "enabled": use_llm,
        "model": ollama_model if use_llm else None
    }
    
    if ollama_server:
        try:
            # Add detailed LLM info if available
            version_info = ollama_server.get_version()
            llm_info["version"] = version_info.get("version")
            llm_info["server_type"] = "FastMCP"
            llm_info["available_tools"] = [
                "generate_completion", 
                "generate_chat_completion",
                "generate_embeddings",
                "extract_content",
                "assess_relevance",
                "generate_plan"
            ]
        except Exception as e:
            logger.error(f"Error getting LLM version info: {e}")
    
    return {
        "message": "Research System API",
        "version": "1.0.0",
        "environment": config.get("environment", "development"),
        "llm": llm_info,
        "components": {
            "agents": coordinator.list_agents(),
            "services": services
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

# LLM direct access endpoints
class LLMCompletionRequest(BaseModel):
    prompt: str
    model: str = None
    system: str = None
    options: Dict[str, Any] = None

class LLMChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: str = None
    options: Dict[str, Any] = None

@app.post("/api/llm/completion")
async def generate_llm_completion(request: LLMCompletionRequest):
    """Generate a completion with the LLM."""
    if not use_llm or not ollama_server:
        raise HTTPException(status_code=503, detail="LLM service is not available")
    
    try:
        result = ollama_server.generate_completion(
            prompt=request.prompt,
            model=request.model,
            system=request.system,
            options=request.options
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/chat")
async def generate_llm_chat_completion(request: LLMChatRequest):
    """Generate a chat completion with the LLM."""
    if not use_llm or not ollama_server:
        raise HTTPException(status_code=503, detail="LLM service is not available")
    
    try:
        result = ollama_server.generate_chat_completion(
            messages=request.messages,
            model=request.model,
            options=request.options
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/models")
async def list_llm_models():
    """List available LLM models."""
    if not use_llm or not ollama_server:
        raise HTTPException(status_code=503, detail="LLM service is not available")
    
    try:
        models = ollama_server.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Set up dashboard
setup_dashboard(app)

if __name__ == '__main__':
    import uvicorn
    # Get port from config or environment
    port = int(os.getenv("PORT", config.get("app", {}).get("port", 8181)))
    
    # Start the FastAPI app
    logger.info(f"Starting Research System API on port {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)
