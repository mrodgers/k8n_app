# Research System Database Documentation

This document provides information about the database implementation for the Research System. The system supports both TinyDB (for development) and PostgreSQL (for production) backends.

## Database Architecture

The Research System uses a dual-backend approach to database storage:

1. **TinyDB**: A lightweight, file-based JSON database for development and testing
2. **PostgreSQL**: A robust, production-ready relational database for deployment in Kubernetes

The system automatically selects the appropriate backend based on configuration.

## Data Models

### ResearchTask

```python
class ResearchTask(BaseModel):
    id: str                           # Unique identifier
    title: str                        # Task title 
    description: str                  # Detailed description
    status: str = "pending"           # pending, in_progress, completed, failed
    created_at: float                 # Creation timestamp
    updated_at: float                 # Last update timestamp
    assigned_to: Optional[str] = None # Agent assigned to this task
    tags: List[str] = []              # Categorization tags
    metadata: Dict[str, Any] = {}     # Additional properties
```

### ResearchResult

```python
class ResearchResult(BaseModel):
    id: str                           # Unique identifier
    task_id: str                      # Reference to parent task
    content: str                      # Result content
    format: str = "text"              # text, json, html, etc.
    status: str = "draft"             # draft, reviewed, final
    created_at: float                 # Creation timestamp
    updated_at: float                 # Last update timestamp
    created_by: Optional[str] = None  # Agent or system that created this result
    tags: List[str] = []              # Categorization tags
    metadata: Dict[str, Any] = {}     # Additional properties
```

## PostgreSQL Schema

The PostgreSQL implementation uses the following schema:

### Tables

**tasks**
- `id`: VARCHAR(64) PRIMARY KEY
- `title`: VARCHAR(255) NOT NULL
- `description`: TEXT NOT NULL
- `status`: VARCHAR(20) NOT NULL DEFAULT 'pending'
- `created_at`: DOUBLE PRECISION NOT NULL
- `updated_at`: DOUBLE PRECISION NOT NULL
- `assigned_to`: VARCHAR(64)
- `tags`: JSONB DEFAULT '[]'
- `metadata`: JSONB DEFAULT '{}'

**results**
- `id`: VARCHAR(64) PRIMARY KEY
- `task_id`: VARCHAR(64) NOT NULL REFERENCES tasks(id) ON DELETE CASCADE
- `content`: TEXT NOT NULL
- `format`: VARCHAR(20) NOT NULL DEFAULT 'text'
- `status`: VARCHAR(20) NOT NULL DEFAULT 'draft'
- `created_at`: DOUBLE PRECISION NOT NULL
- `updated_at`: DOUBLE PRECISION NOT NULL
- `created_by`: VARCHAR(64)
- `tags`: JSONB DEFAULT '[]'
- `metadata`: JSONB DEFAULT '{}'

### Indexes

- `tasks_status_idx`: Index on tasks.status
- `tasks_assigned_idx`: Index on tasks.assigned_to
- `results_task_id_idx`: Index on results.task_id
- `results_status_idx`: Index on results.status
- `results_created_by_idx`: Index on results.created_by

## Configuration

### Environment Variables

The database backend can be configured using the following environment variables:

- `USE_POSTGRES`: Set to "true" to use PostgreSQL (default: "false")
- `DATABASE_URL`: PostgreSQL connection string (e.g., "postgresql://user:password@host:port/dbname")
- `DB_POSTGRES_HOST`: PostgreSQL host
- `DB_POSTGRES_PORT`: PostgreSQL port
- `DB_POSTGRES_DBNAME`: PostgreSQL database name
- `DB_POSTGRES_USER`: PostgreSQL username
- `DB_POSTGRES_PASSWORD`: PostgreSQL password
- `DB_TINYDB_PATH`: Path to the TinyDB database file (default: "./data/research.json")

### Kubernetes Configuration

In Kubernetes, the database is configured using ConfigMaps and Secrets:

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: research-system-config
data:
  config.yaml: |
    database:
      use_postgres: true
      postgres:
        host: postgres
        port: 5432
        dbname: research
        connect_timeout: 5
        retry_attempts: 3

# Secret
apiVersion: v1
kind: Secret
metadata:
  name: research-system-db-credentials
type: Opaque
stringData:
  DB_POSTGRES_PASSWORD: postgres-password
```

## Migration from TinyDB to PostgreSQL

The system includes utilities for migrating data from TinyDB to PostgreSQL:

### Using the Migration Script

```bash
# Run the database migration script
./scripts/setup_db.sh --migrate --tinydb-path ./data/research.json

# Migration with custom PostgreSQL connection
./scripts/setup_db.sh --host mydb.example.com --port 5432 --db research \
  --user dbuser --password dbpass --migrate
```

### Programmatic Migration

```python
from research_system.models.db_migration import DatabaseMigrator

# Create a migrator
migrator = DatabaseMigrator(
    source_db_path="./data/research.json",
    target_connection_string="postgresql://user:password@localhost:5432/research"
)

# Migrate all data
results = migrator.migrate_all()
print(f"Migrated {results['tasks']} tasks and {results['results']} results")

# Verify migration
verification = migrator.verify_migration()
if verification["all_verified"]:
    print("Migration successful!")
else:
    print("Migration had some issues")
```

## Connection Management

The PostgreSQL implementation includes:

- Connection pooling with automatic reconnection
- Exponential backoff for retries
- Error handling for common database issues
- Transaction management

### Example Usage

```python
from research_system.models.db import Database, generate_id, ResearchTask

# Create a database instance
db = Database()  # Auto-selects backend based on environment

# Create a task
task = ResearchTask(
    id=generate_id(),
    title="Research Task",
    description="This is a test task"
)
db.create_task(task)

# Retrieve and update a task
retrieved_task = db.get_task(task.id)
retrieved_task.status = "in_progress"
db.update_task(retrieved_task)

# List tasks with filtering
active_tasks = db.list_tasks(status="in_progress")
for task in active_tasks:
    print(f"Task: {task.title} ({task.id})")
```

## Best Practices

1. **Auto-select backend**: Use the `Database` class which automatically selects the appropriate backend based on configuration.
2. **Generate IDs**: Use the `generate_id()` function to create unique UUIDs for new records.
3. **Use transactions**: The PostgreSQL implementation automatically handles transactions.
4. **Filter queries**: Use the filtering parameters in list methods for better performance.
5. **Handle errors**: Wrap database operations in try/except blocks to handle potential errors.

## Database Initialization

When using PostgreSQL, the tables are automatically created if they don't exist. For a more controlled setup, you can:

```bash
# Initialize database schema
psql -h localhost -U postgres -d research -f scripts/schema.sql

# Or use the setup script
./scripts/setup_db.sh
```