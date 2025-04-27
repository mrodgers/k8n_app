# PostgreSQL Integration and Deployment Checklist

This document provides a checklist for deploying, testing, and verifying the PostgreSQL integration in the Research System.

## Implementation Status

The PostgreSQL database integration has been implemented with the following key features:

- [x] Dual-backend architecture supporting both TinyDB and PostgreSQL
- [x] Environment-based configuration for selecting database backend
- [x] PostgreSQL connection handling with retry mechanism
- [x] Database schema creation with proper indices and constraints 
- [x] Robust JSONB support for storing complex data types
- [x] Migration utilities for transferring data between backends
- [x] Kubernetes integration via environment variables
- [x] Dockerized PostgreSQL for development and testing

## Testing Status

The tests for the PostgreSQL implementation are partially completed:

- [x] Core CRUD operations for tasks and results
- [x] Database factory class testing
- [x] Basic test infrastructure for isolated testing
- [ ] Testing with actual PostgreSQL instances in Docker
- [ ] Full integration testing with the CLI

## Testing Checklist

Before deploying or pushing to git, perform the following tests:

### Local Testing

- [ ] Run application with TinyDB backend:
  ```bash
  export USE_POSTGRES=false
  ./app_manager.sh start
  ```

- [ ] Test basic operations with TinyDB:
  ```bash
  # Create a task
  ./app_manager.sh task create --title "Test Task" --description "Test"
  
  # List tasks
  ./app_manager.sh task list
  
  # Stop the server
  ./app_manager.sh stop
  ```

### Containerized Testing

- [ ] Build and start containers with Podman Compose:
  ```bash
  podman-compose build
  podman-compose up -d
  ```

- [ ] Test PostgreSQL connectivity:
  ```bash
  # Check if the server responds
  curl http://localhost:8181/healthz
  curl http://localhost:8181/readyz
  
  # Test operations with PostgreSQL
  ./app_manager.sh task create --title "PostgreSQL Test" --description "Testing PostgreSQL"
  ./app_manager.sh task list
  ```

- [ ] Clean up containers:
  ```bash
  podman-compose down
  ```

### Unit Tests

- [ ] Run the full test suite:
  ```bash
  ./run_tests.sh
  ```

- [ ] Check for database-specific test failures:
  ```bash
  ./run_tests.sh tests/test_postgres_db.py
  ```

- [ ] Run tests with coverage:
  ```bash
  ./run_tests.sh --cov
  ```

### Kubernetes Configuration Verification

- [ ] Validate Kubernetes configurations:
  ```bash
  # Validate deployment
  kubectl apply --dry-run=client -f kubernetes/deployment.yaml
  
  # Validate PostgreSQL service
  kubectl apply --dry-run=client -f kubernetes/postgres.yaml
  
  # Validate ConfigMap and Secret
  kubectl apply --dry-run=client -f kubernetes/configmaps.yaml
  kubectl apply --dry-run=client -f kubernetes/secrets.yaml
  ```

## Remaining Work

The following items need to be completed:

1. **Fix PostgreSQL Schema Tests**:
   - Fix the list_results test to properly handle the schema context
   - Fix the delete_task test to handle foreign key constraints

2. **Improve Test Infrastructure**:
   - Enhance the Docker test environment to properly set up PostgreSQL
   - Fix the initialization of test schemas in the PostgreSQL database

3. **Update Documentation**:
   - Complete the DATABASE.md documentation with detailed usage instructions
   - Add deployment instructions for Kubernetes

4. **Fix Pydantic Compatibility Issues**:
   - Update all .dict() calls to use .model_dump() for Pydantic v2 compatibility

5. **Improve Error Handling**:
   - Enhance error messages for database connection issues
   - Add more robust recovery mechanisms for database failures

## Deployment Steps

When deploying to a Kubernetes environment, follow these steps:

1. **Set Up PostgreSQL**:
   ```bash
   kubectl apply -f kubernetes/postgres.yaml
   ```

2. **Configure Secrets**:
   ```bash
   kubectl apply -f kubernetes/secrets.yaml
   ```

3. **Configure the Application**:
   ```bash
   kubectl apply -f kubernetes/configmaps.yaml
   ```

4. **Deploy the Application**:
   ```bash
   kubectl apply -f kubernetes/deployment.yaml
   kubectl apply -f kubernetes/service.yaml
   ```

5. **Initialize Database (if needed)**:
   ```bash
   kubectl exec -it deploy/research-system -- python -m src.research_system.models.db_migration
   ```

## Testing in Local Environment

For testing in a local environment, use:

```bash
# Build and start containers
podman-compose up -d

# Run the database migration
podman exec research-system python -m src.research_system.models.db_migration

# Check application logs
podman logs -f research-system 

# Run tests
./run_tests.sh --cov
```

## Potential Issues and Solutions

### TinyDB Not Found

If you encounter errors about TinyDB not being found:
```
ModuleNotFoundError: No module named 'tinydb'
```

Solution: Ensure requirements.txt is up to date and all dependencies are installed with:
```bash
pip install -r requirements.txt
```

### PostgreSQL Connection Issues

If the application fails to connect to PostgreSQL:
```
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed
```

Solutions:
1. Verify PostgreSQL is running: `podman ps | grep postgres`
2. Check connection string: `echo $DATABASE_URL`
3. Verify credentials in environment variables

### Health Check Failures

If health checks fail:
```
{"status": "not_ready", "dependencies": {"database": false}}
```

Solution:
1. Check database connectivity
2. Verify environment variables are correctly set
3. Check logs for specific errors: `./app_manager.sh logs`

## Final Verification

- [ ] All tests are passing
- [ ] Documentation is up to date
- [ ] Code follows established patterns and guidelines
- [ ] No temporary files or sensitive information is included
- [ ] The application works with both TinyDB and PostgreSQL backends