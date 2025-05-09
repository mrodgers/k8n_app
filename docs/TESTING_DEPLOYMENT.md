# Testing and Deployment Guide

*Last updated: May 9, 2025*

This document provides comprehensive guidance for testing and deploying the Research System application, with specific focus on local development environments and containerized deployments using Podman and uv. It includes detailed setup instructions, troubleshooting steps, and best practices based on recent deployment experiences.

## Environment Setup

### Python Environment with uv

The Research System uses `uv` for Python environment management due to its speed and reliability compared to traditional pip/venv workflows.

```bash
# Create a virtual environment with uv
uv venv

# Activate the environment
source .venv/bin/activate  # On Unix/Mac
# or
.\.venv\Scripts\activate   # On Windows

# Install dependencies with uv
uv pip install -r requirements.txt
```

### Container Environment with Podman

The system uses Podman instead of Docker for container management. This is important to remember when running containerized components.

```bash
# Check podman version
podman --version

# Check running containers
podman ps

# View container logs
podman logs <container-name>
```

### Environment Configuration with .env

The system uses a `.env` file to configure various aspects of the application. Create or modify this file in the project root directory:

```bash
# Database Configuration
# Set to true to use PostgreSQL, false for TinyDB
DB_USE_POSTGRES=false  # Use false for development without PostgreSQL

# Full database URL (overrides individual settings)
DATABASE_URL=postgresql://postgres:postgres-password@localhost:5432/research

# Individual PostgreSQL settings (used if DATABASE_URL is not set)
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
DB_POSTGRES_DBNAME=research
DB_POSTGRES_USER=postgres
DB_POSTGRES_PASSWORD=postgres-password

# LLM Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
PLANNER_LLM_MODEL=gemma3:1b
SEARCH_LLM_MODEL=gemma3:1b
USE_LLM=true

# Web Search Configuration
BRAVE_SEARCH_API_KEY='your-brave-search-api-key'

# Application Settings
LOG_LEVEL=info
SERVER_HOST=0.0.0.0
SERVER_PORT=8181
API_TIMEOUT=30
CORS_ORIGINS=*
MEMORY_VECTOR_SEARCH_ENABLED=false  # Set to true if pgvector extension is available
```

Important notes about environment variables:
- Ensure python-dotenv is installed: `pip install python-dotenv`
- Make sure environment variable names in `.env` match what the code expects
- For PostgreSQL password, verify it matches the one in your podman-compose.yml
- For vector search, enable only if pgvector extension is installed in PostgreSQL

## Testing Workflow

### Local Testing

For testing code changes in a local development environment:

1. Ensure your Python environment is activated (using uv):
   ```bash
   source .venv/bin/activate
   ```

2. Start the server in development mode:
   ```bash
   PYTHONPATH=./src python src/app.py
   ```

3. Test endpoints using curl:
   ```bash
   curl http://localhost:8181/health
   curl http://localhost:8181/healthz
   curl http://localhost:8181/readyz
   ```

### Container Testing

For testing with containerized deployments:

1. Build the container with the latest changes:
   ```bash
   ./scripts/build_container.sh --patch
   ```

2. Check for the container image:
   ```bash
   podman images | grep research-system
   ```

3. Stop existing containers if any:
   ```bash
   podman stop python-app
   podman rm python-app
   ```

4. Run the new container:
   ```bash
   podman run -d --name python-app -p 8080:8181 localhost/research-system:latest
   ```

