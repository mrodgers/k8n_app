"""
Ollama Server for the Research System.

This module implements an Ollama server that implements the FastMCP protocol,
allowing the research system's agents to interact with Ollama LLMs through
a standardized interface.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
import json

from src.research_system.core.server import FastMCPServer, Context
from src.research_system.llm.ollama_client import SyncOllamaClient, OllamaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaServer:
    """
    FastMCP server for Ollama LLM integration.
    
    This server provides tools for generating completions, chat conversations,
    and embeddings using local LLM models through Ollama.
    """
    
    def __init__(self, name: str = "ollama", server: Optional[FastMCPServer] = None, 
                config: Dict = None):
        """
        Initialize the Ollama server.
        
        Args:
            name: The name of the server.
            server: Optional FastMCP server to register tools with.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.server = server
        self.config = config or {}
        
        # LLM configuration
        self.default_model = self.config.get("model") or os.environ.get("OLLAMA_DEFAULT_MODEL", "gemma3:1b")
        self.base_url = self.config.get("url") or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        self.timeout = int(self.config.get("timeout") or os.environ.get("OLLAMA_TIMEOUT", "120"))
        
        # Initialize clients (both sync and async)
        self.sync_client = SyncOllamaClient(base_url=self.base_url, timeout=self.timeout)
        self.async_client = OllamaClient(base_url=self.base_url, timeout=self.timeout)
        
        logger.info(f"Ollama server '{name}' initialized with default model: {self.default_model}")
        
        # Register tools with FastMCP server if provided
        if server:
            self.register_tools()
    
    def register_tools(self):
        """Register Ollama tools with the FastMCP server."""
        # Completion and chat tools
        self.server.register_tool(
            name="generate_completion",
            tool_func=self.generate_completion,
            description="Generate a completion for a prompt"
        )
        
        self.server.register_tool(
            name="generate_chat_completion",
            tool_func=self.generate_chat_completion,
            description="Generate a chat completion for a conversation"
        )
        
        self.server.register_tool(
            name="generate_embeddings",
            tool_func=self.generate_embeddings,
            description="Generate embeddings for text input"
        )
        
        # Higher-level task-specific tools
        self.server.register_tool(
            name="extract_content",
            tool_func=self.extract_content,
            description="Extract content from raw text"
        )
        
        self.server.register_tool(
            name="assess_relevance",
            tool_func=self.assess_relevance,
            description="Assess relevance of content to a query"
        )
        
        self.server.register_tool(
            name="generate_plan",
            tool_func=self.generate_plan,
            description="Generate a structured research plan"
        )
        
        # Model management tools
        self.server.register_tool(
            name="list_models",
            tool_func=self.list_models,
            description="List available models"
        )
        
        self.server.register_tool(
            name="preload_model",
            tool_func=self.preload_model,
            description="Preload a model into memory"
        )
        
        self.server.register_tool(
            name="pull_model",
            tool_func=self.pull_model,
            description="Pull a model from the Ollama library"
        )
        
        # Server status tools
        self.server.register_tool(
            name="get_version",
            tool_func=self.get_version,
            description="Get the Ollama server version"
        )
        
        logger.info(f"Registered Ollama tools with server: {self.server.name}")
    
    # Basic Ollama API tools
    
    def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
        context: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion for a prompt.
        
        Args:
            prompt: The prompt to generate a completion for.
            model: The name of the model to use (defaults to the server's default model).
            system: Optional system message to override the model's default.
            stream: Whether to stream the response (not implemented in MCP).
            options: Optional model parameters such as 'temperature'.
            context: Optional context for tracking progress.
            
        Returns:
            The completion result.
        """
        model = model or self.default_model
        
        if context:
            context.update_progress(0.1, f"Generating completion with model: {model}")
        
        try:
            result = self.sync_client.generate_completion(
                model=model,
                prompt=prompt,
                system=system,
                stream=False,  # MCP doesn't support streaming
                options=options
            )
            
            if context:
                context.update_progress(1.0, "Completion generated")
            
            return result
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            if context:
                context.log_error(f"Error generating completion: {e}")
            raise
    
    def generate_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Generate a chat completion for a conversation.
        
        Args:
            messages: List of message objects with 'role' and 'content'.
            model: The name of the model to use (defaults to the server's default model).
            options: Optional model parameters such as 'temperature'.
            tools: Optional list of tool specifications for function calling.
            context: Optional context for tracking progress.
            
        Returns:
            The chat completion result.
        """
        model = model or self.default_model
        
        if context:
            context.update_progress(0.1, f"Generating chat completion with model: {model}")
        
        try:
            result = self.sync_client.generate_chat_completion(
                model=model,
                messages=messages,
                stream=False,  # MCP doesn't support streaming
                options=options,
                tools=tools
            )
            
            if context:
                context.update_progress(1.0, "Chat completion generated")
            
            return result
        except Exception as e:
            logger.error(f"Error generating chat completion: {e}")
            if context:
                context.log_error(f"Error generating chat completion: {e}")
            raise
    
    def generate_embeddings(
        self,
        input_text: Union[str, List[str]],
        model: Optional[str] = None,
        context: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text input.
        
        Args:
            input_text: Text or list of texts to generate embeddings for.
            model: The name of the model to use (defaults to the server's default model).
            context: Optional context for tracking progress.
            
        Returns:
            The embedding result.
        """
        model = model or self.default_model
        
        if context:
            context.update_progress(0.1, f"Generating embeddings with model: {model}")
        
        try:
            result = self.sync_client.generate_embeddings(
                model=model,
                input_text=input_text
            )
            
            if context:
                context.update_progress(1.0, "Embeddings generated")
            
            return result
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            if context:
                context.log_error(f"Error generating embeddings: {e}")
            raise
    
    # Higher-level task-specific tools
    
    def extract_content(
        self,
        raw_text: str,
        extraction_type: str = "summary",
        max_length: int = 1000,
        model: Optional[str] = None,
        context: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Extract content from raw text using LLM.
        
        Args:
            raw_text: The raw text to extract content from.
            extraction_type: Type of extraction (summary, key_points, entities, etc.)
            max_length: Maximum length of the extracted content.
            model: The name of the model to use (defaults to the server's default model).
            context: Optional context for tracking progress.
            
        Returns:
            A dictionary containing the extracted content.
        """
        model = model or self.default_model
        
        if context:
            context.update_progress(0.1, f"Extracting content with model: {model}")
        
        # Truncate input if needed
        if len(raw_text) > 12000:
            raw_text = raw_text[:12000] + "...[content truncated]"
        
        # Create a system prompt based on extraction type
        system_prompt = """
        You are a content extraction assistant. Your job is to extract and structure
        information from raw text. Focus on identifying the main content while removing 
        non-essential parts.
        """
        
        if extraction_type == "summary":
            system_prompt += """
            Your task is to create a concise summary that:
            1. Identifies the main topic or purpose of the content
            2. Captures the most important points
            3. Preserves important statistics, quotes, or references
            4. Is comprehensive but concise
            """
        elif extraction_type == "key_points":
            system_prompt += """
            Your task is to extract the key points as a list that:
            1. Identifies the main claims or arguments
            2. Extracts important facts or statements
            3. Is focused and precise
            4. Uses bullet points for clarity
            """
        elif extraction_type == "entities":
            system_prompt += """
            Your task is to extract named entities that:
            1. Identifies people, organizations, locations, dates, and other named entities
            2. Briefly describes each entity's role or relevance
            3. Is structured as a list of entities with descriptions
            """
        
        user_prompt = f"""
        Extract {extraction_type} from the following text:
        
        {raw_text}
        
        Keep your response under {max_length} words.
        """
        
        try:
            response = self.sync_client.generate_chat_completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=False
            )
            
            # Extract the generated content
            content = response.get("message", {}).get("content", "")
            
            if context:
                context.update_progress(1.0, "Content extraction completed")
            
            return {
                "content": content,
                "extraction_type": extraction_type,
                "model": model,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            if context:
                context.log_error(f"Error extracting content: {e}")
            raise
    
    def assess_relevance(
        self,
        content: str,
        query: str,
        model: Optional[str] = None,
        context: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Assess the relevance of content to a query.
        
        Args:
            content: The content to assess.
            query: The query to assess relevance against.
            model: The name of the model to use (defaults to the server's default model).
            context: Optional context for tracking progress.
            
        Returns:
            A dictionary containing the relevance assessment.
        """
        model = model or self.default_model
        
        if context:
            context.update_progress(0.1, f"Assessing relevance with model: {model}")
        
        # Truncate input if needed
        if len(content) > 8000:
            content = content[:8000] + "...[content truncated]"
        
        system_prompt = """
        You are a relevance assessment assistant. Your job is to evaluate how relevant
        a piece of content is to a given query. Provide:
        
        1. A relevance score from 0.0 to 1.0 (where 1.0 is highly relevant)
        2. A brief justification for this score
        3. Key matching points between the query and content
        
        Be critical and precise - content may be technically related but not truly
        relevant to answering the original query.
        """
        
        user_prompt = f"""
        Query: "{query}"
        
        Content to assess:
        {content}
        
        Provide your assessment as a JSON object with the following fields:
        - relevance_score: a float between 0.0 and 1.0
        - justification: a brief explanation for this score
        - key_matches: a list of key points from the content that match the query
        
        Return only the JSON object, nothing else.
        """
        
        try:
            response = self.sync_client.generate_chat_completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=False
            )
            
            # Extract the generated content
            generated_content = response.get("message", {}).get("content", "")
            
            # Try to parse the JSON response
            try:
                # Find JSON-like content in the response
                import json
                import re
                
                json_match = re.search(r'\{.*\}', generated_content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    # Fallback if JSON parsing fails
                    result = {
                        "relevance_score": 0.5,
                        "justification": "Failed to parse LLM response as JSON",
                        "key_matches": []
                    }
            except Exception as e:
                logger.error(f"Error parsing relevance assessment: {e}")
                result = {
                    "relevance_score": 0.5,
                    "justification": f"Error parsing LLM response: {str(e)}",
                    "key_matches": []
                }
            
            # Add metadata to the result
            result.update({
                "query": query,
                "model": model,
                "timestamp": time.time()
            })
            
            if context:
                context.update_progress(1.0, "Relevance assessment completed")
            
            return result
        except Exception as e:
            logger.error(f"Error assessing relevance: {e}")
            if context:
                context.log_error(f"Error assessing relevance: {e}")
            raise
    
    def generate_plan(
        self,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        num_steps: int = 7,
        model: Optional[str] = None,
        context: Optional[Context] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured research plan.
        
        Args:
            title: The title of the research task.
            description: The description of the research task.
            tags: Optional list of tags for the task.
            num_steps: Number of steps to include in the plan.
            model: The name of the model to use (defaults to the server's default model).
            context: Optional context for tracking progress.
            
        Returns:
            A dictionary containing the generated plan.
        """
        model = model or self.default_model
        
        if context:
            context.update_progress(0.1, f"Generating plan with model: {model}")
        
        system_prompt = f"""
        You are a research planner assistant. Your job is to create a detailed research plan
        for the given task. The plan should include {num_steps} steps, with each step containing:
        - A sequential ID number
        - A type (search, analysis, synthesis, review, interview, experiment, etc.)
        - A descriptive name
        - A detailed description of what to do
        - The status (always set to "pending")
        - Dependencies on previous steps (if applicable)
        
        Create a comprehensive, logical sequence of steps that would result in a thorough
        research outcome for the given task.
        """
        
        user_prompt = f"""
        Create a research plan for the following task:
        
        Title: {title}
        Description: {description}
        Tags: {', '.join(tags) if tags else 'None'}
        
        Return the plan as a JSON array of steps, with each step having the properties:
        id, type, name, description, status, and optionally depends_on.
        """
        
        try:
            response = self.sync_client.generate_chat_completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=False
            )
            
            # Extract the generated content
            generated_content = response.get("message", {}).get("content", "")
            
            # Parse the JSON response
            import json
            import re
            
            # Try to extract JSON from the response
            json_match = re.search(r'\[\s*{.*}\s*\]', generated_content, re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group(0))
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
            
            # If we still don't have valid steps, create a template plan
            if not steps:
                logger.warning("Failed to parse LLM response, falling back to template plan")
                steps = self._create_template_plan(title, description)
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
            
            if context:
                context.update_progress(1.0, "Plan generation completed")
            
            return {
                "title": title,
                "description": description,
                "tags": tags or [],
                "steps": steps,
                "model": model,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            if context:
                context.log_error(f"Error generating plan: {e}")
            raise
    
    def _create_template_plan(self, title: str, description: str) -> List[Dict[str, Any]]:
        """
        Create a template-based research plan.
        
        Args:
            title: The research task title.
            description: The research task description.
            
        Returns:
            A list of plan steps.
        """
        return [
            {
                "id": 1,
                "type": "search",
                "name": "Initial Information Gathering",
                "description": f"Gather initial information about: {title}",
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
    
    # Model management tools
    
    def list_models(self) -> Dict[str, Any]:
        """
        List models available on the Ollama server.
        
        Returns:
            A dictionary containing a list of available models.
        """
        try:
            return self.sync_client.list_models()
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise
    
    def preload_model(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Preload a model into memory.
        
        Args:
            model: The name of the model to preload.
            
        Returns:
            A dictionary containing the result of the operation.
        """
        model = model or self.default_model
        
        try:
            success = self.sync_client.preload_model(model)
            return {
                "model": model,
                "preloaded": success,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error preloading model: {e}")
            raise
    
    def pull_model(self, model: str) -> Dict[str, Any]:
        """
        Pull a model from the Ollama library.
        
        Args:
            model: The name of the model to pull.
            
        Returns:
            A dictionary containing the result of the pull operation.
        """
        try:
            return self.sync_client.pull_model(model)
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            raise
    
    # Server status tools
    
    def get_version(self) -> Dict[str, Any]:
        """
        Get the Ollama server version.
        
        Returns:
            A dictionary containing the version information.
        """
        try:
            version_info = self.sync_client.get_version()
            version_info.update({
                "default_model": self.default_model,
                "base_url": self.base_url,
                "timeout": self.timeout
            })
            return version_info
        except Exception as e:
            logger.error(f"Error getting version: {e}")
            raise

# Create a default Ollama server instance
default_ollama_server = OllamaServer()