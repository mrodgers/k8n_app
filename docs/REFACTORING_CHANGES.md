# Agent Architecture Refactoring

This document describes the changes made to simplify and improve the agent architecture in the Research System.

## Overview of Changes

The agent architecture has been refactored to:

1. Replace HTTP-based communication between agents with direct method calls
2. Separate LLM functionality into a dedicated service layer
3. Define clear interfaces for capability providers
4. Introduce a central registry for capabilities
5. Implement workflow orchestration with simpler dependency injection

## New Components

### 1. LLM Service (`src/research_system/services/llm_service.py`)

A centralized service for interacting with Large Language Models:

- Provides a unified interface for text generation, chat completions, and structured data extraction
- Abstracts away provider-specific details (Ollama, etc.)
- Handles prompt creation, retry logic, and error scenarios
- Includes specialized methods for research plan generation and result ranking

### 2. Registry (`src/research_system/core/registry.py`)

A central registry for capability providers:

- Allows registration of components that provide capabilities
- Maps capability names to provider implementations
- Provides direct method execution without HTTP proxying
- Supports dynamic discovery of capabilities
- Includes workflow registration and execution

### 3. Orchestrator (`src/research_system/core/orchestrator.py`)

A workflow orchestrator that combines multiple capabilities:

- Defines standard research workflows
- Handles cross-agent operations
- Manages execution state and reporting
- Provides a higher-level API for complex operations

### 4. Refactored Agents

Agents have been refactored to use the capability pattern:

- `PlannerAgent` (`src/research_system/agents/planner_refactored.py`)
- `SearchAgent` (`src/research_system/agents/search_refactored.py`)

Each agent now:
- Implements a standard interface with `get_capabilities()` and `execute_capability()`
- Receives dependencies through constructor injection
- Registers its capabilities with a central registry
- Implements capabilities with clear input/output contracts

### 5. New API Routes

Added unified research API routes (`src/research_system/routes/research.py`):

- Provides endpoints for research-oriented operations
- Uses the registry and orchestrator to fulfill requests
- Supports workflow execution via background tasks
- Defines clear request/response models

## Implementation Details

### Standard Agent Interface

```python
class CapabilityProvider(Protocol):
    """Protocol for a capability provider."""
    
    def get_capabilities(self) -> List[str]:
        """Get a list of capabilities provided by this provider."""
        ...
    
    def execute_capability(self, name: str, **kwargs) -> Any:
        """Execute a capability by name with the given arguments."""
        ...
```

### Registry for Capability Management

```python
# Register a provider
registry.register_provider("search", search_agent)

# Execute a capability
results = registry.execute_capability(
    "execute_search",
    query="my search query",
    task_id="task123"
)
```

### LLM Service Usage

```python
# Generate a research plan
steps = llm_service.create_research_plan(
    title="Research topic",
    description="Detailed description",
    tags=["research", "ai"]
)

# Rank search results
ranked_results = llm_service.rank_search_results(
    results=search_results,
    query="search query"
)
```

### Workflow Orchestration

```python
# Execute a complete research workflow
workflow_result = orchestrator.execute_basic_research(
    title="Research topic",
    description="Research description",
    query="search query"
)
```

## Simplified API Routes

The new `research.py` routes provide a unified API for research operations:

- `POST /api/research/tasks` - Create a research task
- `GET /api/research/tasks` - List research tasks
- `POST /api/research/plans/generate` - Generate a research plan
- `POST /api/research/search` - Execute a search
- `POST /api/research/workflow/research` - Execute a complete research workflow

## Benefits of the Refactoring

1. **Reduced Complexity**
   - Eliminated HTTP communication between components
   - Removed redundant proxy layer and server setup
   - Streamlined component interaction

2. **Improved Testability**
   - Components can be easily mocked for testing
   - Clear interfaces for each component
   - Dependency injection for better unit testing

3. **Better Separation of Concerns**
   - LLM functionality separated from agent business logic
   - Database operations decoupled from agent implementation
   - Configuration centralized through proper injection

4. **Enhanced Maintainability**
   - Clear capability contracts between components
   - More intuitive workflow definitions
   - Improved error handling and reporting

5. **Performance Improvements**
   - Direct method calls instead of HTTP requests
   - Reduced network overhead
   - Simplified data flow between components

## Migration Path

The code base currently maintains backward compatibility by:

1. Keeping the original agent implementations available
2. Updating the `app_factory.py` to use new components while preserving backward compatibility
3. Registering both old and new implementations during initialization
4. Providing access to both old interfaces and new capabilities

Over time, usage of the original agent implementations should be migrated to the new capability-based architecture.