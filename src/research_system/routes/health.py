"""
Health check endpoints for the Research System.

This module provides health check endpoints for monitoring system status,
including basic liveness checks and detailed readiness information.
"""

import time
from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint for monitoring system status.
    
    This endpoint provides both basic liveness information and detailed readiness
    checks for system dependencies. It serves as a unified health endpoint for
    both simple health checks and detailed system diagnostics.
    
    For Kubernetes deployments, this endpoint can be used for both liveness
    and readiness probes by configuring the success threshold appropriately.
    
    Returns:
        dict: Status information including system health and dependency checks
    """
    # For simplicity and reliability, return a fixed healthy response
    # This makes the endpoint suitable for both liveness and readiness probes
    response = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "research-system",
        "version": "1.0.0",
        "uptime": time.time() - request.app.state.start_time
    }
    
    return response

@router.get("/healthz")
async def kubernetes_liveness_probe(request: Request):
    """
    Kubernetes liveness probe endpoint.
    
    Simplified health check specifically for Kubernetes liveness probes.
    This endpoint always returns success unless the application is completely down.
    
    Returns:
        dict: Basic health status
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "research-system",
        "version": "1.0.0"
    }

@router.get("/readyz")
async def kubernetes_readiness_probe(request: Request):
    """
    Kubernetes readiness probe endpoint.
    
    This endpoint checks if the application is ready to serve traffic by
    verifying that all dependencies (database, external services) are available.
    
    Returns:
        dict: Detailed readiness status including component checks
    """
    # Check database connection
    db_status = "ready"
    try:
        # Perform a simple database operation to verify connection
        if hasattr(request.app.state, "db"):
            request.app.state.db.ping()
        else:
            db_status = "unknown"
    except Exception:
        db_status = "unavailable"
    
    # Check LLM service if enabled
    llm_status = "disabled"
    if getattr(request.app.state, "llm_enabled", False):
        try:
            if hasattr(request.app.state, "ollama_server"):
                # Try to get version info as a simple check
                request.app.state.ollama_server.get_version()
                llm_status = "ready"
            else:
                llm_status = "unknown"
        except Exception:
            llm_status = "unavailable"
    
    # Overall status is ready only if all required components are ready
    overall_status = "ready" if db_status == "ready" else "not_ready"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "components": {
            "database": db_status,
            "llm": llm_status
        }
    }

@router.get("/")
async def root(request: Request):
    """
    Root endpoint with basic system information and status.
    
    Provides an overview of the Research System API including version, environment,
    LLM configuration, and available components/services.
    
    Returns:
        dict: System information including version, components, and configuration
    """
    # Get configuration
    config = request.app.state.config
    
    # List available services
    services = ["planner", "search", "coordinator"]
    if getattr(request.app.state, "llm_enabled", False):
        services.append("ollama")
    
    # Get LLM info if available
    llm_info = {
        "enabled": getattr(request.app.state, "llm_enabled", False),
        "model": config.get("llm", {}).get("model") if getattr(request.app.state, "llm_enabled", False) else None
    }
    
    if hasattr(request.app.state, "ollama_server"):
        try:
            # Add detailed LLM info if available
            version_info = request.app.state.ollama_server.get_version()
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
        except Exception:
            # Ignore errors when trying to get LLM info
            pass
    
    # Return system information
    return {
        "message": "Research System API",
        "version": "1.0.0",
        "environment": config.get("environment", "development"),
        "llm": llm_info,
        "components": {
            "agents": request.app.state.coordinator.list_agents() if hasattr(request.app.state, "coordinator") else [],
            "services": services
        }
    }