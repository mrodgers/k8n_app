# Research System Dashboard Prototype

This is a lightweight dashboard for monitoring and managing containers in the Research System.

## Features

- View all containers and their statuses
- Start, stop, and restart containers
- View container logs
- Simple and responsive UI for easy management

## Prerequisites

- Python 3.7+
- FastAPI and Uvicorn
- Podman installed and running
- The Research System containers running via Podman

## Quick Start

### Using the Simple Dashboard (Recommended)

1. Start the dashboard with the provided script:

```bash
./start_dashboard.sh
```

2. Open your browser at [http://localhost:8299](http://localhost:8299)

3. Stop the dashboard when finished:

```bash
./stop_dashboard.sh
```

### Local Development Mode

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the direct dashboard:

```bash
python direct_dashboard.py
```

3. Open your browser at [http://localhost:8199](http://localhost:8199)

### Running in a Container (Advanced)

1. Build the dashboard container:

```bash
podman build -t system-dashboard .
```

2. Run the dashboard container with access to the Podman socket:

```bash
podman run -d --name system-dashboard \
  -v /run/podman/podman.sock:/run/podman/podman.sock \
  -p 8199:8199 \
  system-dashboard
```

3. Open your browser at [http://localhost:8199](http://localhost:8199)

## API Endpoints

The direct dashboard exposes the following API endpoints:

- `GET /containers` - List all containers
- `GET /containers/{container_id}` - Get detailed information about a container
- `POST /containers/{container_id}/action` - Perform an action on a container
- `GET /containers/{container_id}/logs` - Get logs from a container
- `GET /debug/containers` - Debug view of container data

## Available Dashboard Versions

- `direct_dashboard.py` - Simple version that directly uses Podman CLI commands (recommended)
- `main_direct.py` - WebSocket-enabled dashboard with more features
- `main.py` - Original prototype using Podman socket API

## Troubleshooting

If you encounter issues with the dashboard:

1. Check if containers are visible via command line:
   ```bash
   podman ps -a
   ```

2. Verify the dashboard logs for errors:
   ```bash
   cat dashboard.log
   ```

3. Check if the port is available:
   ```bash
   lsof -i :8199
   ```

4. Access the debug endpoint for raw container data:
   ```
   http://localhost:8199/debug/containers
   ```

5. Make sure you have the right permissions to run Podman commands

## Security Considerations

This prototype is designed for local development and testing only. For production use, consider:

1. Adding authentication
2. Implementing HTTPS
3. Implementing proper access control

## Technical Notes

- The dashboard uses Podman CLI commands directly rather than the socket API for better compatibility
- API responses are normalized to handle different Podman output formats
- The dashboard automatically parses standard Podman table output if JSON format fails
- Container actions include start, stop, and restart operations

See the full design in the [SYSTEM_DASHBOARD_MVP.md](../../docs/SYSTEM_DASHBOARD_MVP.md) document.