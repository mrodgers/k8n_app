"""
Database Configuration for Research System.

This module provides utilities for loading and managing database configuration.
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

# Default configuration
DEFAULT_CONFIG = {
    "database": {
        "use_postgres": False,
        "tinydb_path": "./data/research.json",
        "postgres": {
            "host": "localhost",
            "port": 5432,
            "dbname": "research",
            "user": "postgres",
            "password": "postgres",
            "connect_timeout": 5,
            "retry_attempts": 3
        }
    }
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from various sources with priority:
    1. Environment variables
    2. Config file (if provided)
    3. Default values
    
    Args:
        config_path: Optional path to a YAML configuration file
        
    Returns:
        Merged configuration dictionary
    """
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Load from config file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config and isinstance(file_config, dict):
                    deep_merge(config, file_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Error loading config from {config_path}: {str(e)}")
    
    # Override with environment variables
    env_config = get_env_config()
    if env_config:
        deep_merge(config, env_config)
        logger.info("Applied environment variable configuration")
    
    return config


def get_env_config() -> Dict[str, Any]:
    """
    Create a configuration dictionary from environment variables.
    
    Environment variable naming convention:
    - DB_USE_POSTGRES: Use PostgreSQL or TinyDB (true/false)
    - DB_TINYDB_PATH: Path to TinyDB file
    - DB_POSTGRES_HOST: PostgreSQL host
    - DB_POSTGRES_PORT: PostgreSQL port
    - DB_POSTGRES_DBNAME: PostgreSQL database name
    - DB_POSTGRES_USER: PostgreSQL username
    - DB_POSTGRES_PASSWORD: PostgreSQL password
    - DATABASE_URL: Full database URL (overrides individual settings)
    
    Returns:
        Configuration dictionary derived from environment variables
    """
    config = {"database": {}}
    db_config = config["database"]
    
    # Check if PostgreSQL should be used
    use_postgres = os.getenv("DB_USE_POSTGRES", os.getenv("USE_POSTGRES", ""))
    if use_postgres:
        db_config["use_postgres"] = use_postgres.lower() in ("true", "1", "yes", "y")
    
    # TinyDB path
    tinydb_path = os.getenv("DB_TINYDB_PATH")
    if tinydb_path:
        db_config["tinydb_path"] = tinydb_path
    
    # Check for DATABASE_URL (highest priority for PostgreSQL configuration)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        db_config["use_postgres"] = True
        db_config["postgres"] = {"connection_url": database_url}
    else:
        # Individual PostgreSQL settings
        postgres_config = {}
        
        host = os.getenv("DB_POSTGRES_HOST", os.getenv("POSTGRES_SERVICE_HOST"))
        if host:
            postgres_config["host"] = host
        
        port = os.getenv("DB_POSTGRES_PORT", os.getenv("POSTGRES_SERVICE_PORT"))
        if port:
            postgres_config["port"] = int(port)
        
        dbname = os.getenv("DB_POSTGRES_DBNAME", os.getenv("POSTGRES_DB"))
        if dbname:
            postgres_config["dbname"] = dbname
        
        user = os.getenv("DB_POSTGRES_USER", os.getenv("POSTGRES_USER"))
        if user:
            postgres_config["user"] = user
        
        password = os.getenv("DB_POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD"))
        if password:
            postgres_config["password"] = password
        
        # Only add the postgres section if we have any PostgreSQL settings
        if postgres_config:
            db_config["postgres"] = postgres_config
    
    return config


def build_connection_string(config: Dict[str, Any]) -> str:
    """
    Build a PostgreSQL connection string from configuration.
    
    Args:
        config: Database configuration dictionary
        
    Returns:
        PostgreSQL connection string
    """
    db_config = config.get("database", {})
    postgres_config = db_config.get("postgres", {})
    
    # If a connection URL is provided, use it directly
    if "connection_url" in postgres_config:
        return postgres_config["connection_url"]
    
    # Otherwise, build from individual components
    host = postgres_config.get("host", "localhost")
    port = postgres_config.get("port", 5432)
    dbname = postgres_config.get("dbname", "research")
    user = postgres_config.get("user", "postgres")
    password = postgres_config.get("password", "postgres")
    
    # Build connection string
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    return connection_string


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    Deep merge two dictionaries, modifying the base dictionary in place.
    
    Args:
        base: Base dictionary to merge into
        override: Dictionary with values to override
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def get_database_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the complete database configuration.
    
    Args:
        config_path: Optional path to a configuration file
        
    Returns:
        Database configuration dictionary
    """
    config = load_config(config_path)
    db_config = config.get("database", {})
    
    # If PostgreSQL is enabled, ensure we have a connection string
    if db_config.get("use_postgres"):
        connection_string = build_connection_string(config)
        db_config["connection_string"] = connection_string
    
    return db_config