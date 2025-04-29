"""
Custom exceptions for the Research System.

This module defines a hierarchy of custom exceptions for the Research System.
These exceptions provide more specific error information than standard Python
exceptions, making it easier to understand and handle errors appropriately.

Using custom exceptions helps with:
1. Providing clear, meaningful error messages
2. Enabling precise exception handling
3. Making error sources easily identifiable
4. Supporting better error reporting to users
"""

from typing import Optional, Dict, Any


class ResearchSystemError(Exception):
    """Base class for all Research System exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception with a message and optional details.
        
        Args:
            message: Human-readable error message
            details: Additional structured information about the error
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(ResearchSystemError):
    """Raised when there is an error in the configuration."""
    pass


class DatabaseError(ResearchSystemError):
    """Base class for database-related exceptions."""
    pass


class ConnectionError(DatabaseError):
    """Raised when a database connection cannot be established."""
    pass


class QueryError(DatabaseError):
    """Raised when a database query fails."""
    pass


class DataIntegrityError(DatabaseError):
    """Raised when data integrity constraints are violated."""
    pass


class ValidationError(ResearchSystemError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize with a message, field name, and optional details.
        
        Args:
            message: Human-readable error message
            field: The name of the field that failed validation
            details: Additional structured information about the error
        """
        super().__init__(message, details)
        self.field = field


class AuthenticationError(ResearchSystemError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(ResearchSystemError):
    """Raised when a user lacks permission to perform an action."""
    pass


class LLMServiceError(ResearchSystemError):
    """Base class for LLM service-related exceptions."""
    pass


class LLMConnectionError(LLMServiceError):
    """Raised when connection to an LLM service fails."""
    pass


class LLMResponseError(LLMServiceError):
    """Raised when an LLM service returns an invalid or unexpected response."""
    pass


class AgentError(ResearchSystemError):
    """Base class for agent-related exceptions."""
    pass


class CapabilityNotFoundError(AgentError):
    """Raised when a requested capability cannot be found."""
    
    def __init__(self, capability: str, provider: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize with a capability name, provider name, and optional details.
        
        Args:
            capability: The name of the capability that was not found
            provider: The name of the provider, if specified
            details: Additional structured information about the error
        """
        message = f"Capability '{capability}' not found"
        if provider:
            message += f" in provider '{provider}'"
        super().__init__(message, details)
        self.capability = capability
        self.provider = provider


class ProviderNotFoundError(AgentError):
    """Raised when a requested provider cannot be found."""
    
    def __init__(self, provider: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize with a provider name and optional details.
        
        Args:
            provider: The name of the provider that was not found
            details: Additional structured information about the error
        """
        message = f"Provider '{provider}' not found"
        super().__init__(message, details)
        self.provider = provider


class ResourceNotFoundError(ResearchSystemError):
    """Raised when a requested resource cannot be found."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize with a resource type, ID, and optional details.
        
        Args:
            resource_type: The type of resource that was not found
            resource_id: The ID of the resource that was not found
            details: Additional structured information about the error
        """
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class TaskNotFoundError(ResourceNotFoundError):
    """Raised when a requested task cannot be found."""
    
    def __init__(self, task_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize with a task ID and optional details.
        
        Args:
            task_id: The ID of the task that was not found
            details: Additional structured information about the error
        """
        super().__init__("Task", task_id, details)


class ResultNotFoundError(ResourceNotFoundError):
    """Raised when a requested result cannot be found."""
    
    def __init__(self, result_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize with a result ID and optional details.
        
        Args:
            result_id: The ID of the result that was not found
            details: Additional structured information about the error
        """
        super().__init__("Result", result_id, details)