"""
Tests for the Search agent with LLM capabilities.

This tests the Search agent's ability to leverage LLM for content extraction,
result filtering, and relevance ranking.
"""

import pytest
import os
import json
import re
from unittest.mock import MagicMock, patch, Mock

from src.research_system.agents.search import SearchAgent, SearchResult, SearchQuery
from src.research_system.core.server import Context
from src.research_system.llm import create_ollama_client

# Skip these tests if we want to avoid LLM tests
SKIP_LLM_TESTS = os.environ.get("SKIP_LLM_TESTS", "true").lower() == "true"
SKIP_REASON = "LLM agent tests are skipped by default. Set SKIP_LLM_TESTS=false to run them."

# Mock responses for LLM
MOCK_LLM_CONTENT_EXTRACTION = {
    "message": {
        "role": "assistant",
        "content": """
        # Climate Change Effects on Coastal Cities
        
        Climate change poses significant threats to coastal cities worldwide through:
        
        1. **Sea Level Rise**: Projected to rise 2-7 feet by 2100, threatening low-lying areas.
        
        2. **Increased Storm Intensity**: More frequent and powerful hurricanes and cyclones.
        
        3. **Flooding**: Both from rising seas and increased precipitation events.
        
        4. **Saltwater Intrusion**: Contaminating freshwater supplies in coastal aquifers.
        
        Major at-risk cities include Miami, New York, Bangkok, Manila, and Rotterdam, with billions of dollars in infrastructure vulnerable to damage.
        
        Adaptation strategies include:
        - Sea walls and levees
        - Raised infrastructure
        - Restoration of natural barriers like wetlands
        - Managed retreat from highest-risk areas
        
        Economic impacts include property devaluation, insurance challenges, and strain on municipal budgets for infrastructure upgrades.
        """
    }
}

MOCK_LLM_RELEVANCE_EVALUATION = {
    "message": {
        "role": "assistant",
        "content": """
        [
            {
                "result_id": 1,
                "relevance_score": 0.92,
                "justification": "Directly addresses climate change impacts on coastal cities with specific examples"
            },
            {
                "result_id": 2,
                "relevance_score": 0.78,
                "justification": "Discusses sea level rise but only briefly mentions coastal impacts"
            },
            {
                "result_id": 3,
                "relevance_score": 0.35,
                "justification": "Primarily about climate change generally, with minimal coastal city content"
            },
            {
                "result_id": 4,
                "relevance_score": 0.85,
                "justification": "Contains detailed analysis of coastal infrastructure vulnerabilities"
            }
        ]
        """
    }
}


class MockDB:
    """Mock database for testing."""
    
    def __init__(self):
        self.tasks = {}
        self.results = {}
        self.queries = {}
    
    def create_task(self, task):
        self.tasks[task.id] = task
        return task
    
    def get_task(self, task_id):
        return self.tasks.get(task_id)
    
    def create_result(self, result):
        self.results[result.id] = result
        return result


def mock_response(*args, **kwargs):
    """Create a mock response for requests."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.text = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Climate Change and Coastal Cities</title>
    </head>
    <body>
        <header>
            <nav>Menu items</nav>
        </header>
        <main>
            <h1>Climate Change Impacts on Coastal Cities</h1>
            <p>Rising sea levels threaten coastal infrastructure.</p>
            <p>Increased storm intensity leads to more severe flooding.</p>
            <p>Many major cities are implementing adaptation strategies.</p>
        </main>
        <footer>Copyright 2023</footer>
    </body>
    </html>
    """
    return mock_resp


