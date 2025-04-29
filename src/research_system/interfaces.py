"""
Core interfaces for the Research System.

This module defines abstract interfaces for the major components of the
Research System, establishing clear contracts between components and
promoting maintainability and extensibility through proper abstraction.

These interfaces define the methods that must be implemented by concrete
classes, ensuring that components can be replaced or extended without
breaking dependent code.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union


class DatabaseInterface(ABC):
    """
    Interface for database operations in the Research System.
    
    This interface defines the contract that all database implementations
    must follow, ensuring that different database backends can be used
    interchangeably.
    """
    
    @abstractmethod
    def ping(self) -> bool:
        """
        Check if the database is reachable and operational.
        
        Returns:
            bool: True if the database is healthy, False otherwise
        """
        pass
        
    @abstractmethod
    def list_tasks(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List research tasks stored in the database.
        
        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of task objects as dictionaries
        """
        pass
    
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: The unique identifier of the task
            
        Returns:
            Task object as dictionary, or None if not found
        """
        pass
    
    @abstractmethod
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new research task.
        
        Args:
            task_data: Task data including title, description, etc.
            
        Returns:
            The created task with generated ID and metadata
        """
        pass
    
    @abstractmethod
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing task.
        
        Args:
            task_id: The unique identifier of the task
            task_data: Updated task data
            
        Returns:
            The updated task, or None if the task was not found
        """
        pass
    
    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task by ID.
        
        Args:
            task_id: The unique identifier of the task
            
        Returns:
            True if the task was deleted, False if it wasn't found
        """
        pass
    
    @abstractmethod
    def list_results(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List research results stored in the database.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of result objects as dictionaries
        """
        pass
    
    @abstractmethod
    def list_results_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        List all results for a specific task.
        
        Args:
            task_id: The unique identifier of the task
            
        Returns:
            List of result objects for the specified task
        """
        pass
    
    @abstractmethod
    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific result by ID.
        
        Args:
            result_id: The unique identifier of the result
            
        Returns:
            Result object as dictionary, or None if not found
        """
        pass
    
    @abstractmethod
    def create_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new research result.
        
        Args:
            result_data: Result data including task ID, content, etc.
            
        Returns:
            The created result with generated ID and metadata
        """
        pass
    
    @abstractmethod
    def update_result(self, result_id: str, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing result.
        
        Args:
            result_id: The unique identifier of the result
            result_data: Updated result data
            
        Returns:
            The updated result, or None if the result was not found
        """
        pass
    
    @abstractmethod
    def delete_result(self, result_id: str) -> bool:
        """
        Delete a result by ID.
        
        Args:
            result_id: The unique identifier of the result
            
        Returns:
            True if the result was deleted, False if it wasn't found
        """
        pass


class LLMServiceInterface(ABC):
    """
    Interface for LLM (Large Language Model) services.
    
    This interface defines the contract that all LLM service implementations
    must follow, ensuring that different LLM providers can be used
    interchangeably.
    """
    
    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The input prompt for text generation
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text as a string
        """
        pass
    
    @abstractmethod
    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from text according to a schema.
        
        Args:
            text: The text to extract data from
            schema: The schema defining the structure of the data to extract
            
        Returns:
            Extracted structured data as a dictionary
        """
        pass
    
    @abstractmethod
    def evaluate_relevance(self, query: str, document: str) -> float:
        """
        Evaluate the relevance of a document to a query.
        
        Args:
            query: The search query
            document: The document to evaluate
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate vector embeddings for the given text.
        
        Args:
            text: The input text to convert to embeddings
            
        Returns:
            Vector representation as a list of floats
        """
        pass


class AgentInterface(ABC):
    """
    Interface for research agents in the system.
    
    This interface defines the contract that all research agents must
    follow, ensuring consistency and interoperability between different
    agent implementations.
    """
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get a list of capabilities provided by this agent.
        
        Returns:
            List of capability names as strings
        """
        pass
    
    @abstractmethod
    def execute_capability(self, name: str, **kwargs) -> Any:
        """
        Execute a specific capability by name.
        
        Args:
            name: The name of the capability to execute
            **kwargs: Parameters for the capability
            
        Returns:
            Result of the capability execution
            
        Raises:
            ValueError: If the agent doesn't provide the requested capability
        """
        pass


class RegistryInterface(ABC):
    """
    Interface for the capability registry system.
    
    This interface defines the contract for the registry that manages
    capabilities and providers, allowing components to discover and
    execute capabilities without direct coupling.
    """
    
    @abstractmethod
    def register_provider(self, name: str, provider: Any) -> None:
        """
        Register a provider with the registry.
        
        Args:
            name: Identifier for the provider
            provider: The provider object
            
        Raises:
            ValueError: If a provider with the same name is already registered
        """
        pass
    
    @abstractmethod
    def get_provider(self, name: str) -> Any:
        """
        Get a provider by name.
        
        Args:
            name: The name of the provider to retrieve
            
        Returns:
            The provider object
            
        Raises:
            ValueError: If no provider with that name is registered
        """
        pass
    
    @abstractmethod
    def register_capability(self, capability: str, provider_name: str) -> None:
        """
        Register a capability provided by a specific provider.
        
        Args:
            capability: The name of the capability
            provider_name: The name of the provider
            
        Raises:
            ValueError: If the provider is not registered
        """
        pass
    
    @abstractmethod
    def execute_capability(self, capability: str, **kwargs) -> Any:
        """
        Execute a capability by name.
        
        Args:
            capability: The name of the capability to execute
            **kwargs: Parameters for the capability
            
        Returns:
            Result of the capability execution
            
        Raises:
            ValueError: If no provider is registered for the capability
        """
        pass


class ConfigInterface(ABC):
    """
    Interface for configuration management.
    
    This interface defines the contract for configuration providers,
    ensuring consistent access to configuration values across the system.
    """
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key to retrieve
            default: Default value if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        pass
    
    @abstractmethod
    def as_dict(self) -> Dict[str, Any]:
        """
        Get the complete configuration as a dictionary.
        
        Returns:
            The complete configuration dictionary
        """
        pass