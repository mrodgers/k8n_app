"""
LLM integration endpoints for the Research System.

This module provides API endpoints for accessing and using 
Large Language Model capabilities.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/llm", tags=["LLM"])

# Pydantic models for request/response validation
class LLMCompletionRequest(BaseModel):
    """
    Request model for LLM text completion.
    
    Attributes:
        prompt: The input text to generate completion for
        model: Specific model to use (defaults to system default)
        system: System message to guide the completion
        options: Additional model-specific options
    """
    prompt: str
    model: Optional[str] = None
    system: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class LLMChatRequest(BaseModel):
    """
    Request model for LLM chat completion.
    
    Attributes:
        messages: Array of message objects with role and content
        model: Specific model to use (defaults to system default)
        options: Additional model-specific options
    """
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

@router.post("/completion")
async def generate_llm_completion(request: LLMCompletionRequest, req: Request):
    """
    Generate a text completion with the LLM.
    
    Creates a completion for the given prompt using the configured LLM service.
    
    Args:
        request: Request containing prompt and options
        
    Returns:
        dict: The completion result with generated text
        
    Raises:
        HTTPException: 503 error if LLM service is unavailable
                      500 error if completion generation fails
    """
    if not getattr(req.app.state, "llm_enabled", False) or not hasattr(req.app.state, "ollama_server"):
        raise HTTPException(status_code=503, detail="LLM service is not available")
    
    try:
        result = req.app.state.ollama_server.generate_completion(
            prompt=request.prompt,
            model=request.model,
            system=request.system,
            options=request.options
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def generate_llm_chat_completion(request: LLMChatRequest, req: Request):
    """
    Generate a chat completion with the LLM.
    
    Creates a chat completion from a sequence of messages using the configured LLM service.
    
    Args:
        request: Request containing messages and options
        
    Returns:
        dict: The chat completion result with generated response
        
    Raises:
        HTTPException: 503 error if LLM service is unavailable
                      500 error if chat completion generation fails
    """
    if not getattr(req.app.state, "llm_enabled", False) or not hasattr(req.app.state, "ollama_server"):
        raise HTTPException(status_code=503, detail="LLM service is not available")
    
    try:
        result = req.app.state.ollama_server.generate_chat_completion(
            messages=request.messages,
            model=request.model,
            options=request.options
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_llm_models(request: Request):
    """
    List all available LLM models.
    
    Retrieves the list of models available through the configured LLM service.
    
    Returns:
        dict: Object containing available models and their details
        
    Raises:
        HTTPException: 503 error if LLM service is unavailable
                      500 error if model listing fails
    """
    if not getattr(request.app.state, "llm_enabled", False) or not hasattr(request.app.state, "ollama_server"):
        raise HTTPException(status_code=503, detail="LLM service is not available")
    
    try:
        models = request.app.state.ollama_server.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))