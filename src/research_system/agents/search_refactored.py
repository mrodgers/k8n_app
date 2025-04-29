"""
Search Agent for the Research System (Refactored).

This module implements a simplified search agent that uses dependency injection
for services and provides capabilities through a standard interface.
"""

import logging
import time
import uuid
import json
import requests
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from research_system.models.db import ResearchTask, ResearchResult, default_db
from research_system.services.llm_service import LLMService, default_llm_service
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
    relevant content from search results. It uses the LLM service for
    content extraction and relevance ranking.
    """
    
    def __init__(self, db=default_db, llm_service=default_llm_service, config: Dict = None):
        """
        Initialize the search agent.
        
        Args:
            db: Database instance for storing tasks and results.
            llm_service: LLM service for content extraction and relevance ranking.
            config: Optional configuration dictionary.
        """
        self.name = "search"  # Fixed name for registry identification
        self.db = db
        self.llm_service = llm_service
        
        # Load configuration if not provided
        if config is None:
            config = load_config()
        self.config = config
        
        # Configure Brave Search API from configuration
        brave_config = self.config.get("brave_search", {})
        self.api_key = brave_config.get("api_key")
        self.endpoint = brave_config.get("endpoint", "https://api.search.brave.com/res/v1/web/search")
        self.max_results = brave_config.get("max_results", 10)
        
        # Ensure API key is available
        if not self.api_key:
            logger.warning(f"Brave Search API key not provided for search agent")
        
        # Store queries and results in memory
        self.queries = {}
        self.results = {}
        
        logger.info(f"Search agent initialized")
    
    def get_capabilities(self) -> List[str]:
        """
        Get a list of capabilities provided by this agent.
        
        Returns:
            List of capability names.
        """
        return [
            "execute_search",
            "extract_content",
            "filter_results",
            "rank_results",
            "create_search_query"
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
            "execute_search": self.execute_search,
            "extract_content": self.extract_content_from_url,
            "filter_results": self.filter_relevant_results,
            "rank_results": self.rank_results_by_relevance,
            "create_search_query": self.create_search_query
        }
        
        if name not in capabilities:
            raise ValueError(f"Capability '{name}' not found in search agent")
        
        return capabilities[name](**kwargs)
    
    def create_search_query(self, task_id: str, query: str, max_results: int = None) -> Dict:
        """
        Create a new search query.
        
        Args:
            task_id: The ID of the associated task.
            query: The search query string.
            max_results: Optional maximum number of results to return.
            
        Returns:
            A dictionary representation of the created query.
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
        return search_query.model_dump()
    
    def execute_search(self, task_id: str, query: str, max_results: int = None) -> List[Dict]:
        """
        Execute a search query and return results.
        
        Args:
            task_id: The ID of the task associated with the search.
            query: The search query string.
            max_results: Optional maximum number of results to return.
            
        Returns:
            A list of dictionaries representing search results.
            
        Raises:
            Exception: If the API request fails.
        """
        # Create a search query
        search_query = self.create_search_query(
            task_id=task_id,
            query=query,
            max_results=max_results
        )
        
        # Prepare the API request
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": search_query["max_results"]
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
        
        # Parse the response
        try:
            data = response.json()
            web_results = data.get("web", {}).get("results", [])
            
            # Process the results
            results = []
            for i, result in enumerate(web_results):
                search_result = SearchResult(
                    query_id=search_query["id"],
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
                results.append(search_result.model_dump())
            
            # Store the results in the database
            self.store_search_results(task_id, results)
            
            logger.info(f"Found {len(results)} results for query: {search_query['id']}")
            
            # Return the results as dictionaries
            return results
        
        except Exception as e:
            logger.error(f"Error processing search results: {e}")
            raise Exception(f"Error processing search results: {e}")
    
    def extract_content_from_url(self, url: str) -> str:
        """
        Extract content from a URL.
        
        This method fetches content from a URL and uses an LLM to extract and summarize
        relevant information.
        
        Args:
            url: The URL to extract content from.
            
        Returns:
            The extracted content as a string.
            
        Raises:
            Exception: If the request fails or content extraction fails.
        """
        try:
            # Fetch the URL content
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"Failed to fetch content from {url}: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Get the content
            html_content = response.text
            
            # Parse HTML with BeautifulSoup
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
            
            # Use LLM service to extract relevant content
            extracted_content = self.llm_service.extract_content_from_text(cleaned_text)
            
            return extracted_content
            
        except Exception as e:
            error_msg = f"Error extracting content from {url}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def filter_relevant_results(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Filter search results based on relevance to the query.
        
        This method uses the LLM service to evaluate and filter search results for
        relevance to the original query.
        
        Args:
            results: List of search result dictionaries.
            query: The original search query.
            
        Returns:
            A filtered list of search result dictionaries.
        """
        if not results:
            return []
        
        # Use LLM service to rank results
        ranked_results = self.llm_service.rank_search_results(results, query)
        
        return ranked_results
    
    def rank_results_by_relevance(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Rank search results by relevance to the query.
        
        This is an alias for filter_relevant_results for backward compatibility.
        
        Args:
            results: List of search results.
            query: The original search query.
            
        Returns:
            A ranked list of search result dictionaries.
        """
        return self.filter_relevant_results(results, query)
    
    def store_search_results(self, task_id: str, results: List[Dict]) -> None:
        """
        Store search results in the database.
        
        Args:
            task_id: The ID of the task associated with the results.
            results: List of search results.
        """
        # Create a research result
        result_id = str(uuid.uuid4())
        research_result = ResearchResult(
            id=result_id,
            task_id=task_id,
            content=json.dumps(results),
            format="json",
            created_by=self.name,
            tags=["search", "raw"],
            metadata={
                "result_count": len(results),
                "timestamp": time.time()
            }
        )
        
        # Store in the database
        self.db.create_result(research_result)
        logger.info(f"Stored {len(results)} search results as result: {result_id}")


# Create a default search agent instance
default_search = SearchAgent()