# Phase 1 Development Plan: Research Agent System - UPDATE
*Last updated: April 27, 2025*

This document updates the implementation plan for Phase 1 of the Research Agent System, with a focus on Kubernetes integration and current development status.

## Current Implementation Status

Based on code review, the project is in the early stages of Phase 1 implementation:

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
- Comprehensive tests (only basic Flask app tests exist)

## Kubernetes-Specific Considerations

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
```python
# Current approach (needs modification)
def load_config():
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Kubernetes-friendly approach
def load_config():
    # Primary source: Environment variables (from ConfigMap/Secrets)
    config = {
        "app": {
            "port": int(os.getenv("APP_PORT", "8080")),
            "max_workers": int(os.getenv("APP_MAX_WORKERS", "4"))
        },
        "logging": {
            "level": os.getenv("LOGGING_LEVEL", "INFO")
        },
        "environment": os.getenv("ENVIRONMENT", "development"),
        "brave_search": {
            "api_key": os.getenv("BRAVE_SEARCH_API_KEY")
        }
    }
    
    # Secondary source (optional): ConfigMap mounted as file
    config_path = os.getenv("CONFIG_PATH")
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                # Deep merge the configs
                deep_merge(config, file_config)
        except Exception as e:
            logger.warning(f"Failed to load file config: {e}")
    
    return config
```

### 3. State Management

**Current State:** TinyDB is used for data persistence, which is file-based and not suitable for Kubernetes.

**Required Changes:**
- Replace TinyDB with a Kubernetes-compatible database:
  - PostgreSQL with persistent volumes
  - MongoDB with StatefulSet
  - Redis for caching and temporary data

Example PostgreSQL implementation:
```python
# models/db.py (PostgreSQL version)
import psycopg2
import psycopg2.extras
import json
import os
import time
import uuid
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        # Get database configuration from environment variables
        self.host = os.getenv("DB_HOST", "postgres")
        self.port = os.getenv("DB_PORT", "5432")
        self.dbname = os.getenv("DB_NAME", "research")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")
        
        self.conn = None
        self.initialize()
    
    def connect(self):
        """Establish database connection"""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
        return self.conn
    
    def initialize(self):
        """Initialize database schema"""
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                # Create tasks table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    assigned_to VARCHAR(50),
                    tags JSONB,
                    metadata JSONB
                )
                ''')
                
                # Create results table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS results (
                    id VARCHAR(36) PRIMARY KEY,
                    task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
                    content TEXT NOT NULL,
                    format VARCHAR(20) NOT NULL DEFAULT 'text',
                    status VARCHAR(20) NOT NULL DEFAULT 'draft',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(50),
                    tags JSONB,
                    metadata JSONB,
                    CONSTRAINT fk_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
                ''')
                
                conn.commit()
                logger.info("Database schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
```

### 4. Health Checks and Readiness

**Current State:** Basic health endpoint exists but lacks Kubernetes-specific probes.

**Required Changes:**
```python
# Add to server.py
@app.get("/healthz")
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive"}

@app.get("/readyz")
async def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    # Check database connection
    try:
        db_healthy = self.db.is_healthy()
    except Exception:
        db_healthy = False
    
    # Check external service connections if applicable
    try:
        services_healthy = all(agent.is_healthy() for agent in self.agents.values())
    except Exception:
        services_healthy = False
    
    if db_healthy and services_healthy:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")
```

### 5. Resource Specifications

**Current State:** No resource specifications for containers.

**Required Changes:**
Create Kubernetes deployment manifests with appropriate resource requests and limits:

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-coordinator
  namespace: research-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: research-coordinator
  template:
    metadata:
      labels:
        app: research-coordinator
    spec:
      containers:
      - name: coordinator
        image: research-system:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        env:
        - name: DB_HOST
          value: postgres
        - name: SEARCH_SERVICE_HOST
          value: search-service
        - name: PLANNER_SERVICE_HOST
          value: planner-service
        - name: BRAVE_SEARCH_API_KEY
          valueFrom:
            secretKeyRef:
              name: research-secrets
              key: brave-search-api-key
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
      volumes:
      - name: config-volume
        configMap:
          name: research-config
```

## Updated Implementation Plan

Based on the current status and Kubernetes requirements, here's the updated implementation plan for Phase 1:

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

- **Integration Tests**
  - Test end-to-end research workflows
  - Verify inter-agent communication
  - Test with mock external services
  - Validate research result quality

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

## Updated Project Structure

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
│   ├── researcher_dev_plan.md
│   ├── phase_1_researcher_dev.md
│   ├── architecture.md             # Enhanced with K8s diagrams
│   └── api.md                      # API documentation
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

## Kubernetes Design Principles

When implementing these changes, adhere to these Kubernetes-centric design principles:

1. **Statelessness**: Design components to be stateless where possible
   - Move all state to external databases
   - Avoid local file storage
   - Design for multiple replicas when applicable

2. **Configuration Externalization**:
   - Use environment variables from ConfigMaps
   - Store secrets in Kubernetes Secrets
   - Avoid hardcoded values in code

3. **Health Management**:
   - Implement proper liveness and readiness probes
   - Add graceful shutdown handling
   - Include connection retry logic for dependencies

4. **Resource Efficiency**:
   - Set appropriate resource requests and limits
   - Optimize container size and memory usage
   - Consider horizontal scaling for appropriate components

5. **Observability**:
   - Implement structured logging (JSON format)
   - Add metrics for Prometheus scraping
   - Include tracing for request flows

## Updated Requirements

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

## Conclusion

This updated development plan addresses the current state of the Phase 1 implementation and provides a clear roadmap for completing it with proper Kubernetes integration. By focusing on the high-priority items first, the team can quickly establish a functioning research system while ensuring it's properly designed for Kubernetes deployment.

The plan balances implementation speed with proper architecture, ensuring that the resulting system will be robust, maintainable, and scalable in a Kubernetes environment.