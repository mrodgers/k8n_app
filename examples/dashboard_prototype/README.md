# Research System Dashboard Prototype

This is a simple MVP prototype for visualizing and managing the Research System components using Podman.

## Features

- View all containers and their status
- Start, stop, and restart containers
- View container logs
- Real-time system metrics via WebSocket
- Environment variable management

## Prerequisites

- Python 3.10+
- Podman installed and running
- The Research System containers running via Podman

## Quick Start

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the dashboard:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

3. Open your browser at [http://localhost:8080](http://localhost:8080)

### Running in a Container

1. Build the dashboard container:

```bash
podman build -t system-dashboard .
```

2. Run the dashboard container with access to the Podman socket:

```bash
podman run -d --name system-dashboard \
  -v /run/podman/podman.sock:/run/podman/podman.sock \
  -p 8080:8080 \
  system-dashboard
```

3. Open your browser at [http://localhost:8080](http://localhost:8080)

## API Endpoints

The dashboard exposes the following API endpoints:

- `GET /containers` - List all containers
- `GET /containers/{container_id}` - Get detailed information about a container
- `POST /containers/{container_id}/action` - Perform an action on a container
- `GET /containers/{container_id}/logs` - Get logs from a container
- `GET /containers/{container_id}/stats` - Get real-time statistics for a container
- `GET /system/info` - Get system-wide information
- `GET /images` - List all images
- `GET /env` - Get all environment variables
- `PUT /env` - Update an environment variable

## WebSocket API

Connect to `/ws` to receive real-time container statistics.

## Integration with podman-compose

To include the dashboard in your podman-compose.yml file:

```yaml
services:
  # ... other services ...

  system-dashboard:
    image: system-dashboard:latest
    container_name: system-dashboard
    volumes:
      - /run/podman/podman.sock:/run/podman/podman.sock
    ports:
      - "8080:8080"
    restart: unless-stopped
```

## Security Considerations

This prototype is designed for local development and testing. For production use, consider:

1. Adding authentication
2. Implementing HTTPS
3. Using volume mounts for sensitive data rather than environment variables
4. Implementing proper access control for the Podman socket

## Next Steps

This prototype demonstrates the core functionality needed for a system dashboard. To develop this into a production-ready solution:

1. Enhance the frontend with a modern framework like Vue.js or React
2. Add authentication and authorization
3. Implement more sophisticated visualizations (graphs, topology views)
4. Add alerting and notification capabilities
5. Implement comprehensive system metrics collection

See the full design in the [SYSTEM_DASHBOARD_MVP.md](../../docs/SYSTEM_DASHBOARD_MVP.md) document.