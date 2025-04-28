"""
Research Web Interface for the Research System.

This module provides a web interface for users to create research tasks,
view results, and interact with the research system.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get templates directory
templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'templates')
templates = Jinja2Templates(directory=templates_dir)

# Create router
router = APIRouter(prefix="/research", tags=["research"])

@router.get("/", response_class=HTMLResponse)
async def research_home(request: Request):
    """Main research interface page."""
    return templates.TemplateResponse("research.html", {"request": request})

def setup_research(app):
    """Set up the research web interface by including its router in the main app."""
    app.include_router(router)
    logger.info("Research web interface setup complete")