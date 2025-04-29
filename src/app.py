"""
Main application entry point for the Research System.

This module is the entry point for the FastAPI application,
using the application factory to create and configure the app.
"""

import os
import logging
import uvicorn
from research_system.app_factory import create_app
from research_system.config import load_config, is_development, get_env_name

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration first
config = load_config()

# Set log level from configuration
log_level = config.get("logging", {}).get("level", "INFO").upper()
logging.getLogger().setLevel(getattr(logging, log_level))

# Log environment information
env_name = get_env_name()
logger.info(f"Starting Research System in {env_name} environment")

# Create the FastAPI app with the loaded config
app = create_app(config=config)

if __name__ == '__main__':
    # Get port from config (which already includes env var overrides)
    port = config.get("app", {}).get("port", 8181)
    
    # Configure uvicorn based on environment
    uvicorn_kwargs = {
        "host": "0.0.0.0",
        "port": port,
    }
    
    # Add development-specific options
    if is_development():
        uvicorn_kwargs.update({
            "reload": True,
            "log_level": log_level.lower(),
        })
    
    # Start the FastAPI app
    logger.info(f"Starting Research System API on port {port}")
    uvicorn.run("app:app", **uvicorn_kwargs)