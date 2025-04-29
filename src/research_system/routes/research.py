"""
Research API routes for the Research System.

This module implements the FastAPI routes for research tasks,
including task creation, plan generation, and research execution.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field

from research_system.core.orchestrator import Orchestrator, default_orchestrator
from research_system.core.registry import Registry, default_registry
from research_system.models.db import default_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define API models
class TaskCreate(BaseModel):
    """Model for creating a research task."""
    title: str
    description: str
    tags: Optional[List[str]] = None
    assigned_to: Optional[str] = None

class PlanCreate(BaseModel):
    """Model for creating a research plan."""
    task_id: str
    steps: Optional[List[Dict[str, Any]]] = None

class SearchRequest(BaseModel):
    """Model for executing a search."""
    task_id: str
    query: str
    max_results: Optional[int] = 10

class WorkflowRequest(BaseModel):
    """Model for executing a workflow."""
    title: Optional[str] = None
    description: Optional[str] = None
    query: str
    task_id: Optional[str] = None

# Create router
router = APIRouter(
    prefix="/api/research",
    tags=["Research"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get components
def get_components():
    """Get registry, orchestrator, and database components."""
    return {
        "registry": default_registry,
        "orchestrator": default_orchestrator,
        "db": default_db
    }

@router.post("/tasks", response_model=Dict[str, Any])
async def create_research_task(
    task: TaskCreate,
    components: Dict = Depends(get_components)
):
    """
    Create a new research task.
    
    Args:
        task: The task to create.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        The created task.
    """
    try:
        registry = components["registry"]
        result = registry.execute_capability(
            "create_research_task",
            **task.model_dump()
        )
        return {"task": result}
    except Exception as e:
        logger.error(f"Error creating research task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating research task: {str(e)}"
        )

@router.get("/tasks", response_model=Dict[str, Any])
async def list_research_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    tag: Optional[str] = None,
    components: Dict = Depends(get_components)
):
    """
    List research tasks.
    
    Args:
        status: Optional status filter.
        assigned_to: Optional assignment filter.
        tag: Optional tag filter.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        A list of tasks matching the filters.
    """
    try:
        registry = components["registry"]
        results = registry.execute_capability(
            "list_research_tasks",
            status=status,
            assigned_to=assigned_to,
            tag=tag
        )
        return {"tasks": results}
    except Exception as e:
        logger.error(f"Error listing research tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing research tasks: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_research_task(
    task_id: str,
    components: Dict = Depends(get_components)
):
    """
    Get a research task by ID.
    
    Args:
        task_id: The ID of the task to get.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        The task with the specified ID.
    """
    try:
        db = components["db"]
        task = db.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task not found: {task_id}"
            )
        return {"task": task.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting research task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting research task: {str(e)}"
        )

@router.post("/plans", response_model=Dict[str, Any])
async def create_research_plan(
    plan: PlanCreate,
    components: Dict = Depends(get_components)
):
    """
    Create a research plan.
    
    Args:
        plan: The plan to create.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        The created plan.
    """
    try:
        registry = components["registry"]
        result = registry.execute_capability(
            "create_research_plan",
            **plan.model_dump()
        )
        return {"plan": result}
    except Exception as e:
        logger.error(f"Error creating research plan: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating research plan: {str(e)}"
        )

@router.post("/plans/generate", response_model=Dict[str, Any])
async def generate_research_plan(
    task_id: str,
    components: Dict = Depends(get_components)
):
    """
    Generate a research plan for a task.
    
    Args:
        task_id: The ID of the task to generate a plan for.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        The generated plan.
    """
    try:
        registry = components["registry"]
        result = registry.execute_capability(
            "generate_plan_for_task",
            task_id=task_id
        )
        return {"plan": result}
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating research plan: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating research plan: {str(e)}"
        )

@router.post("/search", response_model=Dict[str, Any])
async def execute_search(
    search: SearchRequest,
    components: Dict = Depends(get_components)
):
    """
    Execute a search query.
    
    Args:
        search: The search request.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        The search results.
    """
    try:
        registry = components["registry"]
        results = registry.execute_capability(
            "execute_search",
            **search.model_dump()
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Error executing search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error executing search: {str(e)}"
        )

@router.post("/workflow/search", response_model=Dict[str, Any])
async def execute_search_workflow(
    workflow: WorkflowRequest,
    background_tasks: BackgroundTasks,
    components: Dict = Depends(get_components)
):
    """
    Execute a search workflow.
    
    Args:
        workflow: The workflow request.
        background_tasks: FastAPI background tasks.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        A response indicating the workflow has started.
    """
    try:
        orchestrator = components["orchestrator"]
        
        # Run workflow in background
        background_tasks.add_task(
            orchestrator.execute_search_and_summarize,
            query=workflow.query,
            task_id=workflow.task_id
        )
        
        return {
            "status": "accepted",
            "message": "Search workflow started",
            "query": workflow.query
        }
    except Exception as e:
        logger.error(f"Error starting search workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting search workflow: {str(e)}"
        )

@router.post("/workflow/research", response_model=Dict[str, Any])
async def execute_research_workflow(
    workflow: WorkflowRequest,
    background_tasks: BackgroundTasks,
    components: Dict = Depends(get_components)
):
    """
    Execute a complete research workflow.
    
    Args:
        workflow: The workflow request.
        background_tasks: FastAPI background tasks.
        components: The components to use (registry, orchestrator, db).
        
    Returns:
        A response indicating the workflow has started.
    """
    try:
        if not workflow.title or not workflow.description:
            raise HTTPException(
                status_code=400,
                detail="Title and description are required for research workflow"
            )
            
        orchestrator = components["orchestrator"]
        
        # Run workflow in background
        background_tasks.add_task(
            orchestrator.execute_basic_research,
            title=workflow.title,
            description=workflow.description,
            query=workflow.query
        )
        
        return {
            "status": "accepted",
            "message": "Research workflow started",
            "title": workflow.title,
            "query": workflow.query
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting research workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting research workflow: {str(e)}"
        )