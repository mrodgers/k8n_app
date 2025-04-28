"""
Task management endpoints for the Research System.

This module provides API endpoints for creating, retrieving, 
and managing research tasks.
"""

from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Pydantic models for request/response validation
class TaskCreate(BaseModel):
    """
    Model for creating a new research task.
    
    Attributes:
        title: Title of the research task
        description: Detailed description of the task
        tags: List of tags to categorize the task
        assigned_to: Username of the person assigned to the task (optional)
    """
    title: str
    description: str
    tags: List[str] = []
    assigned_to: Optional[str] = None

class SearchRequest(BaseModel):
    """
    Model for search request parameters.
    
    Attributes:
        query: Search query string
        max_results: Maximum number of results to return
    """
    query: str
    max_results: int = 10

@router.get("")
async def list_tasks(request: Request):
    """
    List all research tasks.
    
    Returns:
        dict: Object containing an array of task objects
    """
    tasks = request.app.state.planner.list_research_tasks()
    return {"tasks": tasks}

@router.post("", status_code=201)
async def create_task(task: TaskCreate, request: Request):
    """
    Create a new research task.
    
    Args:
        task: Task data including title, description, and optional tags
        
    Returns:
        dict: The created task object
        
    Raises:
        HTTPException: 400 error if task creation fails
    """
    try:
        created_task = request.app.state.planner.create_research_task(
            title=task.title,
            description=task.description,
            tags=task.tags,
            assigned_to=task.assigned_to
        )
        return {"task": created_task}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{task_id}")
async def get_task(task_id: str, request: Request):
    """
    Get a research task by ID.
    
    Args:
        task_id: Unique identifier of the task
        
    Returns:
        dict: Task object with all properties
        
    Raises:
        HTTPException: 404 error if task not found
    """
    task = request.app.state.db.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.model_dump()}

@router.post("/{task_id}/plan", status_code=201)
async def create_plan(task_id: str, request: Request):
    """
    Create a research plan for a task.
    
    Generates a structured research plan with steps and objectives for the specified task.
    
    Args:
        task_id: Unique identifier of the task
        
    Returns:
        dict: The created plan object
        
    Raises:
        HTTPException: 400 error if plan creation fails or 404 if task not found
    """
    try:
        # Check if task exists
        task = request.app.state.db.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
            
        plan = request.app.state.planner.generate_plan_for_task(task_id)
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{task_id}/search")
async def task_search(task_id: str, search_request: SearchRequest, request: Request):
    """
    Execute a search for a task.
    
    Performs a search query associated with the specified task and returns results.
    
    Args:
        task_id: Unique identifier of the task
        search_request: Search parameters including query and max_results
        
    Returns:
        dict: Object containing an array of search results
        
    Raises:
        HTTPException: 400 error if search fails or 404 if task not found
    """
    try:
        # Check if task exists
        task = request.app.state.db.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
            
        results = request.app.state.search.execute_search(
            task_id=task_id,
            query=search_request.query,
            max_results=search_request.max_results
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))