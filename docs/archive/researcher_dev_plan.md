# Research Agent System Design Summary

I've created a comprehensive design and implementation plan for your agentic research solution. Here's a summary of the key components:

## Design Highlights

1. **Architecture**
   - FastAPI-based backend with asynchronous support
   - FastMCP for agent communication and tool management
   - Modular multi-agent system with clear separation of responsibilities
   - Support for Ollama-based local LLMs
   - CLI interface (evolving to web UI in future phases)

2. **Agent Types**
   - Research Planner: Develops research strategies and breaks down tasks
   - Search Agent: Performs web searches using Brave Search API
   - Paper Analysis Agent: Extracts information from technical papers
   - Citation Agent: Ensures proper citations
   - Summary Agent: Creates concise summaries
   - Supervisor Agent: Provides oversight and coordinates other agents

3. **Key Features**
   - Configurable research depth and domain restrictions
   - User check-ins at configurable intervals
   - Comprehensive citation and source tracking
   - Asynchronous long-running research tasks
   - Extensible tool architecture
   - Integration with FastMCP for agent communication

4. **Implementation Approach**
   - Python 3.10+ with FastAPI and Asyncio
   - FastMCP for standardized agent communication
   - SQLite for MVP storage (PostgreSQL for production)
   - Docker for containerization
   - Pytest for testing

## Next Steps

1. **MVP Phase**
   - Implement basic CLI interface and core coordinator
   - Integrate FastMCP for agent communication
   - Develop Brave Search tool integration
   - Create basic research planner and search agents

2. **Phase 2**
   - Add supervisor and worker agent model
   - Implement user check-ins
   - Enhance research report quality
   - Improve citation handling

3. **Phase 3**
   - Develop web UI with chat interface
   - Add authentication
   - Support additional research tools
   - Enhance collaboration capabilities

The design emphasizes extensibility, allowing for easy addition of new tools and agents as requirements evolve.


# Design Document: Agentic Research System

## 1. Overview

The Agentic Research System (ARS) is a distributed, scalable platform designed to perform automated research tasks using large language models (LLMs). The system leverages FastMCP for agent management and communication, with a focus on technical paper research and web search capabilities. The system follows a multi-agent architecture with specialized agents for different research tasks, coordinated through a standardized communication protocol.

## 2. System Objectives

### 2.1 Core Functionality
- Conduct automated research on technical topics with configurable depth and domain restrictions
- Perform web searches using the Brave Search API
- Generate comprehensive research reports with proper citations and references
- Provide interactive user guidance and feedback during the research process
- Support asynchronous long-running research tasks

### 2.2 Technical Goals
- Create a scalable, extensible architecture that can handle multiple concurrent users
- Implement a modular design that supports the addition of new tools and agents
- Provide a CLI interface with future expansion to a web UI
- Enable deployment in containerized environments (Docker, Kubernetes, OpenShift)
- Utilize local LLM capabilities through Ollama for cost-effective processing

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌───────────────┐     ┌──────────────────┐     ┌───────────────────┐
│               │     │                  │     │                   │
│  Client (CLI) │────▶│  API Gateway     │────▶│  Agent Coordinator│
│               │     │  (FastAPI)       │     │                   │
└───────────────┘     └──────────────────┘     └─────────┬─────────┘
                                                         │
                                                         ▼
                      ┌──────────────────┐     ┌───────────────────┐
                      │                  │     │                   │
                      │  FastMCP Server  │◀───▶│  Agent Runners    │
                      │                  │     │                   │
                      └──────────────────┘     └─────────┬─────────┘
                                                         │
                                                         ▼
