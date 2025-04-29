"""
Planner Agent for the Research System.

This module implements a specialized FastMCP agent for research planning,
leveraging LLMs through the Ollama integration.
"""

import logging
import time
import uuid
import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from research_system.core.server import FastMCPServer, Context
from research_system.models.db import ResearchTask, ResearchResult, default_db
from research_system.llm import create_ollama_client
from research_system.interfaces import AgentInterface
from research_system.exceptions import ResourceNotFoundError, TaskNotFoundError, LLMServiceError

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

class PlannerAgent(AgentInterface):
    """
    Planner agent for the research system.
    
    This agent is responsible for creating and managing research plans.
    It implements the AgentInterface to provide standardized capability
    discovery and execution.
    """
    
    def __init__(self, name: str = "planner", server: Optional[FastMCPServer] = None,
                db=default_db, config: Dict = None):
        """
        Initialize the planner agent.
        
        Args:
            name: The name of the agent.
            server: Optional FastMCP server to register tools with.
            db: Database instance for storing tasks and results.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.server = server
        self.db = db
        self.config = config or {}
        self.plans = {}  # In-memory storage for plans
        
        # LLM configuration
        self.use_llm = self.config.get("use_llm", True)
        self.ollama_model = self.config.get("ollama_model") or os.environ.get("PLANNER_LLM_MODEL", "gemma3:1b")
        
        # Initialize LLM client if enabled
        self.llm_client = None
        if self.use_llm:
            try:
                self.llm_client = create_ollama_client(
                    async_client=False,
                    base_url=self.config.get("ollama_url") or os.environ.get("OLLAMA_URL"),
                    timeout=self.config.get("ollama_timeout", 120)
                )
                logger.info(f"LLM client initialized for {name} agent using model: {self.ollama_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client for {name} agent: {e}")
                logger.warning("The agent will fall back to template-based planning")
                self.use_llm = False
        
        if server:
            self.register_tools()
        
        # Define agent capabilities
        self._capabilities = [
            "create_research_task",
            "create_research_plan",
            "get_research_plan",
            "update_research_plan",
            "list_research_tasks",
            "generate_plan_for_task"
        ]
        
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
            TaskNotFoundError: If the task does not exist.
        """
        # Check if the task exists
        task = self.db.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(
                message=f"Task not found: {task_id}",
                details={"task_id": task_id}
            )
        
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
        return plan.model_dump()
    
    def get_research_plan(self, plan_id: str) -> Dict:
        """
        Get a research plan by ID.
        
        Args:
            plan_id: The ID of the plan.
            
        Returns:
            A dictionary representation of the plan.
            
        Raises:
            ResourceNotFoundError: If the plan does not exist.
        """
        if plan_id not in self.plans:
            raise ResourceNotFoundError(
                message=f"Plan not found: {plan_id}",
                details={"plan_id": plan_id}
            )
        
        return self.plans[plan_id].model_dump()
    
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
            ResourceNotFoundError: If the plan does not exist.
        """
        if plan_id not in self.plans:
            raise ResourceNotFoundError(
                message=f"Plan not found: {plan_id}",
                details={"plan_id": plan_id}
            )
        
        plan = self.plans[plan_id]
        
        if steps is not None:
            plan.steps = steps
        
        if status is not None:
            plan.status = status
        
        plan.updated_at = time.time()
        
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
    
    def generate_plan_for_task(self, task_id: str, context: Context = None) -> Dict:
        """
        Generate a research plan for a task.
        
        This method uses an LLM to generate a structured research plan based on 
        the task description, or falls back to a template-based approach if LLM 
        is unavailable.
        
        Args:
            task_id: The ID of the task to generate a plan for.
            context: Optional context for tracking progress.
            
        Returns:
            A dictionary representation of the generated plan.
            
        Raises:
            TaskNotFoundError: If the task does not exist.
            LLMServiceError: If there's an error with the LLM service that prevents fallback.
        """
        task = self.db.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(
                message=f"Task not found: {task_id}",
                details={"task_id": task_id}
            )
        
        # Update context if provided
        if context:
            context.update_progress(0.1, "Generating research plan")
        
        # Use LLM to generate the plan if available
        steps = []
        if self.use_llm and self.llm_client:
            try:
                if context:
                    context.update_progress(0.2, "Querying LLM for research plan")
                
                # Create a system prompt for the LLM
                system_prompt = """
                You are a research planner assistant. Your job is to create a detailed research plan
                for the given task. The plan should include 5-7 steps, with each step containing:
                - A sequential ID number
                - A type (search, analysis, synthesis, review, interview, experiment, etc.)
                - A descriptive name
                - A detailed description of what to do
                - The status (always set to "pending")
                - Dependencies on previous steps (if applicable)
                
                Create a comprehensive, logical sequence of steps that would result in a thorough
                research outcome for the given task.
                """
                
                # Create a user prompt with the task details
                user_prompt = f"""
                Create a research plan for the following task:
                
                Title: {task.title}
                Description: {task.description}
                Tags: {', '.join(task.tags) if task.tags else 'None'}
                
                Return the plan as a JSON array of steps, with each step having the properties:
                id, type, name, description, status, and optionally depends_on.
                """
                
                # Generate completion with Ollama
                response = self.llm_client.generate_chat_completion(
                    model=self.ollama_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    stream=False
                )
                
                # Extract the generated content
                generated_content = response.get("message", {}).get("content", "")
                
                if context:
                    context.update_progress(0.5, "Processing LLM response")
                
                # Parse the JSON response - handle different formats the LLM might return
                import json
                import re
                
                # Try to extract JSON from the response
                json_match = re.search(r'\[\s*{.*}\s*\]', generated_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    steps = json.loads(json_str)
                else:
                    # Try to extract each step individually if JSON parsing fails
                    steps = []
                    step_matches = re.finditer(r'{[\s\S]*?}', generated_content)
                    for i, match in enumerate(step_matches):
                        try:
                            step = json.loads(match.group(0))
                            if isinstance(step, dict) and "id" in step and "type" in step:
                                steps.append(step)
                        except json.JSONDecodeError:
                            continue
                
                # If we still don't have valid steps, fall back to template
                if not steps:
                    logger.warning("Failed to parse LLM response, falling back to template plan")
                    steps = self._create_template_plan(task)
                else:
                    # Ensure all required fields are present and format is consistent
                    for i, step in enumerate(steps):
                        # Ensure ID is an integer
                        if "id" not in step or not isinstance(step["id"], int):
                            step["id"] = i + 1
                        # Ensure status is "pending"
                        step["status"] = "pending"
                        # Ensure depends_on is a list if present
                        if "depends_on" in step and not isinstance(step["depends_on"], list):
                            step["depends_on"] = [step["depends_on"]] if step["depends_on"] else []
                
                logger.info(f"Generated {len(steps)} research plan steps using LLM")
                
            except Exception as e:
                error_msg = f"Error generating plan with LLM: {e}"
                logger.error(error_msg)
                if context:
                    context.log_error(error_msg)
                # Log the error but don't throw an exception since we can fall back to template
                logger.warning("Falling back to template-based plan generation")
                steps = self._create_template_plan(task)
        else:
            # Fall back to template-based planning
            steps = self._create_template_plan(task)
        
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
    
    def get_capabilities(self) -> List[str]:
        """
        Get a list of capabilities provided by this agent.
        
        Returns:
            List of capability names as strings
        """
        return self._capabilities
    
    def execute_capability(self, name: str, **kwargs) -> Any:
        """
        Execute a specific capability by name.
        
        Args:
            name: The name of the capability to execute
            **kwargs: Parameters for the capability
            
        Returns:
            Result of the capability execution
            
        Raises:
            ResourceNotFoundError: If the agent doesn't provide the requested capability
            TaskNotFoundError: If a task-related operation fails because the task doesn't exist
            LLMServiceError: If there's an error with the LLM service
        """
        if name not in self._capabilities:
            logger.error(f"Requested capability '{name}' not supported by {self.name} agent")
            raise ResourceNotFoundError(
                message=f"Capability not supported: {name}",
                details={"agent": self.name, "available_capabilities": self._capabilities}
            )
            
        # Map capability names to their corresponding methods
        capability_mapping = {
            "create_research_task": self.create_research_task,
            "create_research_plan": self.create_research_plan,
            "get_research_plan": self.get_research_plan,
            "update_research_plan": self.update_research_plan,
            "list_research_tasks": self.list_research_tasks,
            "generate_plan_for_task": self.generate_plan_for_task
        }
        
        # Execute the capability with the provided parameters
        try:
            return capability_mapping[name](**kwargs)
        except TypeError as e:
            # Provide a more helpful error message if the parameters don't match
            logger.error(f"Error executing capability '{name}': {e}")
            raise ResourceNotFoundError(
                message=f"Invalid parameters for capability '{name}'",
                details={"error": str(e), "capability": name}
            )
        except TaskNotFoundError as e:
            # Re-raise task not found exceptions
            logger.error(f"Task not found while executing capability '{name}': {e}")
            raise
        except LLMServiceError as e:
            # Re-raise LLM service errors
            logger.error(f"LLM service error while executing capability '{name}': {e}")
            raise
        except Exception as e:
            # Catch any other exceptions and provide context
            logger.error(f"Error executing capability '{name}': {e}")
            raise
    
    def _create_template_plan(self, task: ResearchTask) -> List[Dict[str, Any]]:
        """
        Create a template-based research plan.
        
        Args:
            task: The research task.
            
        Returns:
            A list of plan steps.
        """
        return [
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

# Create a default planner agent instance
default_planner = PlannerAgent()
