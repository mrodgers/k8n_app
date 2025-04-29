"""
Planner Agent for the Research System (Refactored).

This module implements a simplified planner agent that uses dependency injection
for services and provides capabilities through a standard interface.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from research_system.models.db import ResearchTask, ResearchResult, default_db
from research_system.services.llm_service import LLMService, default_llm_service

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
    It uses the LLM service for generating plans and the database
    for storing tasks and results.
    """
    
    def __init__(self, db=default_db, llm_service=default_llm_service, config: Dict = None):
        """
        Initialize the planner agent.
        
        Args:
            db: Database instance for storing tasks and results.
            llm_service: LLM service for generating plans.
            config: Optional configuration dictionary.
        """
        self.name = "planner"  # Fixed name for registry identification
        self.db = db
        self.llm_service = llm_service
        self.config = config or {}
        self.plans = {}  # In-memory storage for plans
        
        logger.info(f"Planner agent initialized")
    
    def get_capabilities(self) -> List[str]:
        """
        Get a list of capabilities provided by this agent.
        
        Returns:
            List of capability names.
        """
        return [
            "create_research_task",
            "create_research_plan",
            "get_research_plan",
            "update_research_plan",
            "list_research_tasks",
            "generate_plan_for_task"
        ]
    
    def execute_capability(self, name: str, **kwargs) -> Any:
        """
        Execute a capability by name.
        
        Args:
            name: The name of the capability to execute.
            **kwargs: Arguments to pass to the capability.
            
        Returns:
            The result of the capability execution.
            
        Raises:
            ValueError: If the capability does not exist.
        """
        capabilities = {
            "create_research_task": self.create_research_task,
            "create_research_plan": self.create_research_plan,
            "get_research_plan": self.get_research_plan,
            "update_research_plan": self.update_research_plan,
            "list_research_tasks": self.list_research_tasks,
            "generate_plan_for_task": self.generate_plan_for_task
        }
        
        if name not in capabilities:
            raise ValueError(f"Capability '{name}' not found in planner agent")
        
        return capabilities[name](**kwargs)
    
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
        return task.model_dump()
    
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
        
        # Store the plan persistently as a research result
        result = ResearchResult(
            id=str(uuid.uuid4()),
            task_id=task_id,
            content=plan.model_dump_json(),
            format="json",
            status="draft",
            created_by=self.name,
            tags=["plan"],
            metadata={"plan_id": plan.id}
        )
        self.db.create_result(result)
        
        # Update the task to reflect that a plan has been created
        task.metadata["has_plan"] = True
        task.metadata["plan_id"] = plan.id
        task.metadata["result_id"] = result.id
        self.db.update_task(task)
        
        logger.info(f"Created research plan: {plan.id} for task: {task.id}")
        return plan.model_dump()
    
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
        # First check in-memory store
        if plan_id in self.plans:
            return self.plans[plan_id].model_dump()
        
        # If not found, try to restore from database
        # Get all results for tasks that might contain this plan
        tasks = self.db.list_tasks()
        for task in tasks:
            if task.metadata.get("plan_id") == plan_id:
                result_id = task.metadata.get("result_id")
                if result_id:
                    result = self.db.get_result(result_id)
                    if result and result.format == "json":
                        try:
                            import json
                            plan_data = json.loads(result.content)
                            plan = ResearchPlan(**plan_data)
                            self.plans[plan.id] = plan
                            return plan.model_dump()
                        except Exception as e:
                            logger.error(f"Error restoring plan from result: {e}")
        
        raise ValueError(f"Plan not found: {plan_id}")
    
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
        # Get the plan (this will raise ValueError if not found)
        plan_dict = self.get_research_plan(plan_id)
        plan = ResearchPlan(**plan_dict)
        
        if steps is not None:
            plan.steps = steps
        
        if status is not None:
            plan.status = status
        
        plan.updated_at = time.time()
        
        # Update in-memory storage
        self.plans[plan.id] = plan
        
        # Update in database if possible
        task = self.db.get_task(plan.task_id)
        if task and "result_id" in task.metadata:
            result = self.db.get_result(task.metadata["result_id"])
            if result:
                result.content = plan.model_dump_json()
                result.updated_at = time.time()
                self.db.update_result(result)
        
        logger.info(f"Updated research plan: {plan.id}")
        return plan.model_dump()
    
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
        return [task.model_dump() for task in tasks]
    
    def generate_plan_for_task(self, task_id: str) -> Dict:
        """
        Generate a research plan for a task.
        
        This method uses the LLM service to generate a structured research plan
        based on the task description.
        
        Args:
            task_id: The ID of the task to generate a plan for.
            
        Returns:
            A dictionary representation of the generated plan.
            
        Raises:
            ValueError: If the task does not exist.
        """
        task = self.db.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        
        # Generate steps using LLM service
        steps = self.llm_service.create_research_plan(
            title=task.title,
            description=task.description,
            tags=task.tags
        )
        
        # Create the plan
        plan = self.create_research_plan(task_id, steps)
        
        logger.info(f"Generated research plan for task: {task.id}")
        return plan


# Create a default planner agent instance
default_planner = PlannerAgent()