┌───────────────┐     ┌──────────────────┐     ┌───────────────────┐
│               │     │                  │     │                   │
│  Data Storage │◀───▶│  Tool Registry   │◀───▶│  Specialized      │
│               │     │                  │     │  Agents           │
└───────────────┘     └──────────────────┘     └───────────────────┘
```

### 3.2 Component Description

#### 3.2.1 Client (CLI)
- Command-line interface for initiating research tasks, checking status, and retrieving results
- Supports configuration of research parameters (depth, domains, check-in frequency)
- Will eventually evolve into a web-based chat interface

#### 3.2.2 API Gateway (FastAPI)
- RESTful API endpoints for client communication
- Authentication and user management
- Request validation and routing
- Async support for long-running tasks

#### 3.2.3 Agent Coordinator
- Manages the lifecycle of research tasks
- Creates and coordinates multiple specialized agents
- Handles check-ins with users at specified intervals
- Processes and aggregates results from various agents

#### 3.2.4 FastMCP Server
- Provides standardized communication protocol for agent interactions
- Handles tool discovery and invocation
- Manages resource access and context sharing
- Supports LLM sampling for agent intelligence

#### 3.2.5 Agent Runners
- Executes agent workflows using FastMCP
- Manages the agent loop and tool invocations
- Handles handoffs between different agents
- Captures trace information for debugging and optimization

#### 3.2.6 Specialized Agents
- **Research Planner Agent**: Develops research strategies and breaks down complex tasks
- **Search Agent**: Performs web searches using the Brave Search API
- **Paper Analysis Agent**: Extracts and synthesizes information from technical papers
- **Citation Agent**: Ensures proper citation and reference formatting
- **Summary Agent**: Creates concise summaries of research findings
- **Supervisor Agent**: Provides oversight and guidance to worker agents

#### 3.2.7 Tool Registry
- Manages the collection of available tools for agents
- Provides tool discovery and integration capabilities
- Supports the addition of new tools over time

#### 3.2.8 Data Storage
- Stores research results, agent states, and user configurations
- Maintains history of research tasks and their outcomes
- Supports persistence of long-running research tasks

### 3.3 Communication Model

The system uses a standardized communication protocol based on the FastMCP framework:

1. **Agent-to-Agent Communication**:
   - Utilizes the mounting mechanism provided by FastMCP
   - Structured message passing with clear context and objectives
   - Specialized message types for different communication needs

2. **Agent-to-Tool Communication**:
   - Function calling pattern for tool invocation
   - Standardized input/output formats for tool interactions
   - Tool response handling and incorporation into agent context

3. **System-to-User Communication**:
   - Periodic check-ins based on configurable thresholds (time or token usage)
   - Status updates on research progress
   - User guidance requests when needed

## 4. Detailed Component Specifications

### 4.1 Client (CLI) Specification

The CLI will be developed using Python's `click` library for a structured command interface:

```python
# Example CLI structure
@click.group()
def cli():
    """Research Agent CLI"""
    pass

@cli.command()
@click.option('--topic', required=True, help='Research topic')
@click.option('--depth', default='medium', help='Research depth (shallow, medium, deep)')
@click.option('--domains', multiple=True, help='Domain restrictions')
@click.option('--checkin-interval', default=30, help='Check-in interval in minutes')
@click.option('--token-threshold', default=10000, help='Check-in token threshold')
def start_research(topic, depth, domains, checkin_interval, token_threshold):
    """Start a new research task"""
    # Implementation details
```

### 4.2 API Gateway Specification

The API Gateway will be implemented using FastAPI for high performance, async capabilities, and automatic documentation:

```python
# Example API routes
@app.post("/research/tasks", response_model=TaskCreationResponse)
async def create_research_task(task: TaskCreationRequest):
    """Create a new research task"""
    # Implementation details

