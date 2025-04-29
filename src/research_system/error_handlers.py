"""
Global error handlers for the Research System API.

This module defines FastAPI exception handlers for the Research System's custom
exceptions, ensuring consistent error responses across the API.

Each handler is designed to:
1. Log the error appropriately
2. Create a structured error response
3. Return the appropriate HTTP status code
"""

import logging
import time
import traceback
from typing import Dict, Any, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from research_system.exceptions import (
    ResearchSystemError,
    ValidationError,
    ConfigurationError,
    DatabaseError,
    ConnectionError,
    QueryError,
    DataIntegrityError,
    AuthenticationError,
    AuthorizationError,
    LLMServiceError,
    LLMConnectionError,
    LLMResponseError,
    AgentError,
    CapabilityNotFoundError,
    ProviderNotFoundError,
    ResourceNotFoundError,
    TaskNotFoundError,
    ResultNotFoundError,
)

# Configure logging
logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        status_code: The HTTP status code for the response
        error_type: The type of error that occurred
        message: A human-readable error message
        details: Additional structured information about the error
        request_id: A unique identifier for the request
        
    Returns:
        A JSONResponse object with the error information
    """
    response_body = {
        "error": {
            "type": error_type,
            "message": message,
            "timestamp": time.time()
        }
    }
    
    if details:
        response_body["error"]["details"] = details
        
    if request_id:
        response_body["error"]["request_id"] = request_id
        
    return JSONResponse(status_code=status_code, content=response_body)


def get_request_id(request: Request) -> Optional[str]:
    """
    Extract the request ID from the request state or headers.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The request ID if available, or None
    """
    # Try to get request ID from request state
    if hasattr(request.state, "request_id"):
        return request.state.request_id
        
    # Try to get request ID from headers
    return request.headers.get("X-Request-ID")


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI request validation errors.
    
    Args:
        request: The FastAPI request object
        exc: The RequestValidationError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    # Extract error details from the validation error
    details = {"validation_errors": []}
    for error in exc.errors():
        error_info = {
            "location": error["loc"],
            "message": error["msg"],
            "type": error["type"]
        }
        details["validation_errors"].append(error_info)
    
    logger.warning(
        f"Validation error: {exc}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="validation_error",
        message="Invalid request data",
        details=details,
        request_id=request_id
    )


async def pydantic_validation_error_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: The FastAPI request object
        exc: The PydanticValidationError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    # Extract error details from the validation error
    details = {"validation_errors": []}
    for error in exc.errors():
        error_info = {
            "location": error["loc"],
            "message": error["msg"],
            "type": error["type"]
        }
        details["validation_errors"].append(error_info)
    
    logger.warning(
        f"Pydantic validation error: {exc}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="validation_error",
        message="Invalid data structure",
        details=details,
        request_id=request_id
    )


async def custom_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle custom validation errors.
    
    Args:
        request: The FastAPI request object
        exc: The ValidationError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    details = exc.details.copy() if exc.details else {}
    if exc.field:
        details["field"] = exc.field
    
    logger.warning(
        f"Validation error: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="validation_error",
        message=exc.message,
        details=details,
        request_id=request_id
    )


async def configuration_error_handler(request: Request, exc: ConfigurationError) -> JSONResponse:
    """
    Handle configuration errors.
    
    Args:
        request: The FastAPI request object
        exc: The ConfigurationError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    logger.error(
        f"Configuration error: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="configuration_error",
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """
    Handle database errors.
    
    Args:
        request: The FastAPI request object
        exc: The DatabaseError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    logger.error(
        f"Database error: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    # Determine the appropriate status code based on the error type
    if isinstance(exc, ConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_type = "database_connection_error"
    elif isinstance(exc, QueryError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "database_query_error"
    elif isinstance(exc, DataIntegrityError):
        status_code = status.HTTP_409_CONFLICT
        error_type = "data_integrity_error"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "database_error"
    
    return create_error_response(
        status_code=status_code,
        error_type=error_type,
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )


async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """
    Handle authentication errors.
    
    Args:
        request: The FastAPI request object
        exc: The AuthenticationError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    logger.warning(
        f"Authentication error: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return create_error_response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_type="authentication_error",
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """
    Handle authorization errors.
    
    Args:
        request: The FastAPI request object
        exc: The AuthorizationError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    logger.warning(
        f"Authorization error: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return create_error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error_type="authorization_error",
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )


async def llm_service_error_handler(request: Request, exc: LLMServiceError) -> JSONResponse:
    """
    Handle LLM service errors.
    
    Args:
        request: The FastAPI request object
        exc: The LLMServiceError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    logger.error(
        f"LLM service error: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    # Determine the appropriate status code based on the error type
    if isinstance(exc, LLMConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_type = "llm_connection_error"
    elif isinstance(exc, LLMResponseError):
        status_code = status.HTTP_502_BAD_GATEWAY
        error_type = "llm_response_error"
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "llm_service_error"
    
    return create_error_response(
        status_code=status_code,
        error_type=error_type,
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )


async def agent_error_handler(request: Request, exc: AgentError) -> JSONResponse:
    """
    Handle agent-related errors.
    
    Args:
        request: The FastAPI request object
        exc: The AgentError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    logger.error(
        f"Agent error: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    # Determine the appropriate status code and error type
    if isinstance(exc, CapabilityNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        error_type = "capability_not_found"
        details = exc.details.copy() if exc.details else {}
        details.update({
            "capability": exc.capability,
            "provider": exc.provider
        })
    elif isinstance(exc, ProviderNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
        error_type = "provider_not_found"
        details = exc.details.copy() if exc.details else {}
        details.update({"provider": exc.provider})
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = "agent_error"
        details = exc.details
    
    return create_error_response(
        status_code=status_code,
        error_type=error_type,
        message=exc.message,
        details=details,
        request_id=request_id
    )


async def resource_not_found_error_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    """
    Handle resource not found errors.
    
    Args:
        request: The FastAPI request object
        exc: The ResourceNotFoundError exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    logger.info(
        f"Resource not found: {exc.message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    details = exc.details.copy() if exc.details else {}
    details.update({
        "resource_type": exc.resource_type,
        "resource_id": exc.resource_id
    })
    
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_type="resource_not_found",
        message=exc.message,
        details=details,
        request_id=request_id
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions not explicitly covered.
    
    Args:
        request: The FastAPI request object
        exc: The exception
        
    Returns:
        A standardized JSON error response
    """
    request_id = get_request_id(request)
    
    # Get traceback information
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    # In production, we don't want to expose internal error details
    from research_system.config import is_development
    
    details = None
    if is_development():
        details = {
            "traceback": tb_str,
            "exception_type": type(exc).__name__
        }
    
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="internal_server_error",
        message="An unexpected error occurred",
        details=details,
        request_id=request_id
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with a FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    # FastAPI validation error
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    
    # Pydantic validation error
    app.add_exception_handler(PydanticValidationError, pydantic_validation_error_handler)
    
    # Custom validation error
    app.add_exception_handler(ValidationError, custom_validation_error_handler)
    
    # Configuration error
    app.add_exception_handler(ConfigurationError, configuration_error_handler)
    
    # Database errors
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(ConnectionError, database_error_handler)
    app.add_exception_handler(QueryError, database_error_handler)
    app.add_exception_handler(DataIntegrityError, database_error_handler)
    
    # Authentication and authorization errors
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    
    # LLM service errors
    app.add_exception_handler(LLMServiceError, llm_service_error_handler)
    app.add_exception_handler(LLMConnectionError, llm_service_error_handler)
    app.add_exception_handler(LLMResponseError, llm_service_error_handler)
    
    # Agent errors
    app.add_exception_handler(AgentError, agent_error_handler)
    app.add_exception_handler(CapabilityNotFoundError, agent_error_handler)
    app.add_exception_handler(ProviderNotFoundError, agent_error_handler)
    
    # Resource not found errors
    app.add_exception_handler(ResourceNotFoundError, resource_not_found_error_handler)
    app.add_exception_handler(TaskNotFoundError, resource_not_found_error_handler)
    app.add_exception_handler(ResultNotFoundError, resource_not_found_error_handler)
    
    # Generic exception handler for all other exceptions
    app.add_exception_handler(Exception, generic_exception_handler)