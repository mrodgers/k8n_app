"""
Coordinator Module for the Research System.

This module contains the central component that orchestrates the entire system,
including how FastMCP servers are mounted together and how tools from different 
agents are coordinated.
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Union, Callable
import requests
from pydantic import BaseModel, Field
import json

from src.research_system.core.server import FastMCPServer, Context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Agent(BaseModel):
    """Model representing an agent in the research system."""
    name: str
    server_url: str
    description: str = ""
    tools: List[str] = Field(default_factory=list)
    
    def call_tool(self, tool_name: str, **kwargs):
        """
        Call a tool on the agent.
        
        Args:
            tool_name: The name of the tool to call.
            **kwargs: Arguments to pass to the tool.
            
        Returns:
            The result of the tool call.
            
        Raises:
            Exception: If the tool call fails.
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not available on agent '{self.name}'")
        
        url = f"{self.server_url}/tools/{tool_name}"
        try:
            response = requests.post(url, json=kwargs)
            response.raise_for_status()
            return response.json()["result"]
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}' on agent '{self.name}': {e}")
            raise

class Coordinator:
    """
    Central coordinator for the research system.
    
    This class orchestrates the entire system, connecting different agents
    and coordinating their tools to accomplish research tasks.
    """
    
    def __init__(self, name: str = "Research Coordinator"):
        """
        Initialize the coordinator.
        
        Args:
            name: The name of the coordinator.
        """
        self.name = name
        self.agents = {}
        self.workflows = {}
        logger.info(f"Coordinator '{name}' initialized")
    
    def register_agent(self, agent):
        """
        Register an agent with the coordinator.
        
        Args:
            agent: The agent to register (either Agent object or dict with agent properties).
            
        Raises:
            ValueError: If an agent with the same name is already registered.
        """
        # Convert dict to Agent if needed
        if isinstance(agent, dict):
            agent = Agent(**agent)
            
        if agent.name in self.agents:
            raise ValueError(f"Agent '{agent.name}' is already registered")
        
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def get_agent(self, name: str) -> Agent:
        """
        Get an agent by name.
        
        Args:
            name: The name of the agent.
            
        Returns:
            The agent with the specified name.
            
        Raises:
            ValueError: If no agent with the specified name is registered.
        """
        if name not in self.agents:
            raise ValueError(f"No agent named '{name}' is registered")
        
        return self.agents[name]
    
    def list_agents(self) -> List[str]:
        """
        List all registered agents.
        
        Returns:
            A list of agent names.
        """
        return list(self.agents.keys())
    
    def register_workflow(self, name: str, workflow_func: Callable, description: str = ""):
        """
        Register a workflow with the coordinator.
        
        A workflow is a function that orchestrates multiple agents to accomplish a task.
        
        Args:
            name: The name of the workflow.
            workflow_func: The function that implements the workflow.
            description: Optional description of the workflow.
            
        Raises:
            ValueError: If a workflow with the same name is already registered.
        """
        if name in self.workflows:
            raise ValueError(f"Workflow '{name}' is already registered")
        
        self.workflows[name] = {
            "function": workflow_func,
            "description": description
        }
        logger.info(f"Registered workflow: {name}")
    
    def run_workflow(self, name: str, context: Context = None, **kwargs):
        """
        Run a workflow.
        
        Args:
            name: The name of the workflow to run.
            context: Optional context for the workflow.
            **kwargs: Arguments to pass to the workflow.
            
        Returns:
            The result of the workflow.
            
        Raises:
            ValueError: If no workflow with the specified name is registered.
        """
        if name not in self.workflows:
            raise ValueError(f"No workflow named '{name}' is registered")
        
        # Create a context if one is not provided
        if context is None:
            context = Context()
        
        # Run the workflow
        workflow = self.workflows[name]["function"]
        logger.info(f"Running workflow: {name}")
        result = workflow(self, context, **kwargs)
        logger.info(f"Workflow '{name}' completed")
        return result
    
    def list_workflows(self) -> Dict[str, str]:
        """
        List all registered workflows.
        
        Returns:
            A dictionary mapping workflow names to their descriptions.
        """
        return {name: info["description"] for name, info in self.workflows.items()}
    
    def create_server(self, name: str, host: str = "0.0.0.0", port: int = 8080) -> FastMCPServer:
        """
        Create a FastMCP server and register it as an agent.
        
        Args:
            name: The name of the server.
            host: The host address to run the server on.
            port: The port to run the server on.
            
        Returns:
            The created FastMCP server.
        """
        server = FastMCPServer(name)
        
        # Register the server as an agent
        agent = Agent(
            name=name,
            server_url=f"http://{host}:{port}",
            description=f"FastMCP server: {name}"
        )
        self.register_agent(agent)
        
        return server
    
    def mount_agents(self, base_server: FastMCPServer):
        """
        Mount all agents to a base server.
        
        This makes all agent tools available through a single server interface.
        
        Args:
            base_server: The base server to mount agents to.
        """
        for agent_name, agent in self.agents.items():
            if agent_name == base_server.name:
                continue  # Skip the base server itself
            
            # For each tool in the agent, create a proxy function
            for tool_name in agent.tools:
                def proxy_tool(agent=agent, tool_name=tool_name, **kwargs):
                    """Proxy function for the agent tool."""
                    return agent.call_tool(tool_name, **kwargs)
                
                # Register the proxy tool with the base server
                base_server.register_tool(
                    name=f"{agent_name}.{tool_name}",
                    tool_func=proxy_tool,
                    description=f"Proxy for {agent_name}'s {tool_name} tool"
                )
        
        logger.info(f"Mounted all agents to server: {base_server.name}")
    
    def start_all_servers(self):
        """
        Start all servers registered with this coordinator.
        
        This method is not implemented because it would typically require
        multiprocessing or threading to run multiple servers simultaneously.
        In a production environment, servers would be deployed as separate
        processes or containers.
        """
        logger.warning("start_all_servers is not implemented")
        logger.info("In a production environment, servers would be deployed as separate processes or containers")

# Create a default coordinator instance
default_coordinator = Coordinator()
