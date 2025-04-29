"""
Search Agent for the Research System.

This module implements a specialized FastMCP agent for search functionality,
integrating external search APIs and leveraging Ollama LLMs for content
extraction, result filtering, and relevance ranking.
"""

import logging
import time
import uuid
import json
import requests
import asyncio
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import os
from urllib.parse import urlencode

from research_system.core.server import FastMCPServer, Context
from research_system.models.db import ResearchTask, ResearchResult, default_db
from research_system.llm import create_ollama_client
from research_system.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchQuery(BaseModel):
    """Model representing a search query."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    query: str
    max_results: int = 10
    created_at: float = Field(default_factory=time.time)

class SearchResult(BaseModel):
    """Model representing a search result."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str
    title: str
    url: str
    snippet: str
    source: str = "web"  # web, academic, etc.
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchAgent:
    """
    Search agent for the research system.
    
    This agent is responsible for executing search queries and extracting
    relevant content from search results using LLMs.
    """
    
    def __init__(self, name: str = "search", server: Optional[FastMCPServer] = None,
                db=default_db, config: Dict = None):
        """
        Initialize the search agent.
        
        Args:
            name: The name of the agent.
            server: Optional FastMCP server to register tools with.
            db: Database instance for storing tasks and results.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.server = server
        self.db = db
        
        # Load configuration if not provided
        if config is None:
            config = load_config()
        self.config = config
        
        # Configure Brave Search API from centralized config
        brave_config = self.config.get("brave_search", {})
        self.api_key = brave_config.get("api_key")
        self.endpoint = brave_config.get("endpoint", "https://api.search.brave.com/res/v1/web/search")
        self.max_results = brave_config.get("max_results", 10)
        
        # Ensure API key is available
        if not self.api_key:
            logger.warning(f"Brave Search API key not provided for {name} agent")
        
        # LLM configuration from centralized config
        llm_config = self.config.get("llm", {})
        self.use_llm = llm_config.get("enabled", True)
        self.ollama_model = llm_config.get("model", "gemma3:1b")
        
        # Initialize LLM client if enabled
        self.llm_client = None
        if self.use_llm:
            try:
                self.llm_client = create_ollama_client(
                    async_client=False,
                    base_url=llm_config.get("url"),
                    timeout=llm_config.get("timeout", 120)
                )
                logger.info(f"LLM client initialized for {name} agent using model: {self.ollama_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client for {name} agent: {e}")
                logger.warning("The agent will fall back to rule-based processing")
                self.use_llm = False
        
        # Store queries and results
        self.queries = {}
        self.results = {}
        
        if server:
            self.register_tools()
        
        logger.info(f"Search agent '{name}' initialized")
    
    def register_tools(self):
        """Register tools with the FastMCP server."""
        self.server.register_tool(
            name="execute_search",
            tool_func=self.execute_search,
            description="Execute a search query"
        )
        
        self.server.register_tool(
            name="extract_content",
            tool_func=self.extract_content_from_url,
            description="Extract content from a URL"
        )
        
        self.server.register_tool(
            name="filter_results",
            tool_func=self.filter_relevant_results,
            description="Filter relevant search results"
        )
        
        logger.info(f"Registered search tools with server: {self.server.name}")
    
    def create_search_query(self, task_id: str, query: str, max_results: int = None) -> SearchQuery:
        """
        Create a new search query.
        
        Args:
            task_id: The ID of the associated task.
            query: The search query string.
            max_results: Optional maximum number of results to return.
            
        Returns:
            A SearchQuery object.
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        search_query = SearchQuery(
            task_id=task_id,
            query=query,
            max_results=max_results or self.max_results
        )
        
        # Store the query
        self.queries[search_query.id] = search_query
        
        logger.info(f"Created search query: {search_query.id} for task: {task_id}")
        return search_query
    
    def execute_search(self, task_id: str, query: str, max_results: int = None, 
                      context: Context = None) -> List[Dict]:
        """
        Execute a search query and return results.
        
        Args:
            task_id: The ID of the task associated with the search.
            query: The search query string.
            max_results: Optional maximum number of results to return.
            context: Optional context for tracking progress.
            
        Returns:
            A list of dictionaries representing search results.
            
        Raises:
            Exception: If the API request fails.
        """
        if context:
            context.update_progress(0.1, "Creating search query")
        
        # Create a search query
        search_query = self.create_search_query(
            task_id=task_id,
            query=query,
            max_results=max_results
        )
        
        if context:
            context.update_progress(0.3, "Executing search request")
        
        # Prepare the API request
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": search_query.max_results
        }
        
        # Execute the request with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.endpoint,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    break
                
                if response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                
                # Handle other errors
                logger.error(f"API error: {response.status_code} - {response.text}")
                raise Exception(f"API error: {response.status_code} - {response.text}")
            
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to execute search after {max_retries} attempts: {e}")
                
                time.sleep(retry_delay)
                retry_delay *= 2
        
        if context:
            context.update_progress(0.6, "Processing search results")
        
        # Parse the response
        try:
            data = response.json()
            web_results = data.get("web", {}).get("results", [])
            
            # Process the results
            results = []
            for i, result in enumerate(web_results):
                search_result = SearchResult(
                    query_id=search_query.id,
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("description", ""),
                    metadata={
                        "position": i + 1,
                        "extra_snippets": result.get("extra_snippets", []),
                        "additional_urls": result.get("additional_urls", [])
                    }
                )
                
                # Store the result
                self.results[search_result.id] = search_result
                results.append(search_result)
            
            logger.info(f"Found {len(results)} results for query: {search_query.id}")
            
            if context:
                context.update_progress(1.0, "Search completed")
            
            # Return the results as dictionaries
            return [result.model_dump() for result in results]
        
        except Exception as e:
            logger.error(f"Error processing search results: {e}")
            if context:
                context.log_error(f"Error processing search results: {e}")
            raise Exception(f"Error processing search results: {e}")
    
    def extract_content_from_url(self, url: str, context: Context = None) -> str:
        """
        Extract content from a URL.
        
        This method fetches content from a URL and uses an LLM to extract and summarize
        relevant information, or falls back to simple HTML parsing if LLM is unavailable.
        
        Args:
            url: The URL to extract content from.
            context: Optional context for tracking progress.
            
        Returns:
            The extracted content as a string.
            
        Raises:
            Exception: If the request fails or content extraction fails.
        """
        if context:
            context.update_progress(0.1, f"Fetching content from URL: {url}")
        
        try:
            # Fetch the URL content
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"Failed to fetch content from {url}: {response.status_code}"
                logger.error(error_msg)
                if context:
                    context.log_error(error_msg)
                raise Exception(error_msg)
            
            # Get the content
            html_content = response.text
            
            if context:
                context.update_progress(0.3, "Parsing HTML content")
            
            # Parse HTML with BeautifulSoup (needed for both LLM and non-LLM paths)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Extract basic text
            raw_text = soup.get_text()
            
            # Clean up the text
            import re
            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in raw_text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Remove blank lines
            cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate if too long (to avoid overwhelming the LLM)
            MAX_TEXT_LENGTH = 12000
            if len(cleaned_text) > MAX_TEXT_LENGTH:
                cleaned_text = cleaned_text[:MAX_TEXT_LENGTH] + "...[content truncated]"
            
            if context:
                context.update_progress(0.5, "Extracting relevant content")
            
            # Use LLM if available, otherwise return the cleaned text
            if self.use_llm and self.llm_client:
                try:
                    # Create prompts for the LLM
                    system_prompt = """
                    You are a content extraction assistant. Your job is to extract and summarize
                    the most relevant information from web pages. Focus on identifying the main
                    content while removing navigation elements, advertisements, footers, and other
                    non-essential parts.
                    
                    Your summary should:
                    1. Identify the main topic or purpose of the page
                    2. Extract key facts, claims, or arguments
                    3. Preserve any important statistics, quotes, or references
                    4. Be well-structured and organized by themes or topics
                    5. Be comprehensive but concise (around 500-1000 words)
                    """
                    
                    user_prompt = f"""
                    Extract and summarize the relevant content from this web page:
                    
                    URL: {url}
                    
                    RAW CONTENT:
                    {cleaned_text[:8000]}
                    """  # Truncate further for user prompt
                    
                    if context:
                        context.update_progress(0.6, "Querying LLM for content extraction")
                    
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
                    extracted_content = response.get("message", {}).get("content", "")
                    
                    if not extracted_content or len(extracted_content) < 100:
                        logger.warning("LLM returned insufficient content, falling back to basic extraction")
                        extracted_content = cleaned_text
                    else:
                        logger.info(f"Successfully extracted content from {url} using LLM")
                    
                    if context:
                        context.update_progress(1.0, "Content extraction completed")
                    
                    return extracted_content
                    
                except Exception as e:
                    logger.error(f"Error extracting content with LLM: {e}")
                    if context:
                        context.log_error(f"Error using LLM for extraction, falling back to basic extraction: {e}")
                    return cleaned_text
            else:
                # Basic extraction without LLM
                if context:
                    context.update_progress(1.0, "Basic content extraction completed")
                return cleaned_text
            
        except Exception as e:
            error_msg = f"Error extracting content from {url}: {e}"
            logger.error(error_msg)
            if context:
                context.log_error(error_msg)
            raise Exception(error_msg)
    
    def filter_relevant_results(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Filter search results based on relevance to the query.
        
        This method uses an LLM to evaluate and filter search results for
        relevance to the original query, or falls back to keyword matching
        if LLM is unavailable.
        
        Args:
            results: List of search result dictionaries.
            query: The original search query.
            
        Returns:
            A filtered list of search result dictionaries.
        """
        if not results:
            return []
        
        # Convert results to SearchResult objects if they're dictionaries
        search_results = []
        for result in results:
            if isinstance(result, dict):
                search_results.append(SearchResult(**result))
            else:
                search_results.append(result)
        
        # Use LLM if available, otherwise use keyword matching
        if self.use_llm and self.llm_client:
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
                for i, result in enumerate(search_results):
                    results_text += f"""
                    Result #{i+1}:
                    Title: {result.title}
                    Snippet: {result.snippet}
                    URL: {result.url}
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
                
                # Parse the JSON response
                import json
                import re
                
                # Try to extract JSON from the response
                json_match = re.search(r'\[\s*{.*}\s*\]', generated_content, re.DOTALL)
                if json_match:
                    evaluations = json.loads(json_match.group(0))
                else:
                    # Try alternative extraction if the response isn't valid JSON
                    logger.warning("Failed to parse LLM response as JSON, trying alternative extraction")
                    # Fall back to simple relevance extraction
                    evaluations = []
                    pattern = r'Result #(\d+).*?relevance_score.*?(\d+\.\d+)'
                    matches = re.finditer(pattern, generated_content, re.DOTALL)
                    for match in matches:
                        try:
                            result_id = int(match.group(1))
                            score = float(match.group(2))
                            evaluations.append({"result_id": result_id, "relevance_score": score})
                        except (ValueError, IndexError):
                            continue
                
                # If we still don't have valid evaluations, fall back to keyword matching
                if not evaluations:
                    logger.warning("Failed to extract relevance evaluations, falling back to keyword matching")
                    return self._filter_by_keywords(search_results, query)
                
                # Apply the scores to the results
                for eval_item in evaluations:
                    try:
                        result_id = eval_item.get("result_id")
                        if result_id and 1 <= result_id <= len(search_results):
                            search_results[result_id-1].relevance_score = eval_item.get("relevance_score", 0.0)
                            search_results[result_id-1].metadata["justification"] = eval_item.get("justification", "")
                    except Exception as e:
                        logger.error(f"Error processing evaluation item: {e}")
                
                # Filter based on score threshold
                filtered_results = [r for r in search_results if r.relevance_score > 0.5]
                
                # Sort by relevance score
                filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)
                
                logger.info(f"Filtered {len(search_results)} results to {len(filtered_results)} using LLM")
                
                # Return as dictionaries
                return [result.model_dump() for result in filtered_results]
                
            except Exception as e:
                logger.error(f"Error filtering with LLM: {e}")
                # Fall back to keyword matching
                return self._filter_by_keywords(search_results, query)
        else:
            # Fall back to keyword matching
            return self._filter_by_keywords(search_results, query)
    
    def _filter_by_keywords(self, search_results: List[SearchResult], query: str) -> List[Dict]:
        """
        Filter search results using simple keyword matching.
        
        Args:
            search_results: List of SearchResult objects.
            query: The original search query.
            
        Returns:
            A filtered list of search result dictionaries.
        """
        # Use simple keyword matching approach
        keywords = query.lower().split()
        
        filtered_results = []
        for result in search_results:
            # Check title and snippet for keywords
            text = (result.title + " " + result.snippet).lower()
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in text)
            
            # Set relevance score based on matches
            result.relevance_score = matches / len(keywords) if keywords else 0
            
            # Include if score is above threshold
            if result.relevance_score > 0.3:  # Arbitrary threshold
                filtered_results.append(result)
        
        # Sort by relevance score
        filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Filtered {len(search_results)} results to {len(filtered_results)} using keyword matching")
        
        # Return as dictionaries
        return [result.model_dump() for result in filtered_results]
    
    def rank_results_by_relevance(self, results: List[Union[Dict, SearchResult]], query: str) -> List[Dict]:
        """
        Rank search results by relevance to the query.
        
        Args:
            results: List of search results.
            query: The original search query.
            
        Returns:
            A ranked list of search result dictionaries.
        """
        # Convert results to SearchResult objects if they're dictionaries
        search_results = []
        for result in results:
            if isinstance(result, dict):
                search_results.append(SearchResult(**result))
            else:
                search_results.append(result)
        
        # In a real implementation, this would use an LLM to score relevance
        # For now, we'll use a simple keyword matching approach
        keywords = query.lower().split()
        
        for result in search_results:
            # Check title and snippet for keywords
            text = (result.title + " " + result.snippet).lower()
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in text)
            
            # Set relevance score based on matches
            result.relevance_score = matches / len(keywords) if keywords else 0
        
        # Sort by relevance score
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return as dictionaries
        return [result.model_dump() for result in search_results]
    
    def extract_citations(self, results: List[Union[Dict, SearchResult]]) -> List[str]:
        """
        Extract citations from search results.
        
        Args:
            results: List of search results.
            
        Returns:
            A list of formatted citation strings.
        """
        # Convert results to SearchResult objects if they're dictionaries
        search_results = []
        for result in results:
            if isinstance(result, dict):
                search_results.append(SearchResult(**result))
            else:
                search_results.append(result)
        
        citations = []
        for result in search_results:
            # Format basic citation
            citation = f"{result.title}. Retrieved from {result.url}"
            citations.append(citation)
        
        return citations
    
    def store_search_results(self, task_id: str, results: List[Union[Dict, SearchResult]]) -> None:
        """
        Store search results in the database.
        
        Args:
            task_id: The ID of the task associated with the results.
            results: List of search results.
        """
        # Convert results to dictionaries if they're SearchResult objects
        result_dicts = []
        for result in results:
            if isinstance(result, SearchResult):
                result_dicts.append(result.model_dump())
            else:
                result_dicts.append(result)
        
        # Create a research result
        result_id = str(uuid.uuid4())
        research_result = ResearchResult(
            id=result_id,
            task_id=task_id,
            content=json.dumps(result_dicts),
            format="json",
            created_by=self.name,
            tags=["search", "raw"],
            metadata={
                "result_count": len(result_dicts),
                "timestamp": time.time()
            }
        )
        
        # Store in the database
        self.db.create_result(research_result)
        logger.info(f"Stored {len(result_dicts)} search results as result: {result_id}")

# Create a default search agent instance
default_search = SearchAgent()
