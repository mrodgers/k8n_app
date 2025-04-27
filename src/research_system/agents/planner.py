"""
Planner Agent for the Research System.

This module implements a specialized FastMCP agent for research planning.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from research_system.core.server import FastMCPServer, Context
from research_system.models.db import ResearchTask, ResearchResult, default_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchPlan(BaseModel):
    """Model representing a research plan."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    status: str = "draft"  # draft, approved, in_progress, completed

class PlannerAgent:
    """
    Planner agent for the research system.
    
    This agent is responsible for creating and managing research plans.
    """
    
    def __init__(self, name: str = "planner", server: Optional[FastMCPServer] = None,
                db=default_db):
        """
        Initialize the planner agent.
        
        Args:
            name: The name of the agent.
            server: Optional FastMCP server to register tools with.
            db: Database instance for storing tasks and results.
        """
        self.name = name
        self.server = server
        self.db = db
        self.plans = {}  # In-memory storage for plans
        
        if server:
            self.register_tools()
        
        logger.info(f"Planner agent '{name}' initialized")
    
    def register_tools(self):
        """Register tools with the FastMCP server."""
        self.server.register_tool(
            name="create_research_task",
            tool_func=self.create_research_task,
            description="Create a new research task"
        )
        
        self.server.register_tool(
            name="create_research_plan",
            tool_func=self.create_research_plan,
            description="Create a research plan for a task"
        )
        
        self.server.register_tool(
            name="get_research_plan",
            tool_func=self.get_research_plan,
            description="Get a research plan by ID"
        )
        
        self.server.register_tool(
            name="update_research_plan",
            tool_func=self.update_research_plan,
            description="Update a research plan"
        )
        
        self.server.register_tool(
            name="list_research_tasks",
            tool_func=self.list_research_tasks,
            description="List research tasks"
        )
        
        logger.info(f"Registered planner tools with server: {self.server.name}")
    
    def create_research_task(self, title: str, description: str, tags: List[str] = None,
                           assigned_to: str = None) -> Dict:
        """
        Create a new research task.
        
        Args:
            title: The title of the task.
            description: The description of the task.
            tags: Optional list of tags for the task.
            assigned_to: Optional name of the agent assigned to the task.
            
        Returns:
            A dictionary representation of the created task.
        """
        task_id = str(uuid.uuid4())
        task = ResearchTask(
            id=task_id,
            title=title,
            description=description,
            tags=tags or [],
            assigned_to=assigned_to
        )
        self.db.create_task(task)
        logger.info(f"Created research task: {task.id} - {task.title}")
        return task.to_dict()
    
    def create_research_plan(self, task_id: str, steps: List[Dict[str, Any]] = None) -> Dict:
        """
        Create a research plan for a task.
        
        Args:
            task_id: The ID of the task to create a plan for.
            steps: Optional list of steps for the plan.
            
        Returns:
            A dictionary representation of the created plan.
            
        Raises:
            ValueError: If the task does not exist.
        """
        # Check if the task exists
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        
        plan = ResearchPlan(
            task_id=task_id,
            steps=steps or []
        )
        
        # Store the plan in memory
        self.plans[plan.id] = plan
        
        # Update the task to reflect that a plan has been created
        task.metadata["has_plan"] = True
        task.metadata["plan_id"] = plan.id
        self.db.update_task(task)
        
        logger.info(f"Created research plan: {plan.id} for task: {task.id}")
        return plan.dict()
    
    def get_research_plan(self, plan_id: str) -> Dict:
        """
        Get a research plan by ID.
        
        Args:
            plan_id: The ID of the plan.
            
        Returns:
            A dictionary representation of the plan.
            
        Raises:
            ValueError: If the plan does not exist.
        """
        if plan_id not in self.plans:
            raise ValueError(f"Plan not found: {plan_id}")
        
        return self.plans[plan_id].dict()
    
    def update_research_plan(self, plan_id: str, steps: List[Dict[str, Any]] = None,
                           status: str = None) -> Dict:
        """
        Update a research plan.
        
        Args:
            plan_id: The ID of the plan to update.
            steps: Optional new list of steps for the plan.
            status: Optional new status for the plan.
            
        Returns:
            A dictionary representation of the updated plan.
            
        Raises:
            ValueError: If the plan does not exist.
        """
        if plan_id not in self.plans:
            raise ValueError(f"Plan not found: {plan_id}")
        
        plan = self.plans[plan_id]
        
        if steps is not None:
            plan.steps = steps
        
        if status is not None:
            plan.status = status
        
        plan.updated_at = time.time()
        
        logger.info(f"Updated research plan: {plan.id}")
        return plan.dict()
    
    def list_research_tasks(self, status: Optional[str] = None, assigned_to: Optional[str] = None,
                          tag: Optional[str] = None) -> List[Dict]:
        """
        List research tasks, optionally filtered by status, assignment, or tag.
        
        Args:
            status: Optional status filter.
            assigned_to: Optional assignment filter.
            tag: Optional tag filter.
            
        Returns:
            A list of dictionary representations of tasks matching the filters.
        """
        tasks = self.db.list_tasks(status=status, assigned_to=assigned_to, tag=tag)
        return [task.to_dict() for task in tasks]
    
    def generate_plan_for_task(self, task_id: str, context: Context = None) -> Dict:
        """
        Generate a research plan for a task.
        
        This method would typically involve calling an LLM to generate a structured
        research plan based on the task description. For simplicity, this implementation
        creates a basic plan with predefined steps.
        
        Args:
            task_id: The ID of the task to generate a plan for.
            context: Optional context for tracking progress.
            
        Returns:
            A dictionary representation of the generated plan.
            
        Raises:
            ValueError: If the task does not exist.
        """
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        
        # Update context if provided
        if context:
            context.update_progress(0.1, "Generating research plan")
        
        # In a real implementation, this would call an LLM to generate a plan
        # For now, we'll create a simple template plan
        steps = [
            {
                "id": 1,
                "type": "search",
                "name": "Initial Information Gathering",
                "description": f"Gather initial information about: {task.title}",
                "status": "pending"
            },
            {
                "id": 2,
                "type": "analysis",
                "name": "Information Analysis",
                "description": "Analyze the gathered information",
                "status": "pending",
                "depends_on": [1]
            },
            {
                "id": 3,
                "type": "synthesis",
                "name": "Create Initial Draft",
                "description": "Synthesize the analyzed information into an initial draft",
                "status": "pending",
                "depends_on": [2]
            },
            {
                "id": 4,
                "type": "review",
                "name": "Review and Refinement",
                "description": "Review the draft and refine as needed",
                "status": "pending",
                "depends_on": [3]
            },
            {
                "id": 5,
                "type": "finalization",
                "name": "Finalize Research",
                "description": "Finalize the research and prepare for delivery",
                "status": "pending",
                "depends_on": [4]
            }
        ]
        
        # Update context if provided
        if context:
            context.update_progress(0.9, "Research plan generated")
        
        # Create the plan
        plan = self.create_research_plan(task_id, steps)
        
        # Update context if provided
        if context:
            context.update_progress(1.0, "Research plan creation completed")
        
        logger.info(f"Generated research plan for task: {task.id}")
        return plan

# Create a default planner agent instance
default_planner = PlannerAgent()
