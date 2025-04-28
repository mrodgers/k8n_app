"""
Dashboard implementation for the Research System.

This module provides a simple web-based UI for monitoring the status of agents,
services, and overall system health. It is designed for debugging and development.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import json
import psutil

# Import research system components
from src.research_system.core.coordinator import Coordinator, default_coordinator
from src.research_system.models.db import default_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create templates directory if it doesn't exist
templates_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates')
os.makedirs(templates_dir, exist_ok=True)

# Initialize templates
templates = Jinja2Templates(directory=templates_dir)

# Create router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# System status cache
# This prevents excessive DB queries and system calls
status_cache = {
    "last_update": 0,
    "cache_timeout": 5,  # seconds
    "system_status": {},
    "agents_status": {},
    "db_status": {},
    "tasks_count": 0,
    "results_count": 0,
    "recent_tasks": [],
    "recent_results": []
}


def get_system_status() -> Dict:
    """Get system status information including CPU, memory, and disk usage."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": f"{memory.used / (1024 * 1024):.1f} MB",
            "memory_total": f"{memory.total / (1024 * 1024):.1f} MB",
            "disk_percent": disk.percent,
            "disk_used": f"{disk.used / (1024 * 1024 * 1024):.1f} GB",
            "disk_total": f"{disk.total / (1024 * 1024 * 1024):.1f} GB",
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "error": str(e),
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_used": "N/A",
            "memory_total": "N/A",
            "disk_percent": 0,
            "disk_used": "N/A",
            "disk_total": "N/A",
        }


def get_agent_status(coordinator: Coordinator) -> Dict:
    """Get status information for all registered agents."""
    agents = {}
    
    for agent_name in coordinator.list_agents():
        try:
            agent = coordinator.get_agent(agent_name)
            # Basic info for now - we'll expand this
            agents[agent_name] = {
                "name": agent_name,
                "server_url": agent.server_url,
                "description": agent.description,
                "tools": agent.tools,
                "status": "unknown"  # Will be updated with health check
            }
            
            # Try to ping the agent to check status
            try:
                # Simple ping - this is just a placeholder; in a real implementation
                # you would use the actual FastMCP protocol to check health
                if "localhost" in agent.server_url or "127.0.0.1" in agent.server_url:
                    agents[agent_name]["status"] = "active"
                else:
                    # For non-local services, we need a more robust check
                    # This is a placeholder for now
                    agents[agent_name]["status"] = "unknown"
            except Exception as ping_error:
                logger.warning(f"Error pinging agent {agent_name}: {ping_error}")
                agents[agent_name]["status"] = "unreachable"
                agents[agent_name]["error"] = str(ping_error)
                
        except Exception as e:
            logger.error(f"Error getting status for agent {agent_name}: {e}")
            agents[agent_name] = {
                "name": agent_name,
                "status": "error",
                "error": str(e)
            }
    
    return agents


def get_db_status() -> Dict:
    """Get database status and statistics."""
    try:
        # Check if we can connect to the database
        # This is a simple check for now
        try:
            # Query some basic data to check connection
            tasks = default_db.list_tasks()
            results = []
            
            # Only fetch results if we have tasks (to avoid unnecessary overhead)
            if tasks:
                # Get results for the first task only
                results = default_db.list_results_for_task(tasks[0].id)
            
            # Get backend type
            if hasattr(default_db.db, 'db_path'):
                db_type = "TinyDB"
                db_location = default_db.db.db_path
            else:
                db_type = "PostgreSQL"
                # Extract hostname from connection string for security
                conn_str = default_db.db.connection_string
                if '@' in conn_str:
                    db_location = conn_str.split('@')[-1].split('/')[0]
                else:
                    db_location = "Unknown"
            
            return {
                "status": "connected",
                "type": db_type,
                "location": db_location,
                "tasks_count": len(tasks),
                "recent_tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.created_at)),
                    } 
                    for task in tasks[:5]  # Show only the 5 most recent tasks
                ],
                "results_count": len(results),
                "recent_results": [
                    {
                        "id": result.id,
                        "task_id": result.task_id,
                        "format": result.format,
                        "status": result.status,
                        "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.created_at)),
                    }
                    for result in results[:5]  # Show only the 5 most recent results
                ]
            }
        except Exception as db_error:
            logger.error(f"Database connection error: {db_error}")
            return {
                "status": "error",
                "error": str(db_error),
                "tasks_count": 0,
                "results_count": 0,
                "recent_tasks": [],
                "recent_results": []
            }
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return {
            "status": "unknown",
            "error": str(e),
            "tasks_count": 0,
            "results_count": 0,
            "recent_tasks": [],
            "recent_results": []
        }


