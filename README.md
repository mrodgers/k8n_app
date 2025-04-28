# Research System - Kubernetes FastAPI Application

A containerized Python microservices application built with FastAPI for automated research workflows. This system orchestrates specialized agents for planning, searching, and analyzing research tasks.

## Features

- Agent-based research automation
- Task management with PostgreSQL persistence
- Search capabilities with Brave Search API
- Kubernetes-native deployment
- CLI interface for research operations
- Web-based monitoring dashboard for system status
- Research portal for task creation and management
- LLM integration with Ollama for text generation
- RESTful API for service integration

## Quick Start

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/k8s-python-app-new.git
   cd k8s-python-app-new
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run with TinyDB (development)**:
   ```bash
   ./app_manager.sh start
   ```

4. **Run with Docker Compose (PostgreSQL)**:
   ```bash
   docker-compose up -d
   ```

### Kubernetes Deployment

#### Using the k8s_manager.sh Script (Recommended)

Our `k8s_manager.sh` script automates the entire Kubernetes deployment process:

1. **Setup environment**:
   ```bash
   ./scripts/k8s_manager.sh setup
   ```

2. **Start Kubernetes**:
   ```bash
   ./scripts/k8s_manager.sh start
   ```

3. **Deploy the Research System**:
   ```bash
   ./scripts/k8s_manager.sh deploy
   ```

4. **Verify deployment**:
   ```bash
   ./scripts/k8s_manager.sh status
   ```

For more details, see the [Kubernetes Deployment Guide](./docs/KUBERNETES_DEPLOYMENT_GUIDE.md).

#### Manual Deployment

If you prefer to deploy manually:

1. **Deploy PostgreSQL**:
   ```bash
   kubectl apply -f kubernetes/secrets.yaml
   kubectl apply -f kubernetes/postgres.yaml
   ```

2. **Deploy the Research System**:
   ```bash
   kubectl apply -f kubernetes/configmaps.yaml
   kubectl apply -f kubernetes/deployment.yaml
   kubectl apply -f kubernetes/service.yaml
   ```

3. **Verify deployment**:
   ```bash
   kubectl get pods
   kubectl get services
   ```

## Database Migration

The system supports both TinyDB (for development) and PostgreSQL (for production). To migrate data from TinyDB to PostgreSQL:

1. **Run the database setup script**:
   ```bash
   ./scripts/setup_db.sh --migrate --tinydb-path ./data/research.json
   ```

2. **Configure environment for PostgreSQL**:
   ```bash
   export USE_POSTGRES=true
   export DATABASE_URL="postgresql://postgres:postgres-password@localhost:5432/research"
   ```

3. **Verify migration**:
   ```bash
   python -c "from research_system.models.db import Database; db = Database(); print(f'Tasks: {len(db.list_tasks())}')"
   ```

## CLI Usage

The system includes a command-line interface for common operations:

```bash
# Start the server
./app_manager.sh start

# Create a task
./app_manager.sh task create --title "Research Project" --description "Research the latest ML techniques"

# Run a search
./app_manager.sh search --query "machine learning techniques 2025" --max-results 10

# List tasks
./app_manager.sh task list

# Get a specific task
./app_manager.sh task get --id <task-id>
```

## Web Interfaces

The system includes two web-based interfaces: a monitoring dashboard and a research portal.

### Dashboard

The monitoring dashboard provides real-time visibility into:

- System resource usage (CPU, memory, disk)
- Agent status and registered tools
- Database connection and statistics
- Research tasks and results

To access the dashboard:

1. Start the server using `./app_manager.sh start` or deploy to Kubernetes
2. Navigate to `http://localhost:8181/dashboard/` in your browser
3. The dashboard automatically refreshes every 10 seconds

The dashboard also provides JSON API endpoints for programmatic access to monitoring data:

- `/dashboard/api/status` - Complete system status
- `/dashboard/api/agents` - Agent information
- `/dashboard/api/system` - System resource usage
- `/dashboard/api/database` - Database status and statistics
- `/dashboard/api/tasks` - Recent research tasks
- `/dashboard/api/results` - Recent research results

### Research Portal

The Research Portal provides a user-friendly interface for creating and managing research tasks:

