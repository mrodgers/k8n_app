
April 26, 2025:

For a developer joining the project at the beginning of Phase 1, here are the key files to review to get up to speed quickly:
Core Architecture Files

research_system/core/coordinator.py

This is the central component that orchestrates the entire system
Shows how FastMCP servers are mounted together
Demonstrates how tools from different agents are coordinated
Provides a clear picture of the overall workflow


research_system/core/server.py

Contains the main FastMCP server implementation
Shows the system-level tools and resources
Helps understand the entry points for the research system



Agent Implementation Files

research_system/agents/planner.py

Shows how to implement a specialized FastMCP agent
Demonstrates the research planning functionality
Good example of a simple but functional agent implementation


research_system/agents/search.py

More complex agent example with external API integration
Shows how to use FastMCP's Context for progress reporting
Demonstrates LLM sampling for content extraction



Data & Models

research_system/models/db.py

Contains the database implementation
Shows how research tasks and results are stored
Important for understanding data persistence in the system



User Interface

research_system/cli/main.py

Shows how users interact with the system
Demonstrates how to use the FastMCP Client to communicate with the server
Provides examples of command-line interface design



Testing

tests/conftest.py and tests/test_search.py

Shows how to test FastMCP components
Demonstrates mocking external dependencies
Provides patterns for test-driven development



Configuration
Use Podman, not docker for testing.
docker-compose.yml and Dockerfile

Shows how the system is containerized and deployed
Provides context for the development environment



Implementation Order
For a developer starting work on Phase 1, I would recommend reviewing the files in this order:

Start with coordinator.py to understand the overall architecture
Move to server.py to see the system entry points
Review planner.py and search.py to understand agent implementation
Look at db.py to understand data persistence
Check main.py (CLI) to see how users interact with the system
Review testing files to understand the testing approach
Finally, review the Docker configuration to understand the deployment setup

This order provides a top-down understanding of the system, starting with the high-level architecture and working down to implementation details and deployment considerations.

# VIBE_GUIDE_phase1 - UPDATE
*Last updated: April 27, 2025*

## Current Status Assessment

After reviewing the codebase, I've determined that we are in the early stages of Phase 1 implementation for the research system. The following is a detailed assessment of the current state:

### Completed Components

1. **Core Architecture**:
   - `research_system/core/coordinator.py`: The central orchestration component is well-structured
   - `research_system/core/server.py`: The FastMCP server implementation is in place

2. **Partial Agent Implementation**:
   - `research_system/agents/planner.py`: The planning agent is fully implemented
   - `research_system/agents/search.py`: The search agent appears to be incomplete

3. **Data Models**:
   - `research_system/models/db.py`: Database implementation using TinyDB is complete

4. **Basic Containerization**:
   - `Dockerfile`: Basic container definition exists

### Missing or Incomplete Components

1. **User Interface**:
   - CLI interface is incomplete: `research_system/cli/main.py` placeholder exists but lacks implementation

2. **Testing**:
   - Only basic Flask app tests exist
   - Missing recommended test files (`conftest.py`, `test_search.py`)
   - No comprehensive tests for core components

3. **Deployment Configuration**:
   - No `docker-compose.yml` for local development
   - No Kubernetes manifests for deployment

## Kubernetes Considerations

Since this is a Kubernetes-based solution, several design and implementation factors need to be considered:

1. **Service Discovery**: 
   - The current `coordinator.py` assumes hardcoded URLs
   - Need to implement Kubernetes service discovery mechanisms

2. **Configuration Management**:
   - Current configuration loading is basic and file-based
   - Should be updated to use Kubernetes ConfigMaps and Secrets

3. **Health Checks**:
   - Basic health endpoint exists but needs expansion
   - Should implement proper liveness and readiness probes for Kubernetes

4. **Resource Management**:
   - No resource specifications for containers
   - Need to define CPU/memory requests and limits

5. **Stateful Components**:
   - TinyDB is file-based and not suitable for distributed environments
   - Need to consider persistent volumes or migrate to a more suitable database