@pytest.mark.skipif(SKIP_LLM_TESTS, reason=SKIP_REASON)
class TestSearchAgentWithLLM:
    """Tests for the Search agent using LLM capabilities."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        return MockDB()
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock(spec=Context)
        context.update_progress = Mock()
        context.log_error = Mock()
        return context
    
    @pytest.fixture
    def sample_results(self):
        """Create sample search results."""
        return [
            SearchResult(
                id="result-1",
                query_id="query-123",
                title="Climate Change Effects on Coastal Cities",
                url="https://example.com/climate-coastal",
                snippet="Study of rising sea levels and their impact on coastal cities worldwide.",
                source="web"
            ),
            SearchResult(
                id="result-2",
                query_id="query-123",
                title="Sea Level Rise Projections",
                url="https://example.com/sea-level",
                snippet="Scientific projections of sea level rise through 2100.",
                source="web"
            ),
            SearchResult(
                id="result-3",
                query_id="query-123",
                title="Global Warming Trends",
                url="https://example.com/warming",
                snippet="Analysis of global temperature increases over the past century.",
                source="web"
            ),
            SearchResult(
                id="result-4",
                query_id="query-123",
                title="Coastal Infrastructure Vulnerabilities",
                url="https://example.com/infrastructure",
                snippet="Assessment of critical infrastructure vulnerabilities in coastal regions.",
                source="web"
            )
        ]
    
    @pytest.fixture
    def search_with_mock_llm(self, mock_db):
        """Create a search agent with a mocked LLM client."""
        with patch('src.research_system.llm.create_ollama_client') as mock_create_client:
            # Setup the mock LLM client
            mock_client = MagicMock()
            mock_client.generate_chat_completion.return_value = MOCK_LLM_CONTENT_EXTRACTION
            mock_create_client.return_value = mock_client
            
            # Create search agent with mock LLM
            search = SearchAgent(
                name="test_search", 
                db=mock_db,
                config={
                    "use_llm": True,
                    "ollama_model": "test-model"
                }
            )
            
            yield search
    
    @pytest.fixture
    def search_without_llm(self, mock_db):
        """Create a search agent with LLM disabled."""
        search = SearchAgent(
            name="test_search_no_llm", 
            db=mock_db,
            config={
                "use_llm": False
            }
        )
        return search
    
    def test_search_llm_initialization(self, search_with_mock_llm):
        """Test search agent initializes correctly with LLM client."""
        assert search_with_mock_llm.use_llm is True
        assert search_with_mock_llm.ollama_model == "test-model"
        assert search_with_mock_llm.llm_client is not None
    
    def test_search_no_llm_initialization(self, search_without_llm):
        """Test search agent initializes correctly without LLM client."""
        assert search_without_llm.use_llm is False
        assert search_without_llm.llm_client is None
    
    def test_extract_content_with_llm(self, search_with_mock_llm, mock_context):
        """Test extracting content from a URL using LLM."""
        with patch('requests.get', side_effect=mock_response):
            # Configure mock to return different responses for different prompts
            search_with_mock_llm.llm_client.generate_chat_completion.return_value = MOCK_LLM_CONTENT_EXTRACTION
            
            # Extract content
            content = search_with_mock_llm.extract_content_from_url(
                url="https://example.com/climate",
                context=mock_context
            )
            
            # Verify LLM was used for extraction
            search_with_mock_llm.llm_client.generate_chat_completion.assert_called_once()
            
            # Verify the content was extracted
            assert "Climate Change Effects on Coastal Cities" in content
            assert "Sea Level Rise" in content
            assert "Adaptation strategies" in content
    
    def test_extract_content_without_llm(self, search_without_llm, mock_context):
        """Test extracting content from a URL without using LLM."""
        with patch('requests.get', side_effect=mock_response):
            # Extract content
            content = search_without_llm.extract_content_from_url(
                url="https://example.com/climate",
                context=mock_context
            )
            
            # Verify basic extraction was used
            assert "Climate Change Impacts on Coastal Cities" in content
            assert "Rising sea levels" in content
            assert "Copyright" not in content  # Should have filtered out footer
    
    def test_filter_relevant_results_with_llm(self, search_with_mock_llm, sample_results):
        """Test filtering search results for relevance using LLM."""
        # Configure mock to return relevance evaluation
        search_with_mock_llm.llm_client.generate_chat_completion.return_value = MOCK_LLM_RELEVANCE_EVALUATION
        
        # Convert sample results to dictionaries
        result_dicts = [r.model_dump() for r in sample_results]
        
        # Filter results
        filtered = search_with_mock_llm.filter_relevant_results(
            results=result_dicts,
            query="Impact of climate change on coastal cities"
        )
        
        # Verify LLM was used for filtering
        search_with_mock_llm.llm_client.generate_chat_completion.assert_called_once()
        
        # Verify the filtering
        assert len(filtered) == 3  # Should exclude result with score 0.35
        
        # Check scores were applied
        result_1 = next((r for r in filtered if r["id"] == "result-1"), None)
        assert result_1 is not None
        assert result_1["relevance_score"] == 0.92
        assert "justification" in result_1["metadata"]
    
    def test_filter_relevant_results_without_llm(self, search_without_llm, sample_results):
        """Test filtering search results without using LLM."""
        # Convert sample results to dictionaries
        result_dicts = [r.model_dump() for r in sample_results]
        
        # Filter results
        filtered = search_without_llm.filter_relevant_results(
            results=result_dicts,
            query="coastal cities climate impacts"
        )
        
        # Verify the filtering
        assert len(filtered) > 0
        
        # First result should be the most relevant by keyword matching
        assert filtered[0]["id"] == "result-1"  # Has most keyword matches
    
    def test_llm_error_handling_in_extraction(self, search_with_mock_llm, mock_context):
        """Test search agent gracefully handles LLM errors during content extraction."""
        with patch('requests.get', side_effect=mock_response):
            # Configure mock to raise an exception
            search_with_mock_llm.llm_client.generate_chat_completion.side_effect = Exception("LLM service error")
            
            # Extract content - should fall back to basic extraction
            content = search_with_mock_llm.extract_content_from_url(
                url="https://example.com/climate",
                context=mock_context
            )
            
            # Verify basic extraction was used as fallback
            assert "Climate Change Impacts on Coastal Cities" in content
            assert "Rising sea levels" in content
            
            # Should have logged the error
            mock_context.log_error.assert_called()


@pytest.mark.skipif(not SKIP_LLM_TESTS, reason="Running real LLM tests, skipping mocks")
class TestSearchAgentWithMockLLM:
    """Tests for the Search agent using mocked LLM responses."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        return MockDB()
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = Mock(spec=Context)
        context.update_progress = Mock()
        context.log_error = Mock()
        return context
    
    def test_search_with_fake_llm(self, mock_db, mock_context):
        """Test search agent with a completely mocked LLM implementation."""
        # Mock out the entire LLM client creation and response
        with patch('src.research_system.agents.search.create_ollama_client') as mock_create:
            mock_client = MagicMock()
            mock_client.generate_chat_completion.return_value = MOCK_LLM_CONTENT_EXTRACTION
            mock_create.return_value = mock_client
            
            # Mock requests
            with patch('requests.get', side_effect=mock_response):
                # Create search agent with mock LLM
                search = SearchAgent(
                    name="test_search", 
                    db=mock_db,
                    config={
                        "use_llm": True,
                        "ollama_model": "test-model"
                    }
                )
                
                # Extract content
                content = search.extract_content_from_url(
                    url="https://example.com/climate",
                    context=mock_context
                )
                
                # Verify the correct method was called
                mock_client.generate_chat_completion.assert_called_once()
                
                # Verify the content
                assert "Climate Change Effects on Coastal Cities" in content