- Create new research tasks with titles, descriptions, and tags
- View all research tasks with their status
- Generate research plans
- Execute searches
- View research results

To access the Research Portal:

1. Start the server using `./app_manager.sh start` or deploy to Kubernetes
2. Navigate to `http://localhost:8181/research/` in your browser

The Research Portal interacts with the system through RESTful API endpoints:

- `/api/tasks` - List or create research tasks
- `/api/tasks/{task_id}` - Get a specific task
- `/api/tasks/{task_id}/plan` - Create a research plan
- `/api/tasks/{task_id}/search` - Execute a search for a task
- `/api/tasks/{task_id}/results` - Get all results for a task

For more details on the web interfaces, see [Web Interfaces Documentation](./docs/WEB_INTERFACES.md).

## Configuration

The system can be configured using:

1. **Environment variables**:
   - `USE_POSTGRES`: Set to "true" to use PostgreSQL
   - `DATABASE_URL`: PostgreSQL connection string
   - `LOG_LEVEL`: Logging level (info, debug, etc.)

2. **ConfigMap in Kubernetes**:
   - Edit `kubernetes/configmaps.yaml` for application settings

3. **Local config file**:
   - Edit `config.yaml` for local development

## Testing

The system uses containerized testing with Podman to ensure consistent test environments:

```bash
# Run all tests
./run_tests.sh

# Run with coverage reporting
./run_tests.sh --cov

# Run specific tests
./run_tests.sh tests/test_postgres_db.py

# Clean up stale containers before testing
./run_tests.sh --clean

# Skip rebuilding the container (faster for iterative testing)
./run_tests.sh --no-build tests/test_cli

# Use a specific PostgreSQL database for testing
./run_tests.sh --db-url postgresql://user:pass@localhost:5432/testdb
```

For database testing best practices and more detailed information, see [Database Testing Guide](./docs/DATABASE_TESTING.md).

## Project Structure

```
k8s-python-app-new/
├── docker-compose.yml       # Local development with Docker
├── Dockerfile               # Container definition
├── kubernetes/              # K8s manifests
│   ├── configmaps.yaml
│   ├── deployment.yaml
│   ├── postgres.yaml
│   ├── secrets.yaml
│   └── service.yaml
├── scripts/                 # Helper scripts
│   ├── setup_db.sh          # Database setup
│   ├── k8s_manager.sh       # Kubernetes management
│   └── ollama/              # Ollama LLM utilities
├── app_manager.sh           # Application management
├── src/                     # Application source
│   ├── app.py               # Main entry point
│   └── research_system/     # Core components
│       ├── agents/          # Agent implementations
│       ├── cli/             # CLI interface
│       ├── core/            # Core system components
│       │   ├── coordinator.py
│       │   ├── dashboard.py # Monitoring dashboard
│       │   └── server.py
│       ├── llm/             # LLM integration
│       └── models/          # Data models
├── static/                  # Static assets for web UI
├── templates/               # HTML templates for web UI
├── tests/                   # Test suite
└── requirements.txt         # Dependencies
```

## Documentation

For more detailed information, see:

- [Developer Documentation Guide](./docs/DEVELOPER_DOCUMENTATION_GUIDE.md)
- [Research System Development Plan](./docs/RESEARCH_SYSTEM_DEV_PLAN.md)
- [Architecture Documentation](./docs/architecture.md)
- [API Documentation](./docs/API_DOCUMENTATION.md)
- [Database Documentation](./docs/DATABASE.md)
- [Database Testing Guide](./docs/DATABASE_TESTING.md)
- [Health Monitoring](./docs/HEALTH_ENDPOINTS.md)
- [Kubernetes Deployment Guide](./docs/KUBERNETES_DEPLOYMENT_GUIDE.md)
- [Deployment Checklist](./docs/DEPLOYMENT_CHECKLIST.md)
- [Web Interfaces Documentation](./docs/WEB_INTERFACES.md)
- [Implementation Summary](./docs/IMPLEMENTATION_SUMMARY.md)
- [Monitoring Dashboard Guide](./docs/DASHBOARD.md)
- [LLM Integration Guide](./docs/LLM_INTEGRATION.md)

## License

This project is licensed under the terms of the LICENSE file included in the repository.