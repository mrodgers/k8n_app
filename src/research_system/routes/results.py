"""
Research results endpoints for the Research System.

This module provides API endpoints for retrieving and 
managing research results.
"""

from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/api/results", tags=["Results"])

@router.get("/{result_id}")
async def get_result(result_id: str, request: Request):
    """
    Get a research result by ID.
    
    Args:
        result_id: Unique identifier of the result
        
    Returns:
        dict: Result object with all properties
        
    Raises:
        HTTPException: 404 error if result not found
    """
    result = request.app.state.db.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"result": result.model_dump()}

@router.get("/task/{task_id}")
async def get_task_results(task_id: str, request: Request):
    """
    Get all research results for a task.
    
    Args:
        task_id: Unique identifier of the task
        
    Returns:
        dict: Object containing an array of result objects
        
    Raises:
        HTTPException: 404 error if task not found
    """
    try:
        # Check if task exists
        task = request.app.state.db.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get results for this task
        results = request.app.state.db.list_results_for_task(task_id)
        
        # Convert results to dicts
        result_dicts = [result.model_dump() for result in results]
        
        return {"results": result_dicts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))