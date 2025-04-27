# PostgreSQL Database Migration Checklist

This document provides a checklist for testing and verifying the PostgreSQL database migration implementation before pushing to git.

## Code Quality Verification

- [x] PostgreSQL database implementation completed
- [x] TinyDB implementation preserved for development
- [x] Auto-detection of database backend implemented
- [x] Migration utilities for transferring data between backends
- [x] Database configuration file created
- [x] Kubernetes YAML files created/updated
- [x] Docker Compose configuration created
- [x] Documentation updated in CLAUDE.md and DATABASE.md

## Testing Checklist

Before pushing to git, perform the following tests:

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
  curl http://localhost:8080/healthz
  curl http://localhost:8080/readyz
  
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