def update_status_cache():
    """Update the status cache if it's expired."""
    current_time = time.time()
    
    # Return cached data if it's still fresh
    if current_time - status_cache["last_update"] < status_cache["cache_timeout"]:
        return
    
    # Otherwise, update the cache
    try:
        # Update system status
        status_cache["system_status"] = get_system_status()
        
        # Update agents status
        status_cache["agents_status"] = get_agent_status(default_coordinator)
        
        # Update database status
        db_status = get_db_status()
        status_cache["db_status"] = db_status
        status_cache["tasks_count"] = db_status.get("tasks_count", 0)
        status_cache["results_count"] = db_status.get("results_count", 0)
        status_cache["recent_tasks"] = db_status.get("recent_tasks", [])
        status_cache["recent_results"] = db_status.get("recent_results", [])
        
        # Update timestamp
        status_cache["last_update"] = current_time
        
    except Exception as e:
        logger.error(f"Error updating status cache: {e}")


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page showing system overview."""
    # Update cache
    update_status_cache()
    
    # Prepare template context
    context = {
        "request": request,
        "system_status": status_cache["system_status"],
        "agents": status_cache["agents_status"],
        "db_status": status_cache["db_status"],
        "tasks_count": status_cache["tasks_count"],
        "results_count": status_cache["results_count"],
        "recent_tasks": status_cache["recent_tasks"],
        "recent_results": status_cache["recent_results"],
        "last_update": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status_cache["last_update"])),
        "cache_timeout": status_cache["cache_timeout"]
    }
    
    # Render template
    return templates.TemplateResponse("dashboard.html", context)


@router.get("/api/status")
async def api_status():
    """API endpoint to get all status data as JSON."""
    update_status_cache()
    
    return {
        "system": status_cache["system_status"],
        "agents": status_cache["agents_status"],
        "database": status_cache["db_status"],
        "tasks_count": status_cache["tasks_count"],
        "results_count": status_cache["results_count"],
        "last_update": status_cache["last_update"],
        "cache_timeout": status_cache["cache_timeout"]
    }


@router.get("/api/agents")
async def api_agents():
    """API endpoint to get agent status data."""
    update_status_cache()
    return {"agents": status_cache["agents_status"]}


@router.get("/api/system")
async def api_system():
    """API endpoint to get system status data."""
    update_status_cache()
    return {"system": status_cache["system_status"]}


@router.get("/api/database")
async def api_database():
    """API endpoint to get database status data."""
    update_status_cache()
    return {"database": status_cache["db_status"]}


@router.get("/api/tasks")
async def api_tasks():
    """API endpoint to get recent tasks."""
    update_status_cache()
    return {"tasks": status_cache["recent_tasks"]}


@router.get("/api/results")
async def api_results():
    """API endpoint to get recent results."""
    update_status_cache()
    return {"results": status_cache["recent_results"]}


def setup_dashboard(app):
    """
    Set up the dashboard by including its router in the main app.
    
    Args:
        app: The FastAPI application instance.
    """
    app.include_router(router)
    logger.info("Dashboard setup complete")