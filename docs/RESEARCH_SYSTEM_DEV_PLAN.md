# Research System Development Plan
*Last updated: April 28, 2025*

> **Important**: This document outlines development best practices. For API documentation, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md). For health monitoring, see [HEALTH_ENDPOINTS.md](./HEALTH_ENDPOINTS.md).

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
