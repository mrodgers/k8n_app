"""
Main application entry point for the Research System.

This module is the entry point for the FastAPI application,
using the application factory to create and configure the app.
"""

import os
import logging
import uvicorn
from research_system.app_factory import create_app

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = create_app()

if __name__ == '__main__':
    # Get port from environment or config
    config = app.state.config
    port = int(os.getenv("PORT", config.get("app", {}).get("port", 8181)))
    
    # Start the FastAPI app
    logger.info(f"Starting Research System API on port {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)