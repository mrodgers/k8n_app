# Research System Development Plan
*Last updated: April 27, 2025*

This document consolidates the development plan for the Research System, with a focus on Kubernetes integration and current implementation status.

> **Note**: This is a critical document for developers. For a complete guide to all project documentation, refer to the [Developer Documentation Guide](./DEVELOPER_DOCUMENTATION_GUIDE.md).

## Table of Contents

1. [Current Implementation Status](#current-implementation-status)
2. [System Architecture](#system-architecture)
3. [Kubernetes Integration](#kubernetes-integration)
4. [Implementation Plan](#implementation-plan)
5. [Project Structure](#project-structure)
6. [Design Principles](#design-principles)
7. [Requirements](#requirements)
8. [Development Guidelines](#development-guidelines)

## Current Implementation Status

Based on code review completed on April 27, 2025, the project is in the early stages of Phase 1 implementation:

### Completed Components
- Core architecture files (`coordinator.py` and `server.py`)
- Database models for research tasks and results (`db.py`)
- Planner agent implementation (`planner.py`)
- Basic containerization (`Dockerfile`)

### Incomplete Components
- Search agent implementation (`search.py` exists but appears incomplete)
- CLI interface (directory structure exists but implementation is missing)
- Docker Compose configuration (not present)
- Kubernetes manifests (not present)
- Comprehensive tests (only basic FastAPI app tests exist)

## System Architecture

The system follows a microservices architecture using FastMCP servers:

### High-Level Components
- **Coordinator**: Orchestrates interactions between different agents
- **Server**: Provides the main FastMCP server implementation
- **Agents**: Specialized components for planning and search
- **Database**: Storage for tasks and results

### Agent Types
- **Research Planner Agent**: Develops research strategies and breaks down complex tasks
- **Search Agent**: Performs web searches using the Brave Search API
- **Paper Analysis Agent**: Extracts and synthesizes information from technical papers
- **Citation Agent**: Ensures proper citation and reference formatting
- **Summary Agent**: Creates concise summaries of research findings
- **Supervisor Agent**: Provides oversight and guidance to worker agents

## Kubernetes Integration

As this is a Kubernetes-based solution, the following design considerations need to be addressed:

### 1. Service Discovery

**Current State:** The coordinator assumes hardcoded URLs without Kubernetes service discovery.

**Required Changes:**
```python
# Current approach (needs modification)
agent = Agent(
    name="search",
    server_url="http://search-service:8080",
    description="Search Agent"
)

# Kubernetes-friendly approach
agent = Agent(
    name="search",
    server_url=f"http://{os.getenv('SEARCH_SERVICE_HOST', 'search-service')}:{os.getenv('SEARCH_SERVICE_PORT', '8080')}",
    description="Search Agent"
)
```

### 2. Configuration Management

**Current State:** Configuration is loaded from local files.

**Required Changes:**
- Primary configuration source should be environment variables (from ConfigMaps/Secrets)
- Secondary source can be ConfigMap mounted as file
- Implement a deep merge function for combining configurations

### 3. State Management

**Current State:** TinyDB is used for data persistence, which is file-based and not suitable for Kubernetes.

**Required Changes:**
- Replace TinyDB with a Kubernetes-compatible database:
  - PostgreSQL with persistent volumes
  - MongoDB with StatefulSet
  - Redis for caching and temporary data

### 4. Health Checks and Readiness

**Current State:** Basic health endpoint exists but lacks Kubernetes-specific probes.

**Required Changes:**
- Implement proper liveness probe endpoint (`/healthz`)
- Implement readiness probe endpoint (`/readyz`)
- Add dependency checking in readiness probes

### 5. Resource Specifications

**Current State:** No resource specifications for containers.

**Required Changes:**
- Create Kubernetes deployment manifests with resource requests and limits
- Configure appropriate memory and CPU allocations
- Set up appropriate liveness and readiness probe parameters

## Implementation Plan

Based on the current status and Kubernetes requirements, here's the implementation plan for Phase 1:

### 1. Complete Core Components (High Priority)

- **Search Agent Completion**
  - Finish implementation of `search.py`
  - Implement proper Brave Search API integration
  - Add content extraction capabilities
  - Ensure error handling and retry logic

- **CLI Interface Implementation**
  - Create `main.py` in the cli directory
  - Implement command-line argument parsing
  - Add user-friendly output formatting
  - Include progress reporting

### 2. Kubernetes Integration (High Priority)

- **Configuration Management**
  - Modify configuration loading to use environment variables
  - Create ConfigMap and Secret templates
  - Update all hardcoded values to use configuration

- **Database Migration**
  - Replace TinyDB with PostgreSQL
  - Create database schema initialization script
  - Add migration functionality for development
  - Implement connection pooling and retry logic

- **Kubernetes Manifests**
  - Create Deployment manifests for each component
  - Define Service objects for communication
  - Configure resource requests and limits
  - Add proper liveness and readiness probes

### 3. Development Environment (Medium Priority)

- **Docker Compose**
  - Create docker-compose.yml for local development
  - Configure service discovery for local environment
  - Set up local database for development
  - Add environment variable configuration

- **Development Scripts**
  - Create helper scripts for common operations
  - Add database setup and seeding functionality
  - Implement local testing utilities
  - Create documentation for developer workflow

### 4. Testing (Medium Priority)

- **Unit Tests**
  - Add tests for the coordinator component
  - Create tests for the planner agent
  - Implement tests for the search agent
  - Test database operations with mocked DB
  - Create test for each function implemented
  - Aim for 90% code coverage for all new code

- **Integration Tests**
  - Test end-to-end research workflows
  - Verify inter-agent communication
  - Test with mock external services
  - Validate research result quality

- **Coverage Reporting**
  - Configure pytest-cov for coverage reporting
  - Include coverage checks in the CI/CD pipeline
  - Address any coverage gaps before merging new code

### 5. Documentation (Medium Priority)

- **Architecture Documentation**
  - Create Kubernetes architecture diagram
  - Document service interaction patterns
  - Update deployment instructions
  - Add configuration reference

- **API Documentation**
  - Document FastMCP tools and resources
  - Create CLI usage examples
  - Add database schema documentation
  - Include sample research workflows

## Project Structure

```
k8s-python-app-new/
├── docker-compose.yml              # Added for development
├── Dockerfile                      # Enhanced for Kubernetes
├── kubernetes/                     # New directory for K8s configs
│   ├── configmaps.yaml
│   ├── deployments.yaml
│   ├── secrets.yaml
│   └── services.yaml
├── scripts/                        # Development scripts
│   ├── setup_db.sh
│   ├── run_local.sh
│   └── test_endpoints.sh
├── docs/
│   ├── RESEARCH_SYSTEM_DEV_PLAN.md # This document
│   ├── architecture.md             # Enhanced with K8s diagrams
│   ├── api.md                      # API documentation
│   └── CONTRIBUTING.md             # Contribution guidelines
├── requirements.txt
├── setup.py
└── research_system/
    ├── __init__.py
    ├── cli/
    │   ├── __init__.py
    │   └── main.py                 # To be implemented
    ├── core/
    │   ├── __init__.py
    │   ├── coordinator.py          # Enhanced for K8s
    │   ├── main.py
    │   └── server.py               # Enhanced for K8s
    ├── agents/
    │   ├── __init__.py
    │   ├── planner.py
    │   └── search.py               # To be completed
    ├── models/
    │   ├── __init__.py
    │   └── db.py                   # To be migrated to PostgreSQL
    └── utils/
        ├── __init__.py
        └── helpers.py
```

## Design Principles

When implementing these changes, adhere to these Kubernetes-centric design principles:

1. **Statelessness**: Design components to be stateless where possible
2. **Configuration Externalization**: Use environment variables from ConfigMaps
3. **Health Management**: Implement proper liveness and readiness probes
4. **Resource Efficiency**: Set appropriate resource requests and limits
5. **Observability**: Implement structured logging (JSON format)

## Requirements

```
# requirements.txt
fastmcp>=2.0.0
fastapi>=0.104.0
uvicorn>=0.23.2
click>=8.1.7
httpx>=0.25.0
pydantic>=2.4.2
psycopg2-binary>=2.9.9  # For PostgreSQL
prometheus-client>=0.17.1  # For metrics
structlog>=23.1.0  # For structured logging
pytest>=7.4.3
pytest-asyncio>=0.21.1
pytest-mock>=3.12.0
```

## Development Guidelines

### General Guidelines

- Always start a new server after making changes to test them
- Look for existing code to iterate on instead of creating new code
- Do not drastically change patterns before trying to iterate on existing patterns
- Kill all existing related servers before starting a new one
- Prefer simple solutions over complex ones
- Avoid duplication of code
- Write code that accounts for different environments: dev, test, and prod
- Only make well-understood changes related to the requested task
- Keep the codebase clean and organized
- Avoid files over 200-300 lines of code
- Write thorough tests for all major functionality
- Do not add stubbing or fake data patterns to production code

### File Management and Organization

- Place all new files in the appropriate directories according to their function
- Follow the established project structure for file organization
- Clean up temporary files before committing changes to git
- Do not commit any of the following to the repository:
  - Python cache files (`__pycache__/`, `*.pyc`, `*.pyo`)
  - Log files generated during development
  - Local database files from TinyDB
  - Environment-specific configuration files
  - Operating system files (`.DS_Store`, `Thumbs.db`)
  - Virtual environment directories
  - IDE-specific configuration files

### Pre-Commit Verification

Before committing code to the repository, verify:

1. All temporary files have been removed
2. New files are placed in appropriate directories
3. No sensitive information (API keys, credentials) is included
4. Tests are passing with 90% code coverage
5. Code follows established patterns and style guidelines

Use the following commands for cleanup before committing:

```bash
# Clean up temporary Python files
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Clean up log files
find . -name "*.log" -delete

# Clean up OS-specific files
find . -name ".DS_Store" -delete

# Verify tests pass
pytest tests/

# Check test coverage
pytest --cov=research_system tests/
```
