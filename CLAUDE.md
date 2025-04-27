# K8s Python App - Research System Guide

This guide is designed to help Claude Code work effectively with the Research System project. Below you'll find information about the project structure, important patterns, common commands, and development best practices.

> **IMPORTANT**: This document contains critical developer guidance and should be the starting point for any development work on this project.

## Project Overview

The Research System is a Kubernetes-based microservices application using FastMCP servers. It enables automated research workflows through specialized agents for planning, searching, and analysis.

### Key Components

- **Coordinator**: Orchestrates interactions between different agents
- **Server**: Provides the main FastMCP server implementation
- **Agents**: Specialized components for planning and search
- **Database**: Storage for research tasks and results

## Project Structure

```
k8s-python-app-new/
├── docker-compose.yml              # For local development 
├── Dockerfile                      # Container definition
├── kubernetes/                     # K8s manifests
│   ├── deployment.yaml
│   └── service.yaml
├── docs/                           # Documentation
├── src/
│   ├── app.py                      # Main application entry point
│   └── research_system/
│       ├── __init__.py
│       ├── cli/                    # CLI interface
│       │   └── __init__.py
│       ├── core/                   # Core components
│       │   ├── __init__.py
│       │   ├── coordinator.py      # Agent orchestration
│       │   ├── main.py             # Main server logic
│       │   └── server.py           # FastMCP server
│       ├── agents/                 # Agent implementations
│       │   ├── __init__.py
│       │   ├── planner.py          # Research planner
│       │   └── search.py           # Search agent
│       ├── models/                 # Data models
│       │   ├── __init__.py
│       │   └── db.py               # Database models
│       └── utils/                  # Utilities
│           ├── __init__.py
│           └── helpers.py          # Helper functions
├── tests/                          # Test suite
└── requirements.txt                # Dependencies
```

## Common Commands

### Development

```bash
# Start the development server
./app_manager.sh start

# Check the server status
./app_manager.sh status

# Stop the server
./app_manager.sh stop

# View server logs
./app_manager.sh logs

# Run a search query
./app_manager.sh search --query "your search query" --max-results 5

# Create a task
./app_manager.sh task create --title "Task Title" --description "Task description" --tags research report

# List tasks
./app_manager.sh task list

# Get task details
./app_manager.sh task get --id <task-id>

# Create a research plan
./app_manager.sh plan create --task-id <task-id>

# Get plan details
./app_manager.sh plan get --id <plan-id>

# View results
./app_manager.sh result list --task-id <task-id>
./app_manager.sh result get --id <result-id>
```

### Testing

```bash
# Run all tests
./run_tests.sh

# Run specific test suite
./run_tests.sh tests/test_integration

# Run tests with coverage
./run_tests.sh --cov

# Run a specific test
./run_tests.sh tests/test_app.py::test_health_endpoint
```

### Docker and Kubernetes

```bash
# Build Docker image
docker build -t research-system .

# Run with Docker
docker run -p 8080:8080 research-system

# Deploy to Kubernetes
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# Get service status
kubectl get services

# Get pod status
kubectl get pods

# View logs
kubectl logs <pod-name>
```

## Code Style and Patterns

### Python Coding Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Document classes and functions with docstrings
- Keep files under 200-300 lines of code
- Use meaningful variable and function names

### FastMCP Patterns

```python
# Server registration pattern
def setup_server():
    server = Server()
    server.register_tool("tool_name", tool_function)
    server.register_resource("resource_name", resource_value)
    return server

# Agent interaction pattern
async def call_agent(agent_name, task_description):
    agent_url = f"http://{agent_name}-service:8080"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{agent_url}/tools/run_task",
            json={"task": task_description}
        )
        return response.json()
```

### Kubernetes Integration Patterns

```python
# Configuration loading with environment variables
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/db')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')

# Service discovery
agent_host = os.getenv('SEARCH_SERVICE_HOST', 'search-service')
agent_port = os.getenv('SEARCH_SERVICE_PORT', '8080')
agent_url = f"http://{agent_host}:{agent_port}"
```

## Development Guidelines

