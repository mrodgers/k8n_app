"""
Workflow Orchestrator for the Research System.

This module provides workflow orchestration capabilities, combining
multiple agent capabilities into cohesive research workflows.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional

from research_system.core.registry import Registry, default_registry
from research_system.models.db import default_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Workflow orchestrator for the research system.
    
    This class orchestrates workflows across different agents,
    providing high-level workflows that combine multiple capabilities.
    """
    
    def __init__(self, registry: Registry = default_registry, db=default_db):
        """
        Initialize the orchestrator.
        
        Args:
            registry: The capability registry to use.
            db: The database instance to use.
        """
        self.registry = registry
        self.db = db
        self._register_workflows()
        logger.info("Orchestrator initialized")
    
    def _register_workflows(self):
        """Register standard workflows with the registry."""
        self.registry.register_workflow(
            name="basic_research",
            workflow_func=self.execute_basic_research,
            description="Execute a basic research workflow with planning and search"
        )
        
        self.registry.register_workflow(
            name="search_and_summarize",
            workflow_func=self.execute_search_and_summarize,
            description="Search for information and summarize the results"
        )
        
        logger.info("Registered standard workflows")
    
    def execute_basic_research(self, title: str, description: str, query: str) -> Dict[str, Any]:
        """
        Execute a basic research workflow.
        
        This workflow:
        1. Creates a research task
        2. Generates a research plan for the task
        3. Executes a search query
        4. Ranks and filters search results
        
        Args:
            title: The title of the research task.
            description: The description of the research task.
            query: The search query to execute.
            
        Returns:
            A dictionary containing workflow results.
        """
        start_time = time.time()
        logger.info(f"Starting basic research workflow: {title}")
        
        # Create a research task
        task = self.registry.execute_capability(
            "create_research_task",
            title=title,
            description=description,
            tags=["auto", "workflow"]
        )
        task_id = task["id"]
        
        # Generate a research plan
        plan = self.registry.execute_capability(
            "generate_plan_for_task",
            task_id=task_id
        )
        
        # Execute search query
        search_results = self.registry.execute_capability(
            "execute_search",
            task_id=task_id,
            query=query
        )
        
        # Rank and filter results
        if search_results:
            filtered_results = self.registry.execute_capability(
                "filter_results",
                results=search_results,
                query=query
            )
        else:
            filtered_results = []
        
        # Store workflow result as a research result
        workflow_result = {
            "workflow": "basic_research",
            "task_id": task_id,
            "plan_id": plan.get("id"),
            "search_results_count": len(search_results),
            "filtered_results_count": len(filtered_results),
            "duration_seconds": time.time() - start_time
        }
        
        result_id = str(time.time())
        self.db.create_result({
            "id": result_id,
            "task_id": task_id,
            "content": json.dumps(workflow_result),
            "format": "json",
            "status": "final",
            "created_by": "orchestrator",
            "tags": ["workflow", "summary"],
            "metadata": {
                "workflow": "basic_research",
                "query": query
            }
        })
        
        logger.info(f"Completed basic research workflow for task: {task_id}")
        
        return {
            "task": task,
            "plan": plan,
            "raw_results": search_results,
            "filtered_results": filtered_results,
            "summary": workflow_result
        }
    
    def execute_search_and_summarize(self, query: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a search and summarize workflow.
        
        This workflow:
        1. Creates a task if none is provided
        2. Executes a search query
        3. Filters search results
        4. Extracts content from top results
        
        Args:
            query: The search query to execute.
            task_id: Optional task ID to associate with the search.
            
        Returns:
            A dictionary containing workflow results.
        """
        start_time = time.time()
        logger.info(f"Starting search and summarize workflow: {query}")
        
        # Create a task if none is provided
        if task_id is None:
            task = self.registry.execute_capability(
                "create_research_task",
                title=f"Search: {query}",
                description=f"Auto-generated task for search query: {query}",
                tags=["auto", "search"]
            )
            task_id = task["id"]
        
        # Execute search query
        search_results = self.registry.execute_capability(
            "execute_search",
            task_id=task_id,
            query=query
        )
        
        # Filter search results
        if search_results:
            filtered_results = self.registry.execute_capability(
                "filter_results",
                results=search_results,
                query=query
            )
        else:
            filtered_results = []
        
        # Extract content from top results (up to 3)
        extracted_contents = []
        for result in filtered_results[:3]:
            try:
                content = self.registry.execute_capability(
                    "extract_content",
                    url=result["url"]
                )
                
                extracted_contents.append({
                    "title": result["title"],
                    "url": result["url"],
                    "content": content,
                    "relevance_score": result.get("relevance_score", 0)
                })
            except Exception as e:
                logger.error(f"Error extracting content from {result['url']}: {e}")
        
        # Store workflow result
        workflow_result = {
            "workflow": "search_and_summarize",
            "task_id": task_id,
            "query": query,
            "search_results_count": len(search_results),
            "filtered_results_count": len(filtered_results),
            "extracted_contents_count": len(extracted_contents),
            "duration_seconds": time.time() - start_time
        }
        
        logger.info(f"Completed search and summarize workflow for query: {query}")
        
        return {
            "task_id": task_id,
            "query": query,
            "filtered_results": filtered_results,
            "extracted_contents": extracted_contents,
            "summary": workflow_result
        }


# Create a default orchestrator instance
default_orchestrator = Orchestrator()