"""
Tests for the Planner agent with LLM capabilities.

This tests the Planner agent's ability to work with and without LLM.
"""

import pytest
import os
import json
import re
from unittest.mock import MagicMock, patch

from src.research_system.agents.planner import PlannerAgent
from src.research_system.models.db import ResearchTask
from src.research_system.llm import create_ollama_client

# Skip these tests if we want to avoid LLM tests
SKIP_LLM_TESTS = os.environ.get("SKIP_LLM_TESTS", "true").lower() == "true"
SKIP_REASON = "LLM agent tests are skipped by default. Set SKIP_LLM_TESTS=false to run them."

# Mock responses for LLM
MOCK_LLM_PLAN_RESPONSE = {
    "message": {
        "role": "assistant",
        "content": """
        [
            {
                "id": 1,
                "type": "search",
                "name": "Initial Research",
                "description": "Gather fundamental information about the topic",
                "status": "pending"
            },
            {
                "id": 2,
                "type": "analysis",
                "name": "Data Analysis",
                "description": "Analyze gathered information for patterns and insights",
                "status": "pending",
                "depends_on": [1]
            },
            {
                "id": 3,
                "type": "expert_interview",
                "name": "Expert Consultation",
                "description": "Consult with subject matter experts to validate findings",
                "status": "pending",
                "depends_on": [2]
            },
            {
                "id": 4,
                "type": "synthesis",
                "name": "Information Synthesis",
                "description": "Combine all findings into a cohesive narrative",
                "status": "pending",
                "depends_on": [2, 3]
            },
            {
                "id": 5,
                "type": "review",
                "name": "Peer Review",
                "description": "Submit research for peer review and feedback",
                "status": "pending",
                "depends_on": [4]
            },
            {
                "id": 6,
                "type": "finalization",
                "name": "Final Report Creation",
                "description": "Create final report incorporating all feedback",
                "status": "pending",
                "depends_on": [5]
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
    
    def create_task(self, task):
        self.tasks[task.id] = task
        return task
    
    def get_task(self, task_id):
        return self.tasks.get(task_id)
    
    def update_task(self, task):
        self.tasks[task.id] = task
        return task
    
    def list_tasks(self, status=None, assigned_to=None, tag=None):
        return list(self.tasks.values())
    
    def create_result(self, result):
        self.results[result.id] = result
        return result


@pytest.mark.skipif(SKIP_LLM_TESTS, reason=SKIP_REASON)
class TestPlannerAgentWithLLM:
    """Tests for the Planner agent using LLM capabilities."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        return MockDB()
    
    @pytest.fixture
    def sample_task(self, mock_db):
        """Create a sample research task."""
        task = ResearchTask(
            id="task-123",
            title="Climate Change Research",
            description="Research on the effects of climate change on coastal cities",
            tags=["climate", "research", "coastal"]
        )
        mock_db.create_task(task)
        return task
    
    @pytest.fixture
    def planner_with_mock_llm(self, mock_db):
        """Create a planner agent with a mocked LLM client."""
        with patch('src.research_system.llm.create_ollama_client') as mock_create_client:
            # Setup the mock LLM client
            mock_client = MagicMock()
            mock_client.generate_chat_completion.return_value = MOCK_LLM_PLAN_RESPONSE
            mock_create_client.return_value = mock_client
            
            # Create planner with mock LLM
            planner = PlannerAgent(
                name="test_planner", 
                db=mock_db,
                config={
                    "use_llm": True,
                    "ollama_model": "test-model"
                }
            )
            
            yield planner
    
    @pytest.fixture
    def planner_without_llm(self, mock_db):
        """Create a planner agent with LLM disabled."""
        planner = PlannerAgent(
            name="test_planner_no_llm", 
            db=mock_db,
            config={
                "use_llm": False
            }
        )
        return planner
    
    def test_planner_llm_initialization(self, planner_with_mock_llm):
        """Test planner initializes correctly with LLM client."""
        assert planner_with_mock_llm.use_llm is True
        assert planner_with_mock_llm.ollama_model == "test-model"
        assert planner_with_mock_llm.llm_client is not None
    
    def test_planner_no_llm_initialization(self, planner_without_llm):
        """Test planner initializes correctly without LLM client."""
        assert planner_without_llm.use_llm is False
        assert planner_without_llm.llm_client is None
    
    def test_generate_plan_with_llm(self, planner_with_mock_llm, sample_task):
        """Test generating a research plan using LLM."""
        plan = planner_with_mock_llm.generate_plan_for_task(sample_task.id)
        
        # Verify the plan was created
        assert plan is not None
        assert "id" in plan
        assert plan["task_id"] == sample_task.id
        
        # Verify that steps from the mock LLM response were used
        assert len(plan["steps"]) == 6
        assert plan["steps"][0]["name"] == "Initial Research"
        assert plan["steps"][5]["name"] == "Final Report Creation"
        
        # Check dependencies
        assert "depends_on" in plan["steps"][4]
        assert plan["steps"][4]["depends_on"] == [4]
    
    def test_generate_plan_without_llm(self, planner_without_llm, sample_task):
        """Test generating a research plan without using LLM."""
        plan = planner_without_llm.generate_plan_for_task(sample_task.id)
        
        # Verify the plan was created using the template approach
        assert plan is not None
        assert "id" in plan
        assert plan["task_id"] == sample_task.id
        
        # Verify default template steps were used
        assert len(plan["steps"]) == 5
        assert plan["steps"][0]["name"] == "Initial Information Gathering"
        assert plan["steps"][4]["name"] == "Finalize Research"
    
    def test_llm_error_handling(self, mock_db, sample_task):
        """Test planner gracefully handles LLM errors."""
        with patch('src.research_system.llm.create_ollama_client') as mock_create_client:
            # Setup the mock LLM client that raises an exception
            mock_client = MagicMock()
            mock_client.generate_chat_completion.side_effect = Exception("LLM service error")
            mock_create_client.return_value = mock_client
            
            # Create planner with problematic LLM
            planner = PlannerAgent(
                name="test_planner_error", 
                db=mock_db,
                config={
                    "use_llm": True,
                    "ollama_model": "test-model"
                }
            )
            
            # Should fall back to template-based planning
            plan = planner.generate_plan_for_task(sample_task.id)
            
            # Verify the plan was created using the template approach
            assert plan is not None
            assert len(plan["steps"]) == 5
            assert plan["steps"][0]["name"] == "Initial Information Gathering"


@pytest.mark.skipif(not SKIP_LLM_TESTS, reason="Running real LLM tests, skipping mocks")
class TestPlannerAgentWithMockLLM:
    """Tests for the Planner agent using mocked LLM responses."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        return MockDB()
    
    @pytest.fixture
    def sample_task(self, mock_db):
        """Create a sample research task."""
        task = ResearchTask(
            id="task-123",
            title="Climate Change Research",
            description="Research on the effects of climate change on coastal cities",
            tags=["climate", "research", "coastal"]
        )
        mock_db.create_task(task)
        return task
    
    def test_planner_with_fake_llm(self, mock_db, sample_task):
        """Test planner with a completely mocked LLM implementation."""
        # Mock out the entire LLM client creation and response
        with patch('src.research_system.agents.planner.create_ollama_client') as mock_create:
            mock_client = MagicMock()
            mock_client.generate_chat_completion.return_value = MOCK_LLM_PLAN_RESPONSE
            mock_create.return_value = mock_client
            
            # Create planner with mock LLM
            planner = PlannerAgent(
                name="test_planner", 
                db=mock_db,
                config={
                    "use_llm": True,
                    "ollama_model": "test-model"
                }
            )
            
            # Generate a plan
            plan = planner.generate_plan_for_task(sample_task.id)
            
            # Verify the correct method was called
            mock_client.generate_chat_completion.assert_called_once()
            
            # Verify the plan
            assert plan is not None
            assert len(plan["steps"]) == 6
            assert plan["steps"][0]["type"] == "search"