5. Test endpoints using curl:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8080/healthz
   curl http://localhost:8080/readyz
   ```

6. Check container logs:
   ```bash
   podman logs -f python-app
   ```

## Troubleshooting

### Module Import Issues

When you encounter import errors like `ModuleNotFoundError: No module named 'src.research_system'`:

1. Fix import paths to use direct imports:
   ```python
   # Change this:
   from src.research_system.core.server import FastMCPServer

   # To this:
   from research_system.core.server import FastMCPServer
   ```

2. Update the PYTHONPATH environment variable:
   ```bash
   # When running directly:
   PYTHONPATH=. python src/app.py

   # When using app_manager.sh:
   PYTHONPATH=./src ./app_manager.sh start
   ```

3. For a more permanent solution, create or update `src/research_system/__init__.py` to ensure Python searches in the correct paths.

### PostgreSQL Connection Issues

When you encounter PostgreSQL connection errors like `FATAL: password authentication failed for user "postgres"`:

1. Verify PostgreSQL container is running:
   ```bash
   podman ps | grep postgres
   ```

2. Check if the password in `.env` matches the one in your container setup:
   ```bash
   # Check podman-compose.yml for password setting
   grep -r POSTGRES_PASSWORD podman-compose.yml

   # Make sure it matches your .env file
   grep DB_POSTGRES_PASSWORD .env
   ```

3. Test connecting to PostgreSQL directly:
   ```bash
   # Connect to PostgreSQL in the container
   podman exec research-postgres psql -U postgres -c "SELECT 1"
   ```

4. If connection issues persist, fall back to TinyDB by setting `DB_USE_POSTGRES=false` in your `.env` file.

### Vector Search and Document System Issues

When encountering errors related to the pgvector extension like `extension "vector" is not available`:

1. Check if pgvector is installed in PostgreSQL:
   ```bash
   podman exec research-postgres psql -U postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
   ```

2. If not available, you have two options:

   a. Install pgvector (for full functionality):
   ```bash
   # Enter PostgreSQL container
   podman exec -it research-postgres bash

   # Inside container, install pgvector
   apt-get update && apt-get install -y postgresql-16-pgvector

   # Enable the extension
   psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

   b. Disable vector search (easier workaround):
   ```bash
   # Add or update in .env file
   MEMORY_VECTOR_SEARCH_ENABLED=false
   ```

### Port Binding Issues

When port binding fails with `Connection in use: ('0.0.0.0', 8181)`:

1. Check what process is using the port:
   ```bash
   lsof -i :8181
   # or
   sudo lsof -i :8181
   # or
   netstat -anp tcp | grep 8181
   ```

2. Kill the process using the port:
   ```bash
   kill -9 <PID>
   ```

3. Verify port is free before starting the server:
   ```bash
   python -c "import socket; s = socket.socket(); s.bind(('0.0.0.0', 8181)); print('Port 8181 is free'); s.close()"
   ```

### Container Version Discrepancies

When container doesn't reflect code changes:

1. Check when the container was built:
   ```bash
   podman inspect python-app | grep -i created
   ```

2. Check what's inside the container:
   ```bash
   podman exec -it python-app find /app -type f -name "*.py"
   podman exec -it python-app cat /app/src/app.py
   ```

3. Verify environment variables in the container:
   ```bash
   podman exec -it python-app env | grep -i build
   ```

4. Rebuild the container with the latest code:
   ```bash
   ./scripts/build_container.sh --patch
   podman stop python-app
   podman rm python-app
   podman run -d --name python-app -p 8080:8181 localhost/research-system:latest
   ```

### LLM Integration Issues

When encountering errors related to Ollama like `Request URL is missing an 'http://' or 'https://' protocol`:

1. Check Ollama container is running:
   ```bash
   podman ps | grep ollama
   ```

2. Ensure URL format in `.env` includes the protocol:
   ```bash
   # Correct format with protocol
   OLLAMA_URL=http://localhost:11434

   # Incorrect format (missing protocol)
   # OLLAMA_URL=localhost:11434
   ```

3. Check logs for more specific errors:
   ```bash
   ./app_manager.sh logs
   ```

4. Test direct communication with Ollama:
   ```bash
   curl http://localhost:11434/api/version
   ```

## Using the App Manager Script

The `app_manager.sh` script provides a convenient way to manage the application:

```bash
# Start the server
./app_manager.sh start

# Check server status
./app_manager.sh status

# Stop the server
./app_manager.sh stop

# View server logs
./app_manager.sh logs

# Create a research task
./app_manager.sh task create --title "Test Task" --description "Testing deployment"

# Create a research plan
./app_manager.sh plan create --task-id <task-id>

# Run a search query
./app_manager.sh search --query "Python Kubernetes integration"
```

The script handles environment variables and paths automatically, making it easier to work with the application.

## Important Learnings

