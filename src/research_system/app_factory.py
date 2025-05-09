"""
FastAPI application factory for Research System.

This module contains the factory function to create and configure
the FastAPI application with all necessary components.
"""

import time
import os
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import configuration
from research_system.config import load_config

# Logger
logger = logging.getLogger(__name__)

def create_app(config_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        config_path: Path to configuration file (optional)
        config: Pre-loaded configuration dictionary (optional)
            If provided, config_path is ignored.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    # Load configuration if not provided
    if config is None:
        config = load_config(config_path)
    
    # Initialize FastAPI app
    app = FastAPI(
        title="Research System API",
        description="API for managing research tasks, plans, document verification, and search operations",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=[
            {"name": "Health", "description": "Health and status check endpoints"},
            {"name": "Tasks", "description": "Research task management endpoints"},
            {"name": "Results", "description": "Research results endpoints"},
            {"name": "Documents", "description": "Document management and verification endpoints"},
            {"name": "LLM", "description": "Large Language Model integration endpoints"},
        ]
    )
    
    # Store application start time for uptime tracking
    app.state.start_time = time.time()
    
    # Store configuration
    app.state.config = config
    
    # Register middleware
    register_middleware(app, config)
    
    # Register static files
    register_static_files(app)
    
    # Register routes
    register_routes(app)
    
    # Initialize components
    init_components(app, config)
    
    return app

def register_middleware(app: FastAPI, config: Dict[str, Any]) -> None:
    """
    Register middleware for the application.
    
    Args:
        app: FastAPI application
        config: Application configuration
    """
    # Get CORS settings from config
    cors_config = config.get("app", {}).get("cors", {})
    allow_origins = cors_config.get("allow_origins", ["*"])
    allow_methods = cors_config.get("allow_methods", ["*"])
    allow_headers = cors_config.get("allow_headers", ["*"])
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )
    
    # Add additional middleware here if needed

def register_static_files(app: FastAPI) -> None:
    """
    Register static files directory.
    
    Args:
        app: FastAPI application
    """
    # Create static files directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
    os.makedirs(static_dir, exist_ok=True)
    
    # Mount static files directory
    try:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")

def register_routes(app: FastAPI) -> None:
    """
    Register all route modules.
    
    Args:
        app: FastAPI application
    """
    # Import route modules here to avoid circular imports
    from research_system.routes.health import router as health_router
    from research_system.routes.tasks import router as tasks_router
    from research_system.routes.results import router as results_router
    from research_system.routes.llm import router as llm_router
    from research_system.routes.research import router as research_router

    # Include routers
    app.include_router(health_router)
    app.include_router(tasks_router)
    app.include_router(results_router)
    app.include_router(llm_router)
    app.include_router(research_router)

    # Document routes are conditionally loaded below to avoid import errors when vector support is disabled
    
    # Import and setup additional modules
    from research_system.core.research import setup_research
    from research_system.core.dashboard import setup_dashboard

    # Set up dashboard and research portal
    setup_dashboard(app)
    setup_research(app)

    # Dynamically include document routes only if vector search is enabled
    import os
    if os.getenv("MEMORY_VECTOR_SEARCH_ENABLED", "false").lower() != "false":
        from research_system.routes.documents import router as documents_router
        app.include_router(documents_router)

def init_components(app: FastAPI, config: Dict[str, Any]) -> None:
    """
    Initialize system components.
    
    Args:
        app: FastAPI application
        config: Application configuration
    """
    # Import main components
    from research_system.core.registry import default_registry, auto_register_providers
    from research_system.core.orchestrator import default_orchestrator
    from research_system.services.llm_service import default_llm_service
    from research_system.models.db import default_db

    # Register capabilities with the registry
    auto_register_providers(default_registry)

    # Store references to core components
    app.state.registry = default_registry
    app.state.orchestrator = default_orchestrator
    app.state.llm_service = default_llm_service
    app.state.db = default_db

    # Only include document system if vector search is enabled
    import os
    if os.getenv("MEMORY_VECTOR_SEARCH_ENABLED", "false").lower() != "false":
        from research_system.models.document import default_document_storage
        from research_system.agents.verification import default_verification_agent
        app.state.document_storage = default_document_storage
        app.state.verification_agent = default_verification_agent
    else:
        logger.info("Vector search disabled, document system not initialized")
    
    # For backward compatibility
    from research_system.agents.planner_refactored import default_planner
    from research_system.agents.search_refactored import default_search
    app.state.planner = default_planner
    app.state.search = default_search
    
    # Initialize LLM if enabled (sets up the LLM client using config)
    init_llm(app, config)

def init_llm(app: FastAPI, config: Dict[str, Any]) -> None:
    """
    Initialize LLM components if enabled.

    Args:
        app: FastAPI application
        config: Application configuration
    """
    # Get LLM configuration
    llm_config = config.get("llm", {})
    use_llm = llm_config.get("enabled", True)

    if not use_llm:
        logger.info("LLM integration is disabled by configuration")
        app.state.llm_enabled = False
        return

    try:
        # Import LLM components
        from research_system.llm import create_ollama_client, OllamaServer

        # Get LLM settings from config (which now includes env vars)
        ollama_model = llm_config.get("model", "gemma3:1b")
        ollama_url = llm_config.get("url")

        # Use default URL if not set in config
        if ollama_url is None:
            # Try to detect Kubernetes service or fallback to localhost
            if os.getenv("KUBERNETES_SERVICE_HOST"):
                # In Kubernetes, try to use the ollama service
                ollama_url = "http://ollama-service:11434"
                logger.info(f"Detected Kubernetes environment, using Ollama URL: {ollama_url}")
            else:
                ollama_url = "http://localhost:11434"
                logger.info(f"Using default Ollama URL: {ollama_url}")

        # Add protocol if missing
        if ollama_url and not (ollama_url.startswith("http://") or ollama_url.startswith("https://")):
            ollama_url = f"http://{ollama_url}"
            logger.info(f"Added protocol to Ollama URL: {ollama_url}")

        timeout = llm_config.get("timeout", 120)

        logger.info(f"Initializing Ollama client with URL: {ollama_url} and model: {ollama_model}")

        # Initialize LLM client
        llm_client = create_ollama_client(
            async_client=False,
            base_url=ollama_url,
            timeout=timeout
        )

        # Initialize Ollama server
        ollama_server = OllamaServer(
            name="ollama",
            config={
                "model": ollama_model,
                "url": ollama_url,
                "timeout": timeout
            }
        )

        # Store references
        app.state.llm_client = llm_client
        app.state.ollama_server = ollama_server
        app.state.llm_enabled = True

        # Register with coordinator
        coord_url = os.getenv("OLLAMA_SERVICE_URL", "http://localhost:8080")
        if not (coord_url.startswith("http://") or coord_url.startswith("https://")):
            coord_url = f"http://{coord_url}"

        app.state.coordinator.register_agent({
            "name": "ollama",
            "server_url": coord_url,
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
        
        logger.info(f"Initialized LLM services using model: {ollama_model}")
        
    except Exception as e:
        logger.warning(f"Failed to initialize LLM services: {e}")
        logger.warning("Research System will operate without LLM capabilities")
        app.state.llm_enabled = False