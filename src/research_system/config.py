"""
Configuration management for the Research System.

This module centralizes all configuration loading and validation, supporting:
- Default configuration
- File-based configuration (YAML)
- Environment variable overrides
- Configuration validation
- Dotenv support for local development

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
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ValidationError

# Try to import dotenv for local development
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load .env file if available
if DOTENV_AVAILABLE:
    env_file = os.getenv("ENV_FILE", ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from {env_file}")

# Configuration schema models for validation
class DatabaseConfig(BaseModel):
    """Database configuration schema."""
    type: str = "tinydb"
    path: Optional[str] = "data/research.json"
    use_postgres: bool = False
    postgres: Optional[Dict[str, Any]] = Field(default_factory=dict)
    connection_string: Optional[str] = None

class LLMConfig(BaseModel):
    """LLM configuration schema."""
    enabled: bool = True
    model: str = "gemma3:1b"
    timeout: int = 120
    url: Optional[str] = None

class LoggingConfig(BaseModel):
    """Logging configuration schema."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    output: Optional[str] = None

class AppConfig(BaseModel):
    """Application configuration schema."""
    port: int = 8181
    max_workers: int = 4
    cors: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "allow_origins": ["*"],
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }
    )

class BraveSearchConfig(BaseModel):
    """Brave Search API configuration schema."""
    api_key: Optional[str] = None
    max_results: int = 10
    endpoint: str = "https://api.search.brave.com/res/v1/web/search"

