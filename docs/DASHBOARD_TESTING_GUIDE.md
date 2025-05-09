# Dashboard Testing Guide

This guide provides comprehensive instructions for testing the Research System Dashboard. It covers manual testing, automated testing, and integrating the dashboard into your existing workflow.

## Prerequisites

Before testing the dashboard, ensure you have:

1. Podman installed and properly configured
2. Python 3.10+ with pip
3. Access to the Research System repository
4. The Research System up and running

## Testing Options

There are multiple ways to test the dashboard:

1. **Manual Testing**: Running the dashboard and interacting with it directly
2. **Automated Testing**: Using the provided test scripts and pytest integration
3. **Continuous Integration**: Incorporating dashboard tests into your CI pipeline

## 1. Manual Testing

### Option A: Using the test_dashboard.sh script

The simplest way to test the dashboard is using the provided script:

```bash
cd examples/dashboard_prototype
./test_dashboard.sh
```

This script will:
1. Start the Dashboard (either in container or development mode)
2. Start the Research System if it's not already running
3. Create a test task and plan
4. Run a test search query
5. Keep the dashboard running for inspection

### Option B: Running in container mode manually

If you prefer more control:

```bash
# Build the dashboard container
cd examples/dashboard_prototype
podman build -t system-dashboard .

# Start the dashboard container
podman run -d --name system-dashboard \
  -v /run/podman/podman.sock:/run/podman/podman.sock \
  -v "$(pwd)/../../.env:/app/.env:ro" \
  -p 8090:8080 \
  system-dashboard

# Start the Research System (if not already running)
cd ../..
./app_manager.sh start

# Create a test task
./app_manager.sh task create --title "Dashboard Test" --description "Testing with dashboard"

# Get the task ID from the output and create a plan
./app_manager.sh plan create --task-id <TASK_ID>

# Run a search query
./app_manager.sh search --query "Testing dashboard with Python"
```

Then navigate to http://localhost:8090 in your browser to access the dashboard.

### Option C: Running in development mode

For development and debugging:

```bash
# Install dependencies
cd examples/dashboard_prototype
pip install -r requirements.txt

# Start the dashboard
python main.py

# In another terminal, start the Research System
cd /path/to/research-system
./app_manager.sh start

# Create test data (task, plan, search)
./app_manager.sh task create --title "Test Task" --description "Testing dashboard"
```

Access the dashboard at http://localhost:8080.

## 2. Automated Testing

### Using pytest

The repository includes a pytest integration test for the dashboard:

```bash
# Install test dependencies
pip install pytest pytest-cov websocket-client

# Run the dashboard integration tests
python -m pytest tests/test_integration/test_dashboard_integration.py -v
```

This test suite verifies:
- Dashboard API endpoints functionality
- Dashboard integration with Research System operations
- Real-time WebSocket updates from the dashboard

### What the Tests Verify

1. **API Endpoint Tests**:
   - Listing containers
   - Getting container details
   - Viewing container logs
   - Retrieving system information
   - Listing images

2. **Research System Integration**:
   - Creating tasks through the API
   - Creating plans
   - Running search queries
   - Verifying operations appear in logs

3. **Real-time Updates**:
   - WebSocket connection
   - Container statistics updates

## 3. Testing Dashboard Features

Once the dashboard is running, verify these key features:

### Container Management

- [ ] **View Containers**: All Research System containers are visible
- [ ] **Container Status**: Status (running, stopped) is correctly displayed
- [ ] **Start/Stop/Restart**: Controls work correctly for each container
- [ ] **Container Details**: Clicking on a container shows detailed information

### Logs and Monitoring

- [ ] **View Logs**: Select different containers and verify logs are displayed
- [ ] **Real-time Updates**: Stats and status update without manual refresh
- [ ] **System Overview**: Check metrics for accuracy (running containers, etc.)

### Configuration Management

- [ ] **View Environment Variables**: Variables from .env are displayed
- [ ] **Edit Variables**: Editing a variable persists the change
- [ ] **Sensitive Data**: Password/key fields are masked for security

## 4. Integration with podman-compose

To include the dashboard in your existing podman-compose setup:

```yaml
# Add to your podman-compose.yml
services:
  # ... existing services ...
  
  system-dashboard:
    image: system-dashboard:latest
    container_name: system-dashboard
    volumes:
      - /run/podman/podman.sock:/run/podman/podman.sock
      - ./.env:/app/.env:ro
    ports:
      - "8090:8080"
    restart: unless-stopped
```

Then run:

```bash
podman-compose up -d
```

## 5. Performance Testing

For larger deployments, test dashboard performance:

1. **Multiple Containers**: Start 10+ containers and check dashboard responsiveness
2. **Long-running Operation**: Let the dashboard run for 24+ hours to check for memory leaks
3. **Concurrent Operations**: Perform multiple operations while monitoring the dashboard

## 6. Troubleshooting

### Common Issues and Solutions

1. **Cannot Connect to Dashboard**
   - Verify the container is running: `podman ps | grep system-dashboard`
   - Check port mapping: `podman port system-dashboard`
   - Check logs: `podman logs system-dashboard`

2. **Dashboard Shows No Containers**
   - Verify the Podman socket is correctly mounted
   - Check permissions on the Podman socket
   - Run with elevated privileges if needed

3. **WebSocket Connection Failures**
   - Ensure no firewall is blocking WebSocket connections
   - Check browser console for error messages
   - Verify the dashboard container has network access

4. **Environment Variables Not Showing**
   - Verify the .env file is correctly mounted
   - Check file permissions on the .env file
   - Look for error messages in dashboard logs

## 7. Continuous Integration

To add dashboard testing to your CI pipeline:

```yaml
# Example GitHub Actions workflow
jobs:
  test-dashboard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov websocket-client
          pip install -r requirements.txt
          pip install -r examples/dashboard_prototype/requirements.txt
      - name: Setup Podman
        run: |
          sudo apt-get update
          sudo apt-get install -y podman
      - name: Build and start dashboard
        run: |
          cd examples/dashboard_prototype
          podman build -t system-dashboard .
          podman run -d --name system-dashboard -v /run/podman/podman.sock:/run/podman/podman.sock -p 8090:8080 system-dashboard
      - name: Run tests
        run: |
          python -m pytest tests/test_integration/test_dashboard_integration.py -v
```

## Conclusion

The System Dashboard provides valuable visibility and management capabilities for the Research System. By thoroughly testing its features and integration, you can ensure it enhances your operational workflow rather than adding complexity.

Regular dashboard testing should be part of your Research System maintenance routine, especially after updates or changes to the container configuration.