1. **Iterate on Existing Code**: Look for existing code to iterate on instead of creating new code
2. **Preserve Patterns**: Do not drastically change patterns before trying to iterate on existing ones
3. **Simplicity**: Prefer simple solutions over complex ones
4. **DRY Principle**: Avoid duplication of code
5. **Statelessness**: Design components to be stateless where possible
6. **Configuration Externalization**: Use environment variables from ConfigMaps
7. **Health Management**: Implement proper liveness and readiness probes
8. **File Management**: Follow appropriate file organization and cleanup practices

## File Management and Cleanup

### Directory Structure

- Place all source code files in the appropriate directories under `src/research_system/`
- Store tests in the `tests/` directory, mirroring the source code structure
- Keep documentation in the `docs/` directory
- Place Kubernetes configurations in the `kubernetes/` directory
- Store scripts in the `scripts/` directory

### Temporary Files

- Do not commit temporary files to the repository
- Use `.gitignore` to exclude temporary files and directories
- Common temp files to avoid committing include:
  - `__pycache__/` directories
  - `.pyc` and `.pyo` files
  - Log files generated during development
  - Local database files (when using TinyDB)
  - Environment-specific configuration files

### Pre-Commit Checklist

Before committing changes to Git, verify:

1. All temporary files have been cleaned up
2. New files are placed in the appropriate directories
3. No sensitive information (API keys, passwords) is included
4. Tests are passing with the required coverage
5. Code follows the established patterns and guidelines

```bash
# Commands to clean up before committing
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
find . -name "*.log" -delete
find . -name ".DS_Store" -delete

# Run tests to verify everything works
pytest tests/

# Check test coverage
pytest --cov=research_system tests/
```

## Developer Onboarding and Next Steps

### Getting Started for New Developers

1. **Environment Setup**:
   ```bash
   # Clone the repository
   git clone https://github.com/your-org/k8s-python-app-new.git
   cd k8s-python-app-new
   
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run the app locally
   ./app_manager.sh start
   ```

2. **Familiarize with the Codebase**:
   - Review `src/app.py` to understand the application entry point
   - Explore `src/research_system/core/` to understand core architecture
   - Check `src/research_system/agents/` to see agent implementations
   - Look at `tests/` to understand test structure and coverage

3. **Try the CLI**:
   ```bash
   # List available commands
   ./app_manager.sh help
   
   # Try creating a research task
   ./app_manager.sh task create --title "Test Research" --description "This is a test"
   
   # Run a search
   ./app_manager.sh search --query "Kubernetes Python integration"
   ```

4. **Run Tests**:
   ```bash
   # Run all tests
   ./run_tests.sh
   
   # Run with coverage
   ./run_tests.sh --cov
   
   # Run a specific test suite
   ./run_tests.sh tests/test_integration
   ```

### Next Development Steps

The project has made significant progress on Phase 1 implementation. The following tasks should be prioritized:

1. **Database Migration (COMPLETED)**:
   - ✅ Replaced TinyDB with PostgreSQL
   - ✅ Updated `src/research_system/models/db.py` with dual-backend support
   - ✅ Created SQL schema for PostgreSQL
   - ✅ Added migration utilities
   - ✅ Updated connection handling for Kubernetes

2. **Kubernetes Integration (Partially Completed)**:
   - ✅ Enhanced Kubernetes deployment manifests
   - ✅ Added ConfigMaps for configuration management
   - ✅ Implemented proper health check endpoints
   - ✅ Added resource specifications
   - ⏳ Implement persistent volume monitoring

3. **Search Enhancement (Medium Priority)**:
   - Add caching to search results
   - Implement more sophisticated content extraction
   - Add retry mechanisms for API calls
   - Improve error handling

4. **Testing Improvements (Medium Priority)**:
   - Increase test coverage to at least 90%
   - Add more integration tests
   - Create end-to-end tests with mocked external services
   - Add performance benchmarks

5. **Documentation (Medium Priority)**:
   - Update architecture diagrams
   - Document API endpoints
   - Create deployment guides
   - Add usage examples

## Database Configuration