class RootConfig(BaseModel):
    """Root configuration schema."""
    app: AppConfig = Field(default_factory=AppConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    environment: str = "development"
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    brave_search: BraveSearchConfig = Field(default_factory=BraveSearchConfig)

def load_defaults() -> Dict[str, Any]:
    """Load default configuration values."""
    # Create default config using the pydantic models
    return RootConfig().model_dump()

def load_from_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Failed to load configuration from {config_path}: {e}")
        return {}

def load_from_env() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Environment variable naming convention:
    - RESEARCH_APP_PORT: App port
    - RESEARCH_APP_MAX_WORKERS: App max workers
    - RESEARCH_LOG_LEVEL: Logging level
    - RESEARCH_ENV_MODE: Environment mode
    - RESEARCH_DB_TYPE: Database type (tinydb or postgres)
    - RESEARCH_DB_PATH: TinyDB database path
    - RESEARCH_DB_USE_POSTGRES: Use PostgreSQL (true/false)
    - RESEARCH_DB_URL: PostgreSQL connection URL
    - RESEARCH_DB_HOST: PostgreSQL host
    - RESEARCH_DB_PORT: PostgreSQL port
    - RESEARCH_DB_NAME: PostgreSQL database name
    - RESEARCH_DB_USER: PostgreSQL username
    - RESEARCH_DB_PASSWORD: PostgreSQL password
    - RESEARCH_LLM_ENABLED: Enable LLM (true/false)
    - RESEARCH_LLM_MODEL: LLM model name
    - RESEARCH_LLM_URL: LLM API URL
    - RESEARCH_LLM_TIMEOUT: LLM timeout in seconds
    - RESEARCH_BRAVE_API_KEY: Brave Search API key
    """
    config = {}
    
    # App configuration
    if os.getenv("RESEARCH_APP_PORT") or os.getenv("PORT"):
        _ensure_dict_path(config, ["app"])
        config["app"]["port"] = int(os.getenv("RESEARCH_APP_PORT") or os.getenv("PORT", 8181))
    
    if os.getenv("RESEARCH_APP_MAX_WORKERS") or os.getenv("MAX_WORKERS"):
        _ensure_dict_path(config, ["app"])
        config["app"]["max_workers"] = int(os.getenv("RESEARCH_APP_MAX_WORKERS") or os.getenv("MAX_WORKERS", 4))
    
    # Logging configuration
    if os.getenv("RESEARCH_LOG_LEVEL") or os.getenv("LOG_LEVEL"):
        _ensure_dict_path(config, ["logging"])
        config["logging"]["level"] = os.getenv("RESEARCH_LOG_LEVEL") or os.getenv("LOG_LEVEL", "INFO")
    
    # Environment setting
    if os.getenv("RESEARCH_ENV_MODE") or os.getenv("ENV_MODE"):
        config["environment"] = os.getenv("RESEARCH_ENV_MODE") or os.getenv("ENV_MODE", "development")
    
    # Database configuration
    if os.getenv("RESEARCH_DB_TYPE"):
        _ensure_dict_path(config, ["database"])
        config["database"]["type"] = os.getenv("RESEARCH_DB_TYPE")
    
    if os.getenv("RESEARCH_DB_PATH") or os.getenv("DB_TINYDB_PATH"):
        _ensure_dict_path(config, ["database"])
        config["database"]["path"] = os.getenv("RESEARCH_DB_PATH") or os.getenv("DB_TINYDB_PATH", "data/research.json")
    
    if os.getenv("RESEARCH_DB_USE_POSTGRES") or os.getenv("USE_POSTGRES") or os.getenv("DB_USE_POSTGRES"):
        _ensure_dict_path(config, ["database"])
        use_postgres = os.getenv("RESEARCH_DB_USE_POSTGRES") or os.getenv("USE_POSTGRES") or os.getenv("DB_USE_POSTGRES", "false")
        config["database"]["use_postgres"] = use_postgres.lower() in ("true", "1", "yes", "y")
    
    # PostgreSQL connection URL (highest priority for DB config)
    if os.getenv("RESEARCH_DB_URL") or os.getenv("DATABASE_URL"):
        _ensure_dict_path(config, ["database"])
        config["database"]["connection_string"] = os.getenv("RESEARCH_DB_URL") or os.getenv("DATABASE_URL")
        config["database"]["use_postgres"] = True
    
    # Individual PostgreSQL settings
    if os.getenv("RESEARCH_DB_HOST") or os.getenv("DB_POSTGRES_HOST") or os.getenv("POSTGRES_SERVICE_HOST"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["host"] = (
            os.getenv("RESEARCH_DB_HOST") or 
            os.getenv("DB_POSTGRES_HOST") or 
            os.getenv("POSTGRES_SERVICE_HOST", "localhost")
        )
    
    if os.getenv("RESEARCH_DB_PORT") or os.getenv("DB_POSTGRES_PORT") or os.getenv("POSTGRES_SERVICE_PORT"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["port"] = int(
            os.getenv("RESEARCH_DB_PORT") or 
            os.getenv("DB_POSTGRES_PORT") or 
            os.getenv("POSTGRES_SERVICE_PORT", 5432)
        )
    
    if os.getenv("RESEARCH_DB_NAME") or os.getenv("DB_POSTGRES_DBNAME") or os.getenv("POSTGRES_DB"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["dbname"] = (
            os.getenv("RESEARCH_DB_NAME") or 
            os.getenv("DB_POSTGRES_DBNAME") or 
            os.getenv("POSTGRES_DB", "research")
        )
    
    if os.getenv("RESEARCH_DB_USER") or os.getenv("DB_POSTGRES_USER") or os.getenv("POSTGRES_USER"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["user"] = (
            os.getenv("RESEARCH_DB_USER") or 
            os.getenv("DB_POSTGRES_USER") or 
            os.getenv("POSTGRES_USER", "postgres")
        )
    
    if os.getenv("RESEARCH_DB_PASSWORD") or os.getenv("DB_POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASSWORD"):
        _ensure_dict_path(config, ["database", "postgres"])
        config["database"]["postgres"]["password"] = (
            os.getenv("RESEARCH_DB_PASSWORD") or 
            os.getenv("DB_POSTGRES_PASSWORD") or 
            os.getenv("POSTGRES_PASSWORD", "postgres")
        )
    
    # LLM configuration
    if os.getenv("RESEARCH_LLM_ENABLED"):
        _ensure_dict_path(config, ["llm"])
        config["llm"]["enabled"] = os.getenv("RESEARCH_LLM_ENABLED").lower() in ("true", "1", "yes", "y")
    
    if os.getenv("RESEARCH_LLM_MODEL") or os.getenv("OLLAMA_MODEL"):
        _ensure_dict_path(config, ["llm"])
        config["llm"]["model"] = os.getenv("RESEARCH_LLM_MODEL") or os.getenv("OLLAMA_MODEL", "gemma3:1b")
    
    if os.getenv("RESEARCH_LLM_URL") or os.getenv("OLLAMA_URL"):
        _ensure_dict_path(config, ["llm"])
        config["llm"]["url"] = os.getenv("RESEARCH_LLM_URL") or os.getenv("OLLAMA_URL")
    
    if os.getenv("RESEARCH_LLM_TIMEOUT"):
        _ensure_dict_path(config, ["llm"])
        config["llm"]["timeout"] = int(os.getenv("RESEARCH_LLM_TIMEOUT", 120))
    
    # Brave Search configuration
    if os.getenv("RESEARCH_BRAVE_API_KEY") or os.getenv("BRAVE_SEARCH_API_KEY"):
        _ensure_dict_path(config, ["brave_search"])
        config["brave_search"]["api_key"] = os.getenv("RESEARCH_BRAVE_API_KEY") or os.getenv("BRAVE_SEARCH_API_KEY")
    
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
    Validate configuration using Pydantic models.
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Validate using Pydantic model
        RootConfig(**config)
        return True
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

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

def get_database_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract database-specific configuration.
    
    Args:
        config: The complete configuration dictionary
        
    Returns:
        Dict[str, Any]: Database-specific configuration
    """
    db_config = config.get("database", {})
    
    # If PostgreSQL is enabled and no connection string is provided, build one
    if db_config.get("use_postgres") and not db_config.get("connection_string"):
        pg_config = db_config.get("postgres", {})
        host = pg_config.get("host", "localhost")
        port = pg_config.get("port", 5432)
        dbname = pg_config.get("dbname", "research")
        user = pg_config.get("user", "postgres")
        password = pg_config.get("password", "postgres")
        
        # Build and store connection string
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        db_config["connection_string"] = connection_string
    
    return db_config

def get_env_name() -> str:
    """
    Get the current environment name.
    
    Returns:
        str: Environment name (development, testing, production)
    """
    return os.getenv("RESEARCH_ENV_MODE", os.getenv("ENV_MODE", "development"))

def is_development() -> bool:
    """Check if running in development environment."""
    return get_env_name().lower() in ("dev", "development", "local")

def is_testing() -> bool:
    """Check if running in testing environment."""
    return get_env_name().lower() in ("test", "testing")

def is_production() -> bool:
    """Check if running in production environment."""
    return get_env_name().lower() in ("prod", "production")