@app.get("/research/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of an existing task"""
    # Implementation details

@app.post("/research/tasks/{task_id}/checkin", response_model=CheckInResponse)
async def user_checkin(task_id: str, guidance: UserGuidanceRequest):
    """Provide guidance during a research task"""
    # Implementation details
```

### 4.3 FastMCP Agent Models

#### 4.3.1 Research Planner Agent

```python
from fastmcp import FastMCP

# Create dedicated FastMCP server for research planning
research_planner_mcp = FastMCP("Research Planner")

@research_planner_mcp.tool()
async def plan_research(topic: str, depth: str = "medium") -> dict:
    """
    Develop a comprehensive research strategy for the given topic.
    
    Args:
        topic: The research topic to investigate
        depth: Research depth (shallow, medium, deep)
        
    Returns:
        A structured research plan with questions, subtopics, and search queries
    """
    # Implementation details
    return research_plan
```

#### 4.3.2 Search Agent

```python
from fastmcp import FastMCP, Context

# Create dedicated FastMCP server for search functionality
search_agent_mcp = FastMCP("Search Agent")

@search_agent_mcp.tool()
async def brave_search(query: str, num_results: int = 10, ctx: Context = None) -> list:
    """
    Perform a web search using the Brave Search API.
    
    Args:
        query: The search query
        num_results: Number of results to return
        ctx: FastMCP context for progress reporting
        
    Returns:
        List of search results with metadata
    """
    if ctx:
        await ctx.info(f"Searching for: {query}")
    
    # Implementation of Brave Search API call
    
    if ctx:
        await ctx.report_progress(1, 1)
    
    return search_results
```

#### 4.3.3 Supervisor Agent

```python
from fastmcp import FastMCP, Context

# Create FastMCP server for supervisor functionality
supervisor_mcp = FastMCP("Supervisor Agent")

@supervisor_mcp.tool()
async def coordinate_research(topic: str, plan: dict, ctx: Context = None) -> dict:
    """
    Coordinate the research process across multiple specialized agents.
    
    Args:
        topic: The research topic
        plan: The research plan to execute
        ctx: FastMCP context for progress reporting and sampling
        
    Returns:
        Research results including findings and citations
    """
    if ctx:
        await ctx.info(f"Starting coordinated research on: {topic}")
    
    # Implementation details for agent coordination
    
    # Use LLM sampling for decision making if needed
    if ctx:
        decision = await ctx.sample(
            f"Given the current research progress on {topic}, what should be the next focus area?",
            system_prompt="You are a research coordinator making strategic decisions."
        )
    
    # Implementation continues
    
    return research_results
```

### 4.4 Data Models

#### 4.4.1 Research Task

```python
class ResearchDepth(str, Enum):
    SHALLOW = "shallow"
    MEDIUM = "medium"
    DEEP = "deep"

class ResearchTask(BaseModel):
    id: str
    topic: str
    depth: ResearchDepth
    domains: List[str] = []
    checkin_interval: int = 30  # minutes
    token_threshold: int = 10000
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    user_id: str
```

#### 4.4.2 Research Result

```python
class Citation(BaseModel):
    source: str
    url: Optional[str] = None
    title: str
    authors: Optional[List[str]] = None
    publication_date: Optional[date] = None
    accessed_date: date

class ResearchSection(BaseModel):
    title: str
    content: str
    citations: List[Citation] = []

class ResearchResult(BaseModel):
    task_id: str
    summary: str
    sections: List[ResearchSection] = []
    bibliography: List[Citation] = []
    metadata: Dict[str, Any] = {}
```

## 5. Technology Stack

### 5.1 Backend
- **Language**: Python 3.10+
- **API Framework**: FastAPI
- **Agent Framework**: FastMCP
- **CLI Framework**: Click
- **Async Runtime**: Asyncio with Uvicorn
- **Task Queue**: Celery (for long-running tasks)
- **Local LLM**: Ollama

### 5.2 Storage
- **Database**: SQLite (MVP), PostgreSQL (production)
- **Object Storage**: Local filesystem (MVP), S3-compatible storage (production)

### 5.3 Deployment
- **Containerization**: Docker
- **Container Orchestration**: Kubernetes/OpenShift (future)
- **Local Development**: Docker Compose

### 5.4 Testing
- **Unit Testing**: Pytest
- **API Testing**: Requests + Pytest
- **Integration Testing**: Pytest with Docker Compose

## 6. Key Implementation Considerations

### 6.1 FastMCP Integration
- Use mounted FastMCP servers for specialized agent functionality
- Leverage FastMCP Context for progress reporting and agent communication
- Utilize FastMCP's sampling capability for LLM-powered decision making
- Take advantage of FastMCP's standardized tool and resource architecture

### 6.2 LLM Integration
- Use Ollama for local LLM capabilities
- Configurable models per agent type
- Support for model swapping based on task requirements
- Fallback mechanisms for when local models are insufficient

### 6.3 Agent Lifecycle Management
- Dynamic agent creation based on task requirements
- Agent state persistence for long-running tasks
- Graceful handling of agent failures
- Resource management to prevent overloading

### 6.4 Scalability Considerations
- Horizontal scaling of API Gateway
- Worker pool for agent execution
- Connection pooling for database and external APIs
- Rate limiting for Brave Search API and other external services

### 6.5 User Interaction Model
- Asynchronous research tasks with periodic updates
- Configurable check-in points based on time or token usage
- Clear communication of research progress
- Structured guidance requests when needed

### 6.6 Tool Integration
- Leverage FastMCP's decorator-based tool registration
- Support for both synchronous and asynchronous tools
- Standardized error handling and response formatting
- Tool versioning and capability discovery

## 7. Development Roadmap

### 7.1 MVP Phase
- Implement basic CLI interface
- Develop core Agent Coordinator using FastMCP
- Implement Brave Search tool as FastMCP tool
- Create Research Planner and Search agents as FastMCP servers
- Basic research report generation
- Simple local storage
- FastMCP-based development mode for testing

### 7.2 Phase 2
- Add Supervisor agent as a FastMCP server
- Implement worker agent model with FastMCP mounting
- Implement user check-ins using FastMCP context
- Enhance research report quality
- Improve citation handling
- Add persistence for long-running tasks

### 7.3 Phase 3
- Develop web UI with chat interface
- Implement user authentication
- Add support for additional research tools
- Enhance collaboration capabilities
- Improve research quality and depth

### 7.4 Future Enhancements
- Integration with academic paper databases
- Support for multimedia content in research reports
- Fine-tuned domain-specific research agents
- Collaborative research capabilities
- Advanced visualization of research findings

## 8. Requirements Specification

### 8.1 Functional Requirements

1. **Research Initiation**
   - The system must allow users to initiate research tasks with a specified topic
   - Users must be able to configure research depth and domain restrictions
   - The system must confirm receipt of research tasks and provide a task identifier

2. **Research Execution**
   - The system must autonomously conduct research on the specified topic
   - The system must use web searches using FastMCP tools to find relevant information
   - The system must analyze and synthesize information from multiple sources
   - The system must provide proper citations for all information

3. **User Interaction**
   - The system must check in with users at specified intervals or token thresholds
   - The system must provide clear status updates on research progress
   - The system must request guidance when necessary
   - The system must allow users to adjust research direction during execution

4. **Result Delivery**
   - The system must generate comprehensive research reports
   - Reports must include a summary, detailed sections, and bibliography
   - Users must be able to retrieve reports in multiple formats
   - The system must maintain a history of completed research tasks

### 8.2 Non-Functional Requirements

1. **Performance**
   - The system must support at least 10 concurrent users
   - API endpoints must respond within 2 seconds
   - Long-running tasks must be processed asynchronously
   - The system must handle research tasks lasting up to 24 hours

2. **Scalability**
   - The architecture must support horizontal scaling
   - Components must be designed for distributed deployment
   - The system must gracefully handle increases in load

3. **Reliability**
   - The system must recover from component failures
   - Long-running tasks must be recoverable after system restarts
   - Data must be persistently stored and backed up

4. **Security**
   - The system must validate and sanitize all user inputs
   - API endpoints must implement rate limiting
   - Sensitive configuration must be securely managed

5. **Extensibility**
   - The system must support the addition of new agent types
   - The system must support the integration of new tools
   - The architecture must accommodate future UI enhancements

## 9. Conclusion

The Agentic Research System design provides a solid foundation for building an autonomous research assistant capable of handling technical paper research and web searches. By leveraging FastMCP for agent communication and following a multi-agent architecture, the system offers a flexible and extensible platform that can evolve to meet future requirements.

The initial MVP will focus on core functionality with a CLI interface, while future phases will enhance capabilities and introduce a web UI. The modular design allows for incremental development and integration of additional tools and agent types as needed.