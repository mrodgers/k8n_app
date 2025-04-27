# PostgreSQL Integration Deployment Checklist

This document provides a checklist of items for deploying and testing the PostgreSQL integration in the Research System.

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
   kubectl exec -it deploy/research-system -- python -m research_system.models.db_migration
   ```

## Testing in Local Environment

For testing in a local environment, use:

```bash
# Build and start containers
podman-compose up -d

# Run the database migration
podman exec research-system python -m research_system.models.db_migration

# Check application logs
podman logs -f research-system 

# Run tests
./run_tests.sh --cov
```

## Troubleshooting

If you encounter issues with the PostgreSQL integration:

1. Verify the database connection:
   ```bash
   curl http://localhost:8080/readyz
   ```

2. Check database logs:
   ```bash
   kubectl logs deploy/postgres
   ```

3. Run manual database queries:
   ```bash
   kubectl exec -it deploy/postgres -- psql -U postgres -d research
   ```