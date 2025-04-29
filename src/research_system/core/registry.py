"""
Agent Registry Module for the Research System.

This module provides a central registry for capability providers
(like agents) and allows direct invocation of capabilities without
relying on HTTP communication between components.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable, Protocol
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define protocol for a capability provider
class CapabilityProvider(Protocol):
    """Protocol for a capability provider."""
    
    def get_capabilities(self) -> List[str]:
        """Get a list of capabilities provided by this provider."""
        ...
    
    def execute_capability(self, name: str, **kwargs) -> Any:
        """Execute a capability by name with the given arguments."""
        ...

class Registry:
    """
    Central registry for capability providers.
    
    This class manages the registration and lookup of capability providers,
    allowing the system to find and execute capabilities by name.
    """
    
    def __init__(self, name: str = "Research Registry"):
        """
        Initialize the registry.
        
        Args:
            name: The name of the registry.
        """
        self.name = name
        self.providers = {}
        self.workflows = {}
        self.capabilities_map = {}  # Maps capability names to provider names
        logger.info(f"Registry '{name}' initialized")
    
    def register_provider(self, name: str, provider) -> None:
        """
        Register a provider with the registry.
        
        Args:
            name: The name of the provider.
            provider: The provider to register.
            
        Raises:
            ValueError: If a provider with the same name is already registered.
        """
        if name in self.providers:
            raise ValueError(f"Provider '{name}' is already registered")
        
        self.providers[name] = provider
        
        # Map capabilities to this provider
        try:
            capabilities = provider.get_capabilities()
            for capability in capabilities:
                # Check for capability name clashes
                if capability in self.capabilities_map:
                    existing_provider = self.capabilities_map[capability]
                    logger.warning(f"Capability '{capability}' is already provided by '{existing_provider}'. "
                                   f"It will be overridden by '{name}'.")
                
                self.capabilities_map[capability] = name
                logger.debug(f"Registered capability '{capability}' from provider '{name}'")
        except (AttributeError, TypeError):
            logger.warning(f"Provider '{name}' does not implement the CapabilityProvider protocol")
        
        logger.info(f"Registered provider: {name}")
    
    def unregister_provider(self, name: str) -> None:
        """
        Unregister a provider from the registry.
        
        Args:
            name: The name of the provider to unregister.
            
        Raises:
            ValueError: If no provider with the specified name is registered.
        """
        if name not in self.providers:
            raise ValueError(f"No provider named '{name}' is registered")
        
        # Remove capabilities provided by this provider
        capabilities_to_remove = [c for c, p in self.capabilities_map.items() if p == name]
        for capability in capabilities_to_remove:
            del self.capabilities_map[capability]
        
        # Remove the provider
        del self.providers[name]
        logger.info(f"Unregistered provider: {name}")
    
    def get_provider(self, name: str) -> Any:
        """
        Get a provider by name.
        
        Args:
            name: The name of the provider.
            
        Returns:
            The provider with the specified name.
            
        Raises:
            ValueError: If no provider with the specified name is registered.
        """
        if name not in self.providers:
            raise ValueError(f"No provider named '{name}' is registered")
        
        return self.providers[name]
    
    def list_providers(self) -> List[str]:
        """
        List all registered providers.
        
        Returns:
            A list of provider names.
        """
        return list(self.providers.keys())
    
    def list_capabilities(self) -> Dict[str, str]:
        """
        List all registered capabilities.
        
        Returns:
            A dictionary mapping capability names to provider names.
        """
        return self.capabilities_map.copy()
    
    def execute_capability(self, capability: str, **kwargs) -> Any:
        """
        Execute a capability by name.
        
        Args:
            capability: The name of the capability to execute.
            **kwargs: Arguments to pass to the capability.
            
        Returns:
            The result of the capability execution.
            
        Raises:
            ValueError: If no provider is registered for the specified capability.
        """
        if capability not in self.capabilities_map:
            raise ValueError(f"No provider registered for capability '{capability}'")
        
        provider_name = self.capabilities_map[capability]
        provider = self.get_provider(provider_name)
        
        logger.debug(f"Executing capability '{capability}' from provider '{provider_name}'")
        return provider.execute_capability(capability, **kwargs)
    
    def register_workflow(self, name: str, workflow_func: Callable, description: str = "") -> None:
        """
        Register a workflow with the registry.
        
        A workflow is a function that orchestrates multiple capabilities to accomplish a task.
        
        Args:
            name: The name of the workflow.
            workflow_func: The function that implements the workflow.
            description: Optional description of the workflow.
            
        Raises:
            ValueError: If a workflow with the same name is already registered.
        """
        if name in self.workflows:
            raise ValueError(f"Workflow '{name}' is already registered")
        
        self.workflows[name] = {
            "function": workflow_func,
            "description": description
        }
        logger.info(f"Registered workflow: {name}")
    
    def run_workflow(self, name: str, **kwargs) -> Any:
        """
        Run a workflow.
        
        Args:
            name: The name of the workflow to run.
            **kwargs: Arguments to pass to the workflow.
            
        Returns:
            The result of the workflow.
            
        Raises:
            ValueError: If no workflow with the specified name is registered.
        """
        if name not in self.workflows:
            raise ValueError(f"No workflow named '{name}' is registered")
        
        # Run the workflow
        workflow = self.workflows[name]["function"]
        logger.info(f"Running workflow: {name}")
        result = workflow(self, **kwargs)
        logger.info(f"Workflow '{name}' completed")
        return result
    
    def list_workflows(self) -> Dict[str, str]:
        """
        List all registered workflows.
        
        Returns:
            A dictionary mapping workflow names to their descriptions.
        """
        return {name: info["description"] for name, info in self.workflows.items()}


# Create a default registry instance
default_registry = Registry()

# Function to load and register providers automatically
def auto_register_providers(registry: Registry = default_registry):
    """
    Automatically load and register refactored agents.
    
    This function dynamically loads agent modules and registers
    them with the registry.
    """
    try:
        # Import refactored agents
        import research_system.agents.planner_refactored
        import research_system.agents.search_refactored
        
        # Register planner
        registry.register_provider(
            name="planner",
            provider=research_system.agents.planner_refactored.default_planner
        )
        
        # Register search agent
        registry.register_provider(
            name="search",
            provider=research_system.agents.search_refactored.default_search
        )
        
        logger.info("Auto-registered agent providers")
        return True
    except Exception as e:
        logger.error(f"Error auto-registering providers: {e}")
        return False

# Don't auto-register providers here to avoid duplicate registration
# auto_register_providers()  # Will be called from app_factory.py