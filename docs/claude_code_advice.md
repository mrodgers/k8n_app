# Code Development Best Practices

*Last updated: April 27, 2025*

This document consolidates code development best practices for the Research System project, combining general software engineering principles with Kubernetes-specific guidelines and Claude agentic coding patterns.

> **Note**: For a comprehensive guide to all project documentation, refer to the [Developer Documentation Guide](./DEVELOPER_DOCUMENTATION_GUIDE.md).

## Table of Contents

1. [Project-Specific Guidelines](#project-specific-guidelines)
2. [Kubernetes Design Principles](#kubernetes-design-principles)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing Best Practices](#testing-best-practices)
6. [Claude Code Workflows](#claude-code-workflows)
7. [Configuration Management](#configuration-management)

## Project-Specific Guidelines

These guidelines are specific to the Research System project:

- **Iterate on Existing Code**: Look for existing code to iterate on instead of creating new code from scratch
- **Preserve Patterns**: Do not drastically change patterns before trying to iterate on existing patterns
- **Server Management**: 
  - Always start a new server after making changes to test them
  - Kill all existing related servers before starting a new one
- **Environment Awareness**: Write code that accounts for different environments: dev, test, and prod
- **Scope Management**: Only make well-understood changes related to the requested task
- **Simplicity**: Prefer simple solutions over complex ones
- **DRY Principle**: Avoid duplication of code across the codebase
- **File Size**: Keep files under 200-300 lines of code for better maintainability
- **Comprehensive Testing**: Write thorough tests for all major functionality
- **Production Code Quality**: Do not add stubbing or fake data patterns to production code
- **File Organization**:
  - Place files in the appropriate directories based on their purpose
  - Follow the established project structure
  - Clean up temporary files before committing changes

## File Management and Organization

### Directory Structure

Follow the established project structure when adding new files:

```
k8s-python-app-new/
├── src/
│   ├── app.py                      # Main application entry point
│   └── research_system/
│       ├── cli/                    # CLI interface components
│       ├── core/                   # Core components
│       ├── agents/                 # Agent implementations
│       ├── models/                 # Data models
│       └── utils/                  # Utility functions
├── tests/                          # Test suite (mirror src/ structure)
├── kubernetes/                     # Kubernetes configuration files
├── docs/                           # Documentation
└── scripts/                        # Development and utility scripts
```

### Temporary Files

The following temporary files and directories should not be committed to the repository:

- Python cache files (`__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`)
- Log files generated during development or testing
- Local database files (`.db`, `.sqlite`)
- Environment-specific configuration files (local settings)
- Operating system files (`.DS_Store`, `Thumbs.db`)
- Virtual environment directories (`venv/`, `.env/`)
- IDE configuration files (`.idea/`, `.vscode/`)
- Temporary output files from tests or builds

### Pre-Commit Verification

Before committing changes, always perform these verification steps:

1. **Clean Temporary Files**:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -delete
   find . -name "*.log" -delete
   ```

2. **Verify File Placement**:
   - Ensure all new files are in the appropriate directories
   - Follow the established project structure
   - Avoid creating files in the root directory unless necessary

3. **Check for Sensitive Information**:
   - No API keys or credentials in the code
   - No hardcoded secrets or passwords
   - All sensitive values should use environment variables

4. **Run Tests and Coverage**:
   ```bash
   pytest tests/
   pytest --cov=research_system tests/
   ```

5. **Verify Code Quality**:
   - Code follows PEP 8 style guidelines
   - No unused imports or variables
   - Documentation is up to date

## Kubernetes Design Principles

When implementing Kubernetes-based solutions, adhere to these design principles:

1. **Statelessness**: 
   - Design components to be stateless where possible
   - Store state in external databases or caches
   - Implement idempotent operations

2. **Configuration Externalization**: 
   - Use environment variables from ConfigMaps
   - Avoid hardcoded configuration values
   - Implement a deep merge function for combining configurations

3. **Health Management**: 
   - Implement proper liveness probe endpoint (`/healthz`)
   - Implement readiness probe endpoint (`/readyz`)
   - Add dependency checking in readiness probes

4. **Resource Efficiency**: 
   - Set appropriate resource requests and limits
   - Configure appropriate memory and CPU allocations
   - Monitor resource usage and adjust as needed

5. **Observability**: 
   - Implement structured logging (JSON format)
   - Add Prometheus metrics endpoints
   - Set up tracing for distributed services

## Code Organization

### Service Discovery

Replace hardcoded URLs with environment-based service discovery:

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

### State Management

Replace file-based storage with distributed database solutions:

- **PostgreSQL** with persistent volumes for relational data
- **MongoDB** with StatefulSet for document-based data
- **Redis** for caching and temporary data

## Development Workflow

### Explore, Plan, Code, Commit

This versatile workflow suits many problems:

1. **Explore**:
   - Read relevant files, images, or URLs to understand the codebase
   - Consider using subagents for complex problems to verify details or investigate particular questions

2. **Plan**:
   - Create a detailed plan for approaching the problem
   - Consider creating a document or GitHub issue with the plan for reference

3. **Code**:
   - Implement the solution according to the plan
   - Verify the reasonableness of the solution during implementation

4. **Commit**:
   - Commit the solution with clear commit messages
   - Update documentation as needed

### Test-Driven Development

This workflow is particularly effective for changes that are easily verifiable with tests:

1. **Write Tests**:
   - Write tests based on expected input/output pairs
   - Run the tests to confirm they fail
   - Commit the tests when satisfied with them

2. **Implement Code**:
   - Write code that passes the tests
   - Iterate until all tests pass
   - Use independent verification to ensure the implementation isn't overfitting
   - Commit the code once satisfied

## Testing Best Practices

### Unit Tests

- Test individual components in isolation
- Use mocks for external dependencies
- Cover edge cases and error handling
- Test both success and failure paths

### Integration Tests

- Test end-to-end workflows
- Verify inter-agent communication
- Test with mock external services
- Validate result quality and formatting

### Test Structure

- Use appropriate test fixtures
- Organize tests by component and functionality
- Add descriptive test names that explain what's being tested
- Follow the Arrange-Act-Assert pattern

### Code Coverage

- Create tests for each function implemented
- Aim for 90% code coverage for all new code
- Use pytest-cov to generate coverage reports
- Include coverage checks in the CI/CD pipeline
- Address any coverage gaps before merging new code

## Claude Code Workflows

When using Claude Code for development, consider these effective patterns:

### Customize Your Setup

- Create a **CLAUDE.md** file in your repository root to document:
  - Common commands and utilities
  - Core files and functions
  - Code style guidelines
  - Testing instructions
  - Repository workflows
  - Developer environment setup

### Effective Prompting Techniques

- **Be Specific**: Provide clear, detailed instructions
- **Include Context**: Reference relevant files and code
- **Request Plans**: Ask Claude to plan before implementing
- **Course Correct Early**: Guide Claude's approach actively
- **Use Checklists**: For complex multi-step tasks, have Claude use a checklist

### Code Review and Verification

- Have Claude review its own code for potential issues
- Use verification steps to catch logic errors
- Run tests to verify implementations work as expected

### Codebase Navigation

Use Claude for codebase exploration by asking questions like:

- How does [specific feature] work?
- How do I implement a new [component]?
- What does this code on line X of file Y do?
- What edge cases does this implementation handle?

## Configuration Management

### Environment Variables

Use environment variables for configuration with sensible defaults:

```python
# Example configuration loading with environment variables
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/db')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info')
```

### Kubernetes ConfigMaps and Secrets

- Use ConfigMaps for non-sensitive configuration
- Use Secrets for sensitive information like API keys
- Mount configuration as files or environment variables depending on complexity

### Configuration Validation

- Validate configuration at startup
- Fail fast if required configuration is missing
- Provide clear error messages for configuration issues

---

These guidelines aim to provide a comprehensive framework for developing high-quality, maintainable code for the Research System project. By adhering to these practices, we can ensure our codebase remains robust, scalable, and adaptable to changing requirements.
