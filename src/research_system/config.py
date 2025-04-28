"""
Configuration management for the Research System.

This module centralizes all configuration loading and validation, supporting:
- Default configuration
- File-based configuration (YAML)
- Environment variable overrides
- Configuration validation

Usage:
    from research_system.config import load_config
    
    # Load with defaults
    config = load_config()
    
    # Load with specific path
    config = load_config("/path/to/config.yaml")
    
    # Access configuration
    db_config = config.get("database", {})
    app_port = config.get("app", {}).get("port", 8181)
"""

import os
import logging
import yaml
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_defaults() -> Dict[str, Any]:
    """Load default configuration values."""
    return {
        "app": {
            "port": 8181,
            "max_workers": 4,
            "cors": {
                "allow_origins": ["*"],
                "allow_methods": ["*"],
                "allow_headers": ["*"]
            }
        },
        "logging": {
            "level": "INFO"
        },
        "environment": "development",
        "database": {
            "type": "tinydb",
            "path": "data/research.json"
        },
        "llm": {
            "enabled": True,
            "model": "gemma3:1b",
            "timeout": 120,
            "url": "http://localhost:11434"
        }
    }

def load_from_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load configuration from {config_path}: {e}")
        return {}

def load_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    # App configuration
    if os.getenv("PORT"):
        _ensure_dict_path(config, ["app"])
        config["app"]["port"] = int(os.getenv("PORT"))
    
    if os.getenv("MAX_WORKERS"):
        _ensure_dict_path(config, ["app"])
        config["app"]["max_workers"] = int(os.getenv("MAX_WORKERS"))
    
    # Logging configuration
    if os.getenv("LOG_LEVEL"):
        _ensure_dict_path(config, ["logging"])
        config["logging"]["level"] = os.getenv("LOG_LEVEL")
    
    # Environment setting
    if os.getenv("ENV_MODE"):
        config["environment"] = os.getenv("ENV_MODE")
    
    # Database configuration
    if os.getenv("USE_POSTGRES") == "true":
        _ensure_dict_path(config, ["database"])
        config["database"]["type"] = "postgres"
    
    if os.getenv("DB_POSTGRES_HOST"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["host"] = os.getenv("DB_POSTGRES_HOST")
    
    if os.getenv("DB_POSTGRES_PORT"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["port"] = int(os.getenv("DB_POSTGRES_PORT"))
    
    if os.getenv("DB_POSTGRES_DBNAME"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["dbname"] = os.getenv("DB_POSTGRES_DBNAME")
    
    if os.getenv("DB_POSTGRES_USER"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["user"] = os.getenv("DB_POSTGRES_USER")
    
    if os.getenv("DB_POSTGRES_PASSWORD"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["password"] = os.getenv("DB_POSTGRES_PASSWORD")
    
    # LLM configuration
    if os.getenv("OLLAMA_URL"):
        _ensure_dict_path(config, ["llm"])
        config["llm"]["url"] = os.getenv("OLLAMA_URL")
    
    if os.getenv("OLLAMA_MODEL"):
        _ensure_dict_path(config, ["llm"])
        config["llm"]["model"] = os.getenv("OLLAMA_MODEL")
    
    return config

def _ensure_dict_path(config: Dict[str, Any], path: list) -> None:
    """Ensure that a nested dictionary path exists."""
    current = config
    for key in path:
        if key not in current:
            current[key] = {}
        current = current[key]

def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries. 
    If the same key exists in both dictionaries and both values are dictionaries,
    the values are merged recursively.
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration and log warnings for issues.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    valid = True
    
    # Validate app port
    try:
        port = config.get("app", {}).get("port")
        if port is not None and (not isinstance(port, int) or port < 1 or port > 65535):
            logger.warning(f"Invalid port number: {port}. Must be between 1-65535.")
            valid = False
    except Exception:
        logger.warning("Invalid app port configuration")
        valid = False
    
    # Validate logging level
    log_level = config.get("logging", {}).get("level", "").upper()
    if log_level and log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.warning(f"Invalid logging level: {log_level}")
        valid = False
    
    # Validate database configuration
    db_type = config.get("database", {}).get("type")
    if db_type == "postgres":
        postgres_config = config.get("database", {}).get("postgres", {})
        required_fields = ["host", "port", "dbname", "user", "password"]
        for field in required_fields:
            if field not in postgres_config:
                logger.warning(f"Missing required PostgreSQL configuration: {field}")
                valid = False
    
    return valid

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration with priority: env vars > config file > defaults.
    
    Args:
        config_path: Path to configuration file (optional)
        
    Returns:
        Dict[str, Any]: Complete configuration dictionary
    """
    # Start with defaults
    config = load_defaults()
    
    # Override with file config if available
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")
    
    if os.path.exists(config_path):
        file_config = load_from_file(config_path)
        deep_merge(config, file_config)
    
    # Override with environment variables
    env_config = load_from_env()
    deep_merge(config, env_config)
    
    # Validate configuration
    is_valid = validate_config(config)
    if not is_valid:
        logger.warning("Configuration has validation issues, using anyway with defaults where needed")
    
    # Set log level based on configuration
    log_level = config.get("logging", {}).get("level", "INFO").upper()
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    return config