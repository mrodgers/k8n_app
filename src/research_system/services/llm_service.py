"""
LLM Service for the Research System.

This module provides a centralized service for interacting with LLMs,
abstracting away the details of different LLM providers and models.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union, Callable
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Large Language Models.
    
    This service abstracts away the details of different LLM providers
    and models, providing a unified interface for text generation,
    chat completions, and structured data extraction.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the LLM service.
        
        Args:
            config: Configuration dictionary containing LLM settings.
                   If not provided, will be loaded from the central config.
        """
        # Import here to avoid circular imports
        from research_system.config import load_config
        
        # Load configuration if not provided
        if config is None:
            config = load_config()
        
        # Extract LLM configuration
        llm_config = config.get("llm", {})
        self.enabled = llm_config.get("enabled", True)
        self.default_model = llm_config.get("model", "gemma3:1b")
        self.timeout = llm_config.get("timeout", 120)
        self.api_url = llm_config.get("url")
        
        # Initialize clients
        self.ollama_client = None
        
        # Try to initialize the LLM client if enabled
        if self.enabled:
            self._init_client()
    
    def _init_client(self):
        """Initialize the LLM client based on configuration."""
        try:
            # Import client creation function
            from research_system.llm import create_ollama_client
            
            # Initialize Ollama client
            self.ollama_client = create_ollama_client(
                async_client=False,
                base_url=self.api_url,
                timeout=self.timeout
            )
            logger.info(f"Initialized Ollama client with model {self.default_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.enabled = False
    
    def is_available(self) -> bool:
        """
        Check if the LLM service is available.
        
        Returns:
            bool: True if the service is available, False otherwise.
        """
        return self.enabled and self.ollama_client is not None
    
    def generate_text(self, prompt: str, model: str = None, **params) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The prompt to generate text from.
            model: Optional model name to use (defaults to configured model).
            **params: Additional parameters to pass to the LLM.
            
        Returns:
            str: The generated text.
            
        Raises:
            RuntimeError: If the LLM service is not available.
        """
        if not self.is_available():
            raise RuntimeError("LLM service is not available")
        
        try:
            model = model or self.default_model
            
            response = self.ollama_client.generate(
                model=model,
                prompt=prompt,
                stream=False,
                **params
            )
            
            return response.get("response", "")
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    def generate_chat_completion(self, messages: List[Dict[str, str]], 
                                model: str = None, **params) -> Dict[str, Any]:
        """
        Generate a chat completion using the LLM.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys.
            model: Optional model name to use (defaults to configured model).
            **params: Additional parameters to pass to the LLM.
            
        Returns:
            Dict: The chat completion response.
            
        Raises:
            RuntimeError: If the LLM service is not available.
        """
        if not self.is_available():
            raise RuntimeError("LLM service is not available")
        
        try:
            model = model or self.default_model
            
            response = self.ollama_client.generate_chat_completion(
                model=model,
                messages=messages,
                stream=False,
                **params
            )
            
            return response
        except Exception as e:
            logger.error(f"Error generating chat completion: {e}")
            raise
    
    def extract_structured_data(self, prompt: str, schema: Dict[str, Any],
                              system_prompt: str = None, model: str = None,
                              max_retries: int = 3) -> Dict[str, Any]:
        """
        Extract structured data from text using the LLM.
        
        Args:
            prompt: The prompt to extract data from.
            schema: The JSON schema to extract.
            system_prompt: Optional system prompt to use.
            model: Optional model name to use (defaults to configured model).
            max_retries: Maximum number of retries for extracting valid JSON.
            
        Returns:
            Dict: The extracted structured data.
            
        Raises:
            RuntimeError: If the LLM service is not available.
            ValueError: If the LLM could not extract valid structured data.
        """
        if not self.is_available():
            raise RuntimeError("LLM service is not available")
        
        model = model or self.default_model
        
        # If no system prompt is provided, generate one based on the schema
        if not system_prompt:
            system_prompt = f"""
            You are a structured data extraction assistant. Extract the requested information
            from the user's input and return it as a valid JSON object with the following schema:
            
            {json.dumps(schema, indent=2)}
            
            Your response must be valid, parseable JSON with no additional text. 
            All keys in the schema must be included in your response.
            """
        
        user_prompt = f"""
        Extract the structured data from the following text. Return ONLY valid JSON with no additional text:
        
        {prompt}
        """
        
        # Try to extract structured data with retries
        for attempt in range(max_retries):
            try:
                response = self.generate_chat_completion(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                content = response.get("message", {}).get("content", "")
                
                # Try to extract JSON from the response
                json_match = re.search(r'(\{|\[).*(\}|\])', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    return data
                
                # If no JSON was found, try again with a more explicit prompt
                user_prompt = f"""
                The previous response was not valid JSON. Please extract the structured data
                and return ONLY valid JSON with no explanations or additional text:
                
                {prompt}
                """
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to extract structured data (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Could not extract structured data after {max_retries} attempts")
    
    def generate_embeddings(self, texts: List[str], model: str = None) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of texts to generate embeddings for.
            model: Optional model name to use (defaults to configured model).
            
        Returns:
            List of embeddings (lists of floats).
            
        Raises:
            RuntimeError: If the LLM service is not available.
        """
        if not self.is_available():
            raise RuntimeError("LLM service is not available")
        
        try:
            model = model or self.default_model
            
            # Ollama embeddings endpoint expects a single string
            # For multiple texts, we need to call it multiple times
            embeddings = []
            
            for text in texts:
                response = self.ollama_client.generate_embeddings(
                    model=model,
                    prompt=text
                )
                
                if "embedding" in response:
                    embeddings.append(response["embedding"])
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def create_research_plan(self, title: str, description: str, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Create a research plan using the LLM.
        
        Args:
            title: The title of the research task.
            description: The description of the research task.
            tags: Optional tags for the research task.
            
        Returns:
            List of plan steps, each as a dictionary.
            
        Raises:
            RuntimeError: If the LLM service is not available.
        """
        if not self.is_available():
            return self._create_template_plan(title, description)
        
        try:
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
            
            Title: {title}
            Description: {description}
            Tags: {', '.join(tags) if tags else 'None'}
            
            Return the plan as a JSON array of steps, with each step having the properties:
            id, type, name, description, status, and optionally depends_on.
            """
            
            # Extract a structured plan
            schema = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "type": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "status": {"type": "string"},
                        "depends_on": {"type": "array", "items": {"type": "integer"}}
                    },
                    "required": ["id", "type", "name", "description", "status"]
                }
            }
            
            steps = self.extract_structured_data(
                prompt=user_prompt,
                schema=schema,
                system_prompt=system_prompt
            )
            
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
            return steps
            
        except Exception as e:
            logger.error(f"Error creating research plan with LLM: {e}")
            return self._create_template_plan(title, description)
    
    def _create_template_plan(self, title: str, description: str) -> List[Dict[str, Any]]:
        """
        Create a template-based research plan when LLM is unavailable.
        
        Args:
            title: The title of the research task.
            description: The description of the research task.
            
        Returns:
            List of plan steps, each as a dictionary.
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
    
    def rank_search_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rank search results by relevance using the LLM.
        
        Args:
            results: List of search result dictionaries.
            query: The original search query.
            
        Returns:
            List of search results with relevance scores, sorted by relevance.
        """
        if not self.is_available() or not results:
            return self._keyword_rank_results(results, query)
        
        try:
            # Create a system prompt for the LLM
            system_prompt = """
            You are a search result evaluation assistant. Your job is to analyze search results
            and determine if they are relevant to the original search query.
            
            For each result, provide:
            1. A relevance score from 0.0 to 1.0 (where 1.0 is highly relevant)
            2. A brief justification for this score
            
            Be critical and precise - many search results may be technically related but not 
            truly relevant to answering the original query.
            """
            
            # Format the results for the LLM
            results_text = ""
            for i, result in enumerate(results):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                url = result.get("url", "")
                results_text += f"""
                Result #{i+1}:
                Title: {title}
                Snippet: {snippet}
                URL: {url}
                """
            
            user_prompt = f"""
            Original search query: "{query}"
            
            Evaluate the following search results for relevance to this query:
            
            {results_text}
            
            Return your evaluation as a JSON array with objects containing:
            - result_id: the # of the result
            - relevance_score: a float between 0.0 and 1.0
            - justification: a brief explanation for this score
            
            Only return the JSON array, nothing else.
            """
            
            # Extract structured data
            schema = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "integer"},
                        "relevance_score": {"type": "number"},
                        "justification": {"type": "string"}
                    },
                    "required": ["result_id", "relevance_score"]
                }
            }
            
            try:
                evaluations = self.extract_structured_data(
                    prompt=user_prompt,
                    schema=schema,
                    system_prompt=system_prompt
                )
                
                # Apply the scores to the results
                for eval_item in evaluations:
                    result_id = eval_item.get("result_id")
                    if result_id and 1 <= result_id <= len(results):
                        results[result_id-1]["relevance_score"] = eval_item.get("relevance_score", 0.0)
                        if "justification" in eval_item:
                            results[result_id-1].setdefault("metadata", {})["justification"] = eval_item["justification"]
                
                # Filter based on score threshold and sort
                filtered_results = [r for r in results if r.get("relevance_score", 0) > 0.5]
                filtered_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
                
                return filtered_results
            except Exception as e:
                logger.error(f"Error extracting relevance data: {e}")
                return self._keyword_rank_results(results, query)
        except Exception as e:
            logger.error(f"Error ranking search results: {e}")
            return self._keyword_rank_results(results, query)
    
    def _keyword_rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rank search results using simple keyword matching when LLM is unavailable.
        
        Args:
            results: List of search result dictionaries.
            query: The original search query.
            
        Returns:
            List of search results with relevance scores, sorted by relevance.
        """
        if not results:
            return []
            
        keywords = query.lower().split()
        
        for result in results:
            # Check title and snippet for keywords
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            text = f"{title} {snippet}"
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in text)
            
            # Set relevance score based on matches
            result["relevance_score"] = matches / len(keywords) if keywords else 0
        
        # Filter based on score threshold and sort
        filtered_results = [r for r in results if r.get("relevance_score", 0) > 0.3]
        filtered_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return filtered_results
    
    def extract_content_from_text(self, text: str, max_length: int = 1000) -> str:
        """
        Extract and summarize the most relevant content from text.
        
        Args:
            text: The text to extract content from.
            max_length: The maximum length of the extracted content.
            
        Returns:
            The extracted and summarized content.
        """
        if not self.is_available() or not text:
            return text[:max_length] if text else ""
        
        try:
            # Create prompts for the LLM
            system_prompt = """
            You are a content extraction assistant. Your job is to extract and summarize
            the most relevant information from text. Focus on identifying the main
            content while removing noise and non-essential parts.
            
            Your summary should:
            1. Identify the main topic or purpose
            2. Extract key facts, claims, or arguments
            3. Preserve any important statistics, quotes, or references
            4. Be well-structured and organized by themes or topics
            5. Be comprehensive but concise
            """
            
            # Truncate text if it's very long to avoid overwhelming the LLM
            truncated_text = text
            if len(text) > 8000:
                truncated_text = text[:8000] + "...[content truncated]"
            
            user_prompt = f"""
            Extract and summarize the relevant content from this text:
            
            {truncated_text}
            """
            
            response = self.generate_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            extracted_content = response.get("message", {}).get("content", "")
            
            if not extracted_content or len(extracted_content) < 100:
                return text[:max_length] if text else ""
            
            return extracted_content
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return text[:max_length] if text else ""


# Create a default service instance
default_llm_service = LLMService()