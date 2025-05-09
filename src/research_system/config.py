"""
Centralized configuration module for the Research System.

This module provides functions for loading and accessing application configuration.
"""

import os
import logging
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parents[2] / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger = logging.getLogger(__name__)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    # Try to find .env in the current directory
    current_dir_env = Path.cwd() / '.env'
    if current_dir_env.exists():
        load_dotenv(dotenv_path=current_dir_env)
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded environment variables from {current_dir_env}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "app": {
        "name": "Research System",
        "port": 8080,
        "debug": False
    },
    "database": {
        "use_postgres": False,
        "postgres_host": "localhost",
        "postgres_port": 5432,
        "postgres_db": "research",
        "postgres_user": "postgres",
        "postgres_password": "postgres",
        "tinydb_path": "./data/research.json"
    },
    "memory": {
        "consolidation_interval": 3600,  # 1 hour
        "vector_search_enabled": False
    }
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment.
    
    Args:
        config_path: Path to YAML configuration file (optional).
        
    Returns:
        Dictionary containing configuration.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as file:
                file_config = yaml.safe_load(file)
                if file_config:
                    _deep_update(config, file_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
    
    # Override with environment variables
    _update_from_env(config)
    
    return config


def get_database_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get database configuration.
    
    Args:
        config: Optional configuration dictionary. If not provided, will load from default config.
        
    Returns:
        Dictionary containing database configuration.
    """
    if config is None:
        config = load_config()
    
    db_config = config.get("database", {}).copy()
    
    # Build connection string if using PostgreSQL
    if db_config.get("use_postgres", False):
        host = db_config.get("postgres_host", "localhost")
        port = db_config.get("postgres_port", 5432)
        dbname = db_config.get("postgres_db", "research")
        user = db_config.get("postgres_user", "postgres")
        password = db_config.get("postgres_password", "postgres")
        
        db_config["connection_string"] = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    return db_config


def _deep_update(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """
    Recursively update a dictionary with another dictionary.
    
    Args:
        base: Base dictionary to update
        update: Dictionary with updates to apply
    """
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def _update_from_env(config: Dict) -> None:
    """
    Update configuration with environment variables.

    Args:
        config: Configuration dictionary to update.
    """
    # App configuration
    if "PORT" in os.environ:
        config["app"]["port"] = int(os.environ["PORT"])

    if "SERVER_PORT" in os.environ:
        config["app"]["port"] = int(os.environ["SERVER_PORT"])

    if "DEBUG" in os.environ:
        config["app"]["debug"] = os.environ["DEBUG"].lower() == "true"

    # Database configuration
    if "DB_USE_POSTGRES" in os.environ or "USE_POSTGRES" in os.environ:
        use_postgres = os.environ.get("DB_USE_POSTGRES", os.environ.get("USE_POSTGRES"))
        config["database"]["use_postgres"] = use_postgres.lower() == "true"

    if "POSTGRES_HOST" in os.environ or "DB_POSTGRES_HOST" in os.environ:
        config["database"]["postgres_host"] = os.environ.get("DB_POSTGRES_HOST", os.environ.get("POSTGRES_HOST", "localhost"))

    if "POSTGRES_PORT" in os.environ or "DB_POSTGRES_PORT" in os.environ:
        port_str = os.environ.get("DB_POSTGRES_PORT", os.environ.get("POSTGRES_PORT", "5432"))
        config["database"]["postgres_port"] = int(port_str)

    if "POSTGRES_DB" in os.environ or "DB_POSTGRES_DBNAME" in os.environ:
        config["database"]["postgres_db"] = os.environ.get("DB_POSTGRES_DBNAME", os.environ.get("POSTGRES_DB", "research"))

    if "POSTGRES_USER" in os.environ or "DB_POSTGRES_USER" in os.environ:
        config["database"]["postgres_user"] = os.environ.get("DB_POSTGRES_USER", os.environ.get("POSTGRES_USER", "postgres"))

    if "POSTGRES_PASSWORD" in os.environ or "DB_POSTGRES_PASSWORD" in os.environ:
        config["database"]["postgres_password"] = os.environ.get("DB_POSTGRES_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "postgres"))

    if "TINYDB_PATH" in os.environ:
        config["database"]["tinydb_path"] = os.environ["TINYDB_PATH"]

    # Database URL (overrides individual settings)
    if "DATABASE_URL" in os.environ:
        db_url = os.environ["DATABASE_URL"]
        # If this is set, ensure use_postgres is True
        if db_url.startswith("postgresql"):
            config["database"]["use_postgres"] = True
            config["database"]["connection_string"] = db_url

    # Memory configuration
    if "MEMORY_CONSOLIDATION_INTERVAL" in os.environ:
        config["memory"]["consolidation_interval"] = int(os.environ["MEMORY_CONSOLIDATION_INTERVAL"])

    if "MEMORY_VECTOR_SEARCH_ENABLED" in os.environ:
        config["memory"]["vector_search_enabled"] = os.environ["MEMORY_VECTOR_SEARCH_ENABLED"].lower() == "true"

    # LLM configuration
    if "llm" not in config:
        config["llm"] = {}

    if "OLLAMA_URL" in os.environ:
        config["llm"]["url"] = os.environ["OLLAMA_URL"]

    if "OLLAMA_MODEL" in os.environ:
        config["llm"]["model"] = os.environ["OLLAMA_MODEL"]

    if "PLANNER_LLM_MODEL" in os.environ:
        config["llm"]["planner_model"] = os.environ["PLANNER_LLM_MODEL"]

    if "SEARCH_LLM_MODEL" in os.environ:
        config["llm"]["search_model"] = os.environ["SEARCH_LLM_MODEL"]

    if "USE_LLM" in os.environ:
        config["llm"]["enabled"] = os.environ["USE_LLM"].lower() == "true"

    # Search configuration
    if "search" not in config:
        config["search"] = {}

    if "BRAVE_SEARCH_API_KEY" in os.environ:
        config["search"]["brave_api_key"] = os.environ["BRAVE_SEARCH_API_KEY"]

def is_development() -> bool:
    """
    Check if the application is running in development mode.
    
    Returns:
        True if in development mode, False otherwise.
    """
    return get_env_name() == "development"

def get_env_name() -> str:
    """
    Get the environment name.
    
    Returns:
        The environment name (development, staging, production).
    """
    return os.getenv("ENV_NAME", "development").lower()