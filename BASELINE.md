# Working Baseline

This document captures the current state of the application as a working baseline.

## Current State
- **Framework**: FastAPI (migrated from Flask)
- **Branch**: working-baseline
- **Last Verified**: April 28, 2025

## Functionality
The application is a Research System with:
- Task management capabilities
- Search functionality
- LLM integration with Ollama
- RESTful API interface
- Web-based dashboard and research portal

## Verified Working Features
- Health check endpoint (/health)
- Root endpoint (/)
- API endpoints for tasks, results, and LLM operations
- Container-based deployment via Podman

## Running the Application
```bash
# Start the application
./app_manager.sh start

# Check application status
./app_manager.sh status

# Access in browser
# Open http://localhost:8181
```

## Tests
The application includes tests that can be run using:
```bash
# Run all tests
python -m pytest

# Or in a container for consistent environments
podman run --rm -v $(pwd)/tests:/app/tests -v $(pwd)/src:/app/src test-app python -m pytest tests/
```

## Database Options
- TinyDB (for development)
- PostgreSQL (for production)

## Configuration
Application configuration is managed through:
- config.yaml file
- Environment variables
- Kubernetes ConfigMaps (for k8s deployment)

## Dependencies
See requirements.txt for the full list of dependencies.

This baseline serves as a reference point for future development.