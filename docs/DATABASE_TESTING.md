# Database Testing Guide

This guide documents best practices for testing database functionality in the Research System, based on our experiences implementing PostgreSQL integration.

## Container-Based Testing

Our system uses containerized testing with Podman to ensure consistent environments:

```bash
# Run all tests with a clean environment
./run_tests.sh --clean

# Run specific database tests
./run_tests.sh tests/test_postgres_db.py

# Use a custom test database
./run_tests.sh --db-url postgresql://user:pass@localhost:5432/testdb
```

### Benefits of Container Testing

- Consistent environments for all developers
- Isolation from development databases
- No need to install dependencies locally
- Clean teardown after test completion

## Database Test Isolation Strategies

### Schema-Based Isolation

We use unique schema names for each test run:

```python
# Create a unique schema name for test isolation
test_schema = f"test_{uuid.uuid4().hex[:8]}"

# Modify connection string to use the test schema
conn_string = f"{base_conn}/{dbname}?options=-c%20search_path%3D{test_schema}"
```

This approach allows multiple tests to run simultaneously against the same database without interfering with each other.

### Automatic Schema Cleanup

After tests complete, schemas are automatically dropped:

```python
# Clean up the schema
conn = psycopg2.connect(TEST_DB_URL)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute(f"DROP SCHEMA IF EXISTS {test_schema} CASCADE")
conn.close()
```

## Testing Without a Database

### Mock Database Implementation

For environments without PostgreSQL, we provide a mock implementation:

```python
# Apply the mock
monkeypatch.setattr(psycopg2, 'connect', mock_connect)

# Create a mock PostgreSQL database
db = PostgreSQLDatabase(conn_string)
        
# Mock the database operations to use in-memory storage
db._memory_tasks = {}
db._memory_results = {}
```

### Graceful Degradation

Our database implementation automatically falls back to TinyDB if PostgreSQL isn't available:

```python
# Determine which database backend to use
use_postgres = os.getenv("USE_POSTGRES", "false").lower() in ("true", "1", "yes")
db_url = connection_string or os.getenv("DATABASE_URL", "")

if use_postgres or db_url:
    try:
        # Try to import psycopg2 to see if it's available
        import psycopg2
        self.db = PostgreSQLDatabase(connection_string)
        logger.info("Using PostgreSQL database backend")
    except ImportError:
        logger.warning("psycopg2 not available, falling back to TinyDB")
        self.db = TinyDBDatabase(db_path)
else:
    logger.info("Using TinyDB database backend")
    self.db = TinyDBDatabase(db_path)
```

## Resilient Database Operations

### Retry Mechanism

We implement retry logic with exponential backoff for database operations:

```python
def _execute_with_retry(self, operation_name, callback, max_retries=3):
    """Execute a database operation with retry logic."""
    retries = 0
    while retries < max_retries:
        try:
            conn = self._get_connection()
            result = callback(conn)
            if not conn.closed:
                conn.commit()
            return result
        except psycopg2.OperationalError as e:
            logger.warning(f"Operational error in {operation_name}: {str(e)}. Retrying...")
            self.conn = None  # Force reconnection
            retries += 1
            if retries >= max_retries:
                logger.error(f"Failed to execute {operation_name} after {max_retries} retries")
                raise
            time.sleep(0.5 * retries)  # Exponential backoff
        except Exception as e:
            logger.error(f"Error in {operation_name}: {str(e)}")
            if not conn.closed:
                conn.rollback()
            raise
```

### Handling JSON Fields

PostgreSQL's JSONB fields require special handling:

```python
# Handle tags field
if data['tags'] is None:
    data['tags'] = []
elif isinstance(data['tags'], str):
    data['tags'] = json.loads(data['tags'])
# For PostgreSQL's json/jsonb type
elif hasattr(data['tags'], '__iter__') and not isinstance(data['tags'], (str, bytes)):
    # Already a proper iterable object, no conversion needed
    pass
```

## Test Fixtures

### Data Fixtures

We use pytest fixtures for consistent test data:

```python
@pytest.fixture
def test_task_data():
    """Fixture providing test task data."""
    return {
        "id": generate_id(),
        "title": "Test Task",
        "description": "This is a test task for the database implementation.",
        "status": "pending",
        "created_at": time.time(),
        "updated_at": time.time(),
        "assigned_to": "test_user",
        "tags": ["test", "database"],
        "metadata": {"priority": 1, "source": "test"}
    }
```

### Database Fixtures

Database connections are provided as fixtures:

```python
@pytest.fixture
def postgres_db(monkeypatch) -> Generator[PostgreSQLDatabase, None, None]:
    """
    Fixture providing a PostgreSQL database instance.
    
    This fixture uses a mock implementation if a real database is not available.
    """
    if not HAS_POSTGRES:
        pytest.skip("PostgreSQL library not available")
    
    # Create a unique schema name for test isolation
    test_schema = f"test_{uuid.uuid4().hex[:8]}"
    
    # Test code here...
    
    yield db
    
    # Cleanup
    conn = psycopg2.connect(TEST_DB_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f"DROP SCHEMA IF EXISTS {test_schema} CASCADE")
    conn.close()
```

## Common Testing Issues

### Schema Conflicts

If tests fail with schema-related errors:

- Ensure schema names are unique per test run
- Check for proper schema cleanup after tests
- Try running with the `--clean` flag to reset the environment

### Container Issues

If container tests fail:

- Run with `--clean` to remove stale containers
- Check podman/docker status with `podman info`
- Ensure sufficient disk space for container images

### Connection Problems

When database connection issues occur:

- Verify TEST_DATABASE_URL is correctly formatted
- Check that PostgreSQL is running and accessible
- Consider creating a dedicated test database user with appropriate permissions