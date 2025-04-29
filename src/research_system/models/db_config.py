"""
Database Configuration for Research System.

DEPRECATED: This module is replaced by the centralized configuration system
in research_system.config. Use that module instead.

This module remains here for backward compatibility but will be removed in a future version.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import centralized configuration
from research_system.config import load_config, get_database_config

# Log deprecation warning
logger.warning(
    "research_system.models.db_config is deprecated. Use research_system.config instead. "
    "This module will be removed in a future version."
)

# Compatibility functions that use the centralized configuration

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    DEPRECATED: Use research_system.config.load_config instead.
    
    Load configuration from various sources.
    
    Args:
        config_path: Optional path to a YAML configuration file
        
    Returns:
        Merged configuration dictionary
    """
    return load_config(config_path)


def get_env_config() -> Dict[str, Any]:
    """
    DEPRECATED: Use research_system.config.load_from_env instead.
    
    Create a configuration dictionary from environment variables.
    
    Returns:
        Configuration dictionary derived from environment variables
    """
    from research_system.config import load_from_env
    return {"database": get_database_config(load_from_env())}


def build_connection_string(config: Dict[str, Any]) -> str:
    """
    DEPRECATED: Use research_system.config.get_database_config instead.
    
    Build a PostgreSQL connection string from configuration.
    
    Args:
        config: Database configuration dictionary
        
    Returns:
        PostgreSQL connection string
    """
    db_config = get_database_config(config)
    return db_config.get("connection_string", "")


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    DEPRECATED: Use research_system.config.deep_merge instead.
    
    Deep merge two dictionaries, modifying the base dictionary in place.
    
    Args:
        base: Base dictionary to merge into
        override: Dictionary with values to override
    """
    from research_system.config import deep_merge as config_deep_merge
    config_deep_merge(base, override)


def get_database_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    DEPRECATED: Use research_system.config.get_database_config instead.
    
    Get the complete database configuration.
    
    Args:
        config_path: Optional path to a configuration file
        
    Returns:
        Database configuration dictionary
    """
    if isinstance(config_path, dict):
        # If a config dict was passed instead of a path, use it directly
        return get_database_config(config_path)
    
    # Otherwise load config from path
    config = load_config(config_path)
    return get_database_config(config)