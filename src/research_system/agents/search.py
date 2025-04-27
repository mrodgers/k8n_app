"""
Search Agent for the Research System.

This module implements a specialized FastMCP agent for search functionality,
demonstrating external API integration and LLM sampling for content extraction.
"""

import logging
import time
import uuid
import json
import requests
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
import os
from urllib.parse import urlencode

from research_system.core.server import FastMCPServer, Context
from research_system.models.db import ResearchTask, ResearchResult, default_db

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
        self.config = config or {}
        
        # Configure Brave Search API
        self.api_key = self.config.get("brave_search", {}).get("api_key") or os.getenv("BRAVE_SEARCH_API_KEY")
        self.endpoint = self.config.get("brave_search", {}).get("endpoint") or "https://api.search.brave.com/res/v1/web/search"
        self.max_results = self.config.get("brave_search", {}).get("max_results") or 10
        
        # Ensure API key is available
        if not self.api_key:
            logger.warning(f"Brave Search API key not provided for {name} agent")
        
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
            return [result.dict() for result in results]
        
        except Exception as e:
            logger.error(f"Error processing search results: {e}")
            if context:
                context.log_error(f"Error processing search results: {e}")
            raise Exception(f"Error processing search results: {e}")
    
    def extract_content_from_url(self, url: str, context: Context = None) -> str:
        """
        Extract content from a URL.
        
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
            content = response.text
            
            if context:
                context.update_progress(0.5, "Processing content")
            
            # In a real implementation, this would use an LLM to extract relevant content
            # For now, we'll just return a simplified version of the HTML content
            
            # Simple extraction logic (this would be replaced by LLM-based extraction)
            import re
            from bs4 import BeautifulSoup
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Remove blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if context:
                context.update_progress(1.0, "Content extraction completed")
            
            return text
        
        except Exception as e:
            error_msg = f"Error extracting content from {url}: {e}"
            logger.error(error_msg)
            if context:
                context.log_error(error_msg)
            raise Exception(error_msg)
    
    def filter_relevant_results(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Filter search results based on relevance to the query.
        
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
        
        # In a real implementation, this would use an LLM to score relevance
        # For now, we'll use a simple keyword matching approach
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
        
        logger.info(f"Filtered {len(search_results)} results to {len(filtered_results)}")
        
        # Return as dictionaries
        return [result.dict() for result in filtered_results]
    
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
        return [result.dict() for result in search_results]
    
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
                result_dicts.append(result.dict())
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