6. **Logging and Monitoring**:
   - Basic logging exists but lacks structured formatting
   - Need to implement proper logging for Kubernetes environments (JSON format)

## Recommended Next Steps

### 1. Complete Core Implementation

- **Complete Search Agent**:
  - Finish implementation of `search.py`
  - Ensure proper integration with external APIs
  - Implement LLM sampling for content extraction

- **Implement CLI Interface**:
  - Create a robust CLI for user interaction
  - Allow for task creation, monitoring, and result retrieval

### 2. Kubernetes-Specific Enhancements

- **Service Discovery**:
  - Modify the coordinator to use Kubernetes DNS for service discovery
  - Implement a configurable service naming scheme

- **Configuration**:
  - Create Kubernetes ConfigMap templates
  - Update config loading to use environment variables

- **Database**:
  - Consider replacing TinyDB with a Kubernetes-compatible database
  - Options include MongoDB, PostgreSQL with persistent volumes

### 3. Deployment Configuration

- **Kubernetes Manifests**:
  - Create Deployment manifests for each component
  - Define Service objects for internal communication
  - Set up Ingress for external access if needed

- **Development Environment**:
  - Create a docker-compose.yml for local development
  - Ensure compatibility between local and K8s environments

### 4. Testing and CI/CD

- **Enhanced Testing**:
  - Implement comprehensive unit tests for all components
  - Create integration tests for the full system
  - Set up a CI/CD pipeline for automated testing
  - Ensure tests cover Kubernetes-specific behaviors

### 5. Documentation

- **System Architecture**:
  - Document the overall Kubernetes architecture
  - Create diagrams showing service relationships
  - Document scaling considerations

- **Operational Guides**:
  - Create deployment instructions
  - Document monitoring and troubleshooting procedures
  - Provide examples for common operations

## Kubernetes-Specific Design Principles

When implementing these next steps, keep these Kubernetes-centric design principles in mind:

1. **Statelessness**: Design components to be stateless where possible to facilitate scaling
2. **Configuration Externalization**: All configuration should be externalized via ConfigMaps and Secrets
3. **Graceful Failure Handling**: Components should handle node failures and restarts gracefully
4. **Resource Efficiency**: Be mindful of resource usage, especially in multi-tenant clusters
5. **Service Isolation**: Clearly define service boundaries and interfaces
6. **Observability**: Implement comprehensive logging, metrics, and tracing

Following these guidelines will ensure the research system is properly adapted for Kubernetes environments and can take full advantage of container orchestration benefits.


- After making changes, ALWAYS make sure to start up a new server so I can test it.
- Always look for existing code to iterate on instead of creating new code.
- Do not drastically change the patterns before trying to iterate on existing patterns.
- Always kill all existing related servers that may have been created in previous testing before trying to start a new server.
- Always prefer simple solutions
- Avoid duplication of code whenever possible, which means checking for other areas of the codebase that might already have similar code and functionality
- Write code that takes into account the different environments: dev, test, and prod
- You are careful to only make changes that are requested or you are confident are well understood and related to the change being requested
- When fixing an issue or bug, do not introduce a new pattern or technology without first exhausting all options for the existing implementation. And if you finally do this, make sure to remove the old implementation afterwards so we don't have duplicate logic.
- Keep the codebase very clean and organized
- Avoid writing scripts in files if possible, especially if the script is likely only to be run once
- Avoid having files over 200-300 lines of code. Refactor at that point.
- Mocking data is only needed for tests, never mock data for dev or prod
- Never add stubbing or fake data patterns to code that affects the dev or prod environments
- Never overwrite my .env file without first asking and confirming
- Focus on the areas of code relevant to the task
- Do not touch code that is unrelated to the task
- Write thorough tests for all major functionality
- Avoid making major changes to the patterns and architecture of how a feature works, after it has shown to work well, unless explicitly instructed
- Always think about what other methods and areas of code might be affected by code changes