1. **Import Path Management**:
   - Always use relative imports within packages (`from research_system.core import X`)
   - Never use absolute imports from src (`from src.research_system import X`)
   - Set PYTHONPATH correctly before running commands
   - Avoid circular imports by organizing code hierarchically

2. **Container Rebuild Requirements**:
   - Any changes to code must be followed by a container rebuild
   - The container shows the code at build time, not the current state of the codebase
   - Use build numbers to track container versions

3. **Environment Configuration**:
   - Use `.env` file for configuration and make sure python-dotenv is installed
   - Ensure passwords match between `.env` and container configuration
   - For PostgreSQL, make sure the database connection parameters are correct
   - For Ollama URL, ensure the protocol (http://) is included

4. **Database Strategy**:
   - TinyDB works well for development (set `DB_USE_POSTGRES=false`)
   - PostgreSQL is needed for production deployments
   - The vector search feature requires pgvector extension in PostgreSQL
   - If pgvector is unavailable, disable with `MEMORY_VECTOR_SEARCH_ENABLED=false`

5. **Testing Health Endpoints**:
   - Always test health endpoints after deployment
   - Imports within endpoint functions help avoid module caching issues
   - Check for version and build number in health endpoint responses

6. **Podman vs Docker Commands**:
   - Use `podman` instead of `docker` for all container operations
   - Remember that podman uses slightly different networking than Docker
   - Use `podman-compose` instead of `docker-compose` for multi-container setups
   - Container networking may differ between Podman and Docker

## Complete Deployment Process

### 1. Local Setup and Testing

- [ ] Clone the repository and set up the Python environment
- [ ] Create or update `.env` file with appropriate configuration
- [ ] Install required dependencies with `pip install -r requirements.txt`
- [ ] Start the app with `./app_manager.sh start` and verify it's running
- [ ] Test core functionality (tasks, plans, search)

### 2. Database Configuration

- [ ] Decide whether to use TinyDB or PostgreSQL
- [ ] If using PostgreSQL, verify container is running
- [ ] Check database connection parameters match in `.env` file
- [ ] Set `DB_USE_POSTGRES` appropriately (true/false)
- [ ] For vector search: Install pgvector or disable with `MEMORY_VECTOR_SEARCH_ENABLED=false`

### 3. Containerized Deployment

- [ ] Update version number and build number in version.py
- [ ] Run all tests locally with `./run_tests.sh`
- [ ] Build container with `./scripts/build_container.sh --patch`
- [ ] Test container locally with appropriate port mapping
- [ ] Verify all health endpoints show correct version info
- [ ] Test all relevant API endpoints through container
- [ ] Check container logs for errors
- [ ] Ensure changes follow project conventions and guidelines

### 4. Kubernetes Deployment

- [ ] Update Kubernetes manifests with the latest image tag and configuration
- [ ] Apply ConfigMaps and Secrets first
- [ ] Deploy PostgreSQL and Ollama services if needed
- [ ] Deploy the application
- [ ] Verify pods are running with `kubectl get pods`
- [ ] Check logs with `kubectl logs <pod-name>`
- [ ] Test endpoints through the Kubernetes service
- [ ] Verify health and readiness probes are working

### 5. Verification and Rollback Plan

- [ ] Verify all functionality with integration tests
- [ ] Perform a simple workflow task end-to-end
- [ ] Monitor system for any errors after deployment
- [ ] Have a rollback plan in case of issues
- [ ] Document any new configuration or deployment steps

## Reference Commands

### Essential Development Commands

```bash
# Start development server
PYTHONPATH=. python src/app.py

# Run tests
pytest tests/

# Build container
./scripts/build_container.sh --patch

# Start container
podman run -d --name python-app -p 8080:8181 localhost/research-system:latest

# Check health endpoint
curl http://localhost:8080/health
```

### Useful Debugging Commands

```bash
# Check imported modules
python -c "import sys; print(sys.modules.keys())"

# Verify Python path
python -c "import sys; print(sys.path)"

# Find all Python files in project
find . -name "*.py" | grep -v "__pycache__"

# Check container filesystem
podman exec -it python-app ls -la /app/src

# Test if version module is properly imported
PYTHONPATH=./src python -c "from research_system.version import get_version_info; print(get_version_info())"
```