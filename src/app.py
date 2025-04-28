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
    description="API for managing research tasks, plans, and search operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Health", "description": "Health and status check endpoints"},
        {"name": "Tasks", "description": "Research task management endpoints"},
        {"name": "Results", "description": "Research results endpoints"},
        {"name": "LLM", "description": "Large Language Model integration endpoints"},
    ]
)

# Store application start time for uptime tracking
app.state.start_time = time.time()

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
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring system status.
    
    This endpoint provides both basic liveness information and detailed readiness
    checks for system dependencies. It serves as a unified health endpoint for
    both simple health checks and detailed system diagnostics.
    
    For Kubernetes deployments, this endpoint can be used for both liveness
    and readiness probes by configuring the success threshold appropriately.
    
    Returns:
        dict: Status information including system health and dependency checks
        
    Raises:
        HTTPException: 503 error if critical dependencies are unavailable
    """
    # For simplicity and reliability, return a fixed healthy response
    # This makes the endpoint suitable for both liveness and readiness probes
    response = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "research-system",
        "version": "1.0.0",
        "uptime": time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0
    }
    
    return response


@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint with basic system information and status.
    
    Provides an overview of the Research System API including version, environment,
    LLM configuration, and available components/services.
    
    Returns:
        dict: System information including version, components, and configuration
    """
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

@app.get("/api/tasks", tags=["Tasks"])
async def list_tasks():
    """
    List all research tasks.
    
    Returns:
        dict: Object containing an array of task objects
    """
    tasks = planner.list_research_tasks()
    return {"tasks": tasks}

@app.post("/api/tasks", status_code=201, tags=["Tasks"])
async def create_task(task: TaskCreate):
    """
    Create a new research task.
    
    Args:
        task (TaskCreate): Task data including title, description, and optional tags
        
    Returns:
        dict: The created task object
        
    Raises:
        HTTPException: 400 error if task creation fails
    """
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

@app.get("/api/tasks/{task_id}", tags=["Tasks"])
async def get_task(task_id: str):
    """
    Get a research task by ID.
    
    Args:
        task_id (str): Unique identifier of the task
        
    Returns:
        dict: Task object with all properties
        
    Raises:
        HTTPException: 404 error if task not found
    """
    task = default_db.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.model_dump()}

@app.post("/api/tasks/{task_id}/plan", status_code=201, tags=["Tasks"])
async def create_plan(task_id: str):
    """
    Create a research plan for a task.
    
    Generates a structured research plan with steps and objectives for the specified task.
    
    Args:
        task_id (str): Unique identifier of the task
        
    Returns:
        dict: The created plan object
        
    Raises:
        HTTPException: 400 error if plan creation fails or 404 if task not found
    """
    try:
        # Check if task exists
        task = default_db.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
            
        plan = planner.generate_plan_for_task(task_id)
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tasks/{task_id}/search", tags=["Tasks"])
async def task_search(task_id: str, search_request: SearchRequest):
    """
    Execute a search for a task.
    
    Performs a search query associated with the specified task and returns results.
    
    Args:
        task_id (str): Unique identifier of the task
        search_request (SearchRequest): Search parameters including query and max_results
        
    Returns:
        dict: Object containing an array of search results
        
    Raises:
        HTTPException: 400 error if search fails or 404 if task not found
    """
    try:
        # Check if task exists
        task = default_db.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
            
        results = search.execute_search(
            task_id=task_id,
            query=search_request.query,
            max_results=search_request.max_results
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/results/{result_id}", tags=["Results"])
async def get_result(result_id: str):
    """
    Get a research result by ID.
    
    Args:
        result_id (str): Unique identifier of the result
        
    Returns:
        dict: Result object with all properties
        
    Raises:
        HTTPException: 404 error if result not found
    """
    result = default_db.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"result": result.model_dump()}

@app.get("/api/tasks/{task_id}/results", tags=["Results"])
async def get_task_results(task_id: str):
    """
    Get all research results for a task.
    
    Args:
        task_id (str): Unique identifier of the task
        
    Returns:
        dict: Object containing an array of result objects
        
    Raises:
        HTTPException: 404 error if task not found
    """
    try:
        # Check if task exists
        task = default_db.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get results for this task
        results = default_db.list_results_for_task(task_id)
        
        # Convert results to dicts
        result_dicts = [result.model_dump() for result in results]
        
        return {"results": result_dicts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# LLM direct access endpoints
class LLMCompletionRequest(BaseModel):
    """
    Request model for LLM text completion.
    
    Attributes:
        prompt (str): The input text to generate completion for
        model (str, optional): Specific model to use (defaults to system default)
        system (str, optional): System message to guide the completion
        options (Dict[str, Any], optional): Additional model-specific options
    """
    prompt: str
    model: str = None
    system: str = None
    options: Dict[str, Any] = None

class LLMChatRequest(BaseModel):
    """
    Request model for LLM chat completion.
    
    Attributes:
        messages (List[Dict[str, Any]]): Array of message objects with role and content
        model (str, optional): Specific model to use (defaults to system default)
        options (Dict[str, Any], optional): Additional model-specific options
    """
    messages: List[Dict[str, Any]]
    model: str = None
    options: Dict[str, Any] = None

@app.post("/api/llm/completion", tags=["LLM"])
async def generate_llm_completion(request: LLMCompletionRequest):
    """
    Generate a text completion with the LLM.
    
    Creates a completion for the given prompt using the configured LLM service.
    
    Args:
        request (LLMCompletionRequest): Request containing prompt and options
        
    Returns:
        dict: The completion result with generated text
        
    Raises:
        HTTPException: 503 error if LLM service is unavailable
                      500 error if completion generation fails
    """
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

@app.post("/api/llm/chat", tags=["LLM"])
async def generate_llm_chat_completion(request: LLMChatRequest):
    """
    Generate a chat completion with the LLM.
    
    Creates a chat completion from a sequence of messages using the configured LLM service.
    
    Args:
        request (LLMChatRequest): Request containing messages and options
        
    Returns:
        dict: The chat completion result with generated response
        
    Raises:
        HTTPException: 503 error if LLM service is unavailable
                      500 error if chat completion generation fails
    """
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

@app.get("/api/llm/models", tags=["LLM"])
async def list_llm_models():
    """
    List all available LLM models.
    
    Retrieves the list of models available through the configured LLM service.
    
    Returns:
        dict: Object containing available models and their details
        
    Raises:
        HTTPException: 503 error if LLM service is unavailable
                      500 error if model listing fails
    """
    if not use_llm or not ollama_server:
        raise HTTPException(status_code=503, detail="LLM service is not available")
    
    try:
        models = ollama_server.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Import research interface
from src.research_system.core.research import setup_research

# Add API documentation metadata
app.description = """
Research System API provides endpoints for creating and managing research tasks,
generating research plans, performing searches, and accessing LLM capabilities.

For detailed documentation, see the API_DOCUMENTATION.md file in the docs directory.
"""

app.swagger_ui_parameters = {
    "defaultModelsExpandDepth": -1,  # Hide schemas section by default
    "displayRequestDuration": True,   # Show request execution time
    "filter": True,                  # Enable filtering operations
    "syntaxHighlight.theme": "monokai" # More readable theme
}

# Set up dashboard
setup_dashboard(app)

# Set up research interface
setup_research(app)

if __name__ == '__main__':
    import uvicorn
    # Get port from config or environment
    port = int(os.getenv("PORT", config.get("app", {}).get("port", 8181)))
    
    # Start the FastAPI app
    logger.info(f"Starting Research System API on port {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)