The system now supports both TinyDB (for development) and PostgreSQL (for production):

```python
# Database model classes
class ResearchTask(BaseModel):
    id: str
    title: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResearchResult(BaseModel):
    id: str
    task_id: str
    content: str
    format: str = "text"  # text, json, html, etc.
    status: str = "draft"  # draft, reviewed, final
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### Database Backend Selection

The system automatically selects the appropriate database backend:

```bash
# Use TinyDB (default for development)
export USE_POSTGRES=false

# Use PostgreSQL (recommended for production)
export USE_POSTGRES=true
export DATABASE_URL="postgresql://postgres:postgres-password@localhost:5432/research"
```

For more detailed information on the database implementation, refer to [DATABASE.md](./docs/DATABASE.md).

### PostgreSQL in Kubernetes

When deploying to Kubernetes, the PostgreSQL database runs as a separate service with persistent storage:

```yaml
# Service for PostgreSQL
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  ports:
  - port: 5432
  selector:
    app: postgres

# Deployment for PostgreSQL
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  selector:
    matchLabels:
      app: postgres
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:16
        env:
        - name: POSTGRES_DB
          value: "research"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
```

## Testing

When writing tests:

- Use pytest for all tests
- Test each component in isolation
- Use mocks for external dependencies
- Write integration tests for end-to-end workflows
- Verify agent communication works correctly
- Test with mock external services
- Create a test for each function implemented
- Aim for 90% code coverage for all new code
- Run coverage reports using pytest-cov

## Common Issues and Solutions

1. **Service Communication Issues**
   - Ensure services are registered correctly
   - Check network policies in Kubernetes
   - Verify environment variables are set correctly

2. **Database Connection Errors**
   - Check database URL in environment variables
   - Ensure database is running and accessible
   - Verify database schema is up to date

3. **Agent Failures**
   - Check agent logs for error messages
   - Verify agent registration with coordinator
   - Ensure required tools are registered

## Documentation

For more detailed information, refer to:

- `docs/DEVELOPER_DOCUMENTATION_GUIDE.md`: Guide to important documentation
- `docs/RESEARCH_SYSTEM_DEV_PLAN.md`: Comprehensive development plan
- `docs/architecture.md`: Architecture diagrams
- `docs/api.md`: API documentation
- `docs/DATABASE.md`: PostgreSQL implementation and migration guide
- `docs/CODE_REVIEW_202504270919pacific.md`: Latest code review with detailed recommendations

## Recent Implementation Progress

The following important changes have recently been completed:

1. **Database Migration to PostgreSQL**:
   - Implemented dual-backend database system supporting both TinyDB and PostgreSQL
   - Created SQL schema and migration utilities
   - Added connection pooling with retry logic
   - Added configuration through environment variables and Kubernetes ConfigMaps
   - Created comprehensive documentation in `docs/DATABASE.md`

2. **Kubernetes Enhancement**:
   - Added proper health check endpoints for liveness and readiness probes
   - Created PostgreSQL deployment and service manifests 
   - Added resource specifications and persistent storage
   - Implemented configuration via ConfigMaps and Secrets
   - Created Docker Compose for local development with PostgreSQL

3. **CLI Implementation**:
   - Added rich text formatting for better user experience
   - Implemented command-line argument parsing and validation
   - Added progress tracking for long-running operations
   - Created table-based output for search results and tasks

4. **Flask App Integration**:
   - Enhanced app.py to integrate with Research System core components
   - Added API endpoints for tasks, plans, and search
   - Implemented proper routing and error handling
   - Connected the Flask app with agent functionality

5. **Testing Infrastructure**:
   - Created Docker/Podman-based testing environment
   - Fixed test compatibility issues
   - Added integration tests for core components
   - Improved test coverage to 62%

6. **Management Scripts**:
   - Added app_manager.sh for common operations
   - Created run_tests.sh for containerized testing
   - Added database setup and migration scripts
   - Added support for coverage reporting

These improvements have completed several key components of the Research System. The database now supports production deployment in Kubernetes, the CLI is fully functional, and the core components are well-integrated, making the system ready for the next phase of development.
