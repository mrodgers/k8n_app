# Research System Dashboard MVP

This document outlines the design for a simple MVP of a container-based system dashboard for visualizing and managing the Research System components.

## Overview

The System Dashboard will provide a unified web interface to:

1. Visualize system component status and relationships
2. Monitor system health and performance
3. Manage individual components (start/stop/restart)
4. View logs from all components
5. Configure environment variables and settings

## Architecture

### Core Components

1. **Dashboard Backend**
   - FastAPI application for serving API endpoints
   - WebSocket support for real-time updates
   - Access to container management via Podman API

2. **Dashboard Frontend**
   - React/Vue.js web application
   - Interactive system visualization
   - Component management controls
   - Configuration interface

3. **Metrics Collector**
   - Collects system performance metrics
   - Stores history for trend analysis
   - Minimal performance impact

### Container Integration

The dashboard will use the Podman Socket API to interact with containers:

```
+-------------------------+      +----------------------+
| System Dashboard        |      | Podman Socket API    |
| (Container)             | <--> | /run/podman/podman.sock |
+-------------------------+      +----------------------+
         |                               |
         v                               v
+-------------------------+      +----------------------+
| Database Container      |      | Research System      |
| (PostgreSQL)            |      | (Main Application)   |
+-------------------------+      +----------------------+
                                           |
                                           v
                                  +----------------------+
                                  | Ollama Container     |
                                  | (LLM Services)       |
                                  +----------------------+
```

## Implementation Plan

### Phase 1: Basic Dashboard (MVP)

1. **Container Information Display**
   - List of all containers with status
   - Basic metrics (CPU, memory, uptime)
   - Clickable containers for detailed view
   - System topology visualization

2. **Container Management**
   - Start/stop/restart containers
   - View container logs
   - Simple health status indicators
   - Error notifications

3. **Configuration Management**
   - View and edit environment variables
   - Save configuration changes
   - Configuration history

### Technical Stack (MVP)

- **Backend**: FastAPI (Python)
- **Frontend**: Vue.js + D3.js for visualization
- **Container Management**: Podman API via Python bindings
- **Data Storage**: SQLite for simplicity in MVP
- **Deployment**: Single container with volume mounts for Podman socket

## Implementation Details

### 1. Dashboard Backend

Create a FastAPI application that communicates with Podman:

```python
from fastapi import FastAPI, WebSocket
import podman
import asyncio

app = FastAPI(title="Research System Dashboard")

# Connect to Podman socket
def get_podman_client():
    return podman.PodmanClient(base_url="unix:///run/podman/podman.sock")

@app.get("/containers")
def list_containers():
    client = get_podman_client()
    containers = client.containers.list(all=True)
    return [
        {
            "id": container.id,
            "name": container.name,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else "unknown",
            "created": container.created,
            "labels": container.labels
        }
        for container in containers
    ]

@app.post("/containers/{container_id}/start")
def start_container(container_id: str):
    client = get_podman_client()
    container = client.containers.get(container_id)
    container.start()
    return {"status": "started", "id": container_id}

@app.post("/containers/{container_id}/stop")
def stop_container(container_id: str):
    client = get_podman_client()
    container = client.containers.get(container_id)
    container.stop()
    return {"status": "stopped", "id": container_id}

@app.get("/containers/{container_id}/logs")
def get_container_logs(container_id: str):
    client = get_podman_client()
    container = client.containers.get(container_id)
    logs = container.logs(tail=100).decode("utf-8")
    return {"logs": logs}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client = get_podman_client()
    
    try:
        while True:
            containers = client.containers.list(all=True)
            stats = [
                {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "cpu": container.stats()["cpu_stats"]["cpu_usage"]["total_usage"],
                    "memory": container.stats()["memory_stats"]["usage"]
                }
                for container in containers
            ]
            
            await websocket.send_json({"type": "stats", "data": stats})
            await asyncio.sleep(5)
    except Exception as e:
        await websocket.close()
```

### 2. Dashboard Frontend

Create a Vue.js application with visualization components:

```html
<!-- Container topology visualization -->
<template>
  <div class="topology-view">
    <h2>System Topology</h2>
    <div class="topology-container" ref="topology"></div>
    
    <div class="container-list">
      <div v-for="container in containers" :key="container.id"
           class="container-card" :class="container.status">
        <h3>{{ container.name }}</h3>
        <div class="status">Status: {{ container.status }}</div>
        <div class="controls">
          <button @click="startContainer(container.id)" 
                  :disabled="container.status === 'running'">Start</button>
          <button @click="stopContainer(container.id)"
                  :disabled="container.status !== 'running'">Stop</button>
          <button @click="showLogs(container.id)">Logs</button>
        </div>
      </div>
    </div>
    
    <div v-if="selectedContainer" class="container-details">
      <h3>{{ selectedContainer.name }} Details</h3>
      <pre class="logs">{{ containerLogs }}</pre>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  data() {
    return {
      containers: [],
      selectedContainer: null,
      containerLogs: '',
      socket: null
    }
  },
  
  mounted() {
    this.fetchContainers();
    this.setupWebSocket();
    this.renderTopology();
  },
  
  methods: {
    async fetchContainers() {
      const response = await fetch('/containers');
      this.containers = await response.json();
    },
    
    setupWebSocket() {
      this.socket = new WebSocket(`ws://${window.location.host}/ws`);
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'stats') {
          // Update container stats
          this.updateContainerStats(data.data);
        }
      };
    },
    
    async startContainer(id) {
      await fetch(`/containers/${id}/start`, { method: 'POST' });
      this.fetchContainers();
    },
    
    async stopContainer(id) {
      await fetch(`/containers/${id}/stop`, { method: 'POST' });
      this.fetchContainers();
    },
    
    async showLogs(id) {
      const response = await fetch(`/containers/${id}/logs`);
      const data = await response.json();
      this.containerLogs = data.logs;
      this.selectedContainer = this.containers.find(c => c.id === id);
    },
    
    renderTopology() {
      // Basic D3.js visualization of container relationships
      const svg = d3.select(this.$refs.topology)
        .append('svg')
        .attr('width', 800)
        .attr('height', 600);
        
      // Implement D3.js visualization
    },
    
    updateContainerStats(stats) {
      // Update the container stats with real-time data
      stats.forEach(stat => {
        const container = this.containers.find(c => c.id === stat.id);
        if (container) {
          container.status = stat.status;
          container.cpu = stat.cpu;
          container.memory = stat.memory;
        }
      });
    }
  }
}
</script>
```

### 3. Dockerfile

Create a Dockerfile for the dashboard:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    podman \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend ./backend
COPY frontend/dist ./frontend/dist

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 4. Docker Compose Integration

Update `podman-compose.yml` to include the dashboard:

```yaml
version: '3'
services:
  postgres:
    image: postgres:16
    container_name: research-postgres
    environment:
      - POSTGRES_DB=research
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    container_name: research-ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped

  research-system:
    image: research-system:latest
    container_name: research-system
    environment:
      - DB_USE_POSTGRES=true
      - DATABASE_URL=postgresql://postgres:postgres-password@postgres:5432/research
      - OLLAMA_URL=http://ollama:11434
      - OLLAMA_MODEL=gemma3:1b
      - USE_LLM=true
      - BRAVE_SEARCH_API_KEY=${BRAVE_SEARCH_API_KEY}
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8181
      - MEMORY_VECTOR_SEARCH_ENABLED=false
    ports:
      - "8182:8182"
    depends_on:
      - postgres
      - ollama
    restart: unless-stopped

  system-dashboard:
    image: system-dashboard:latest
    container_name: system-dashboard
    volumes:
      - /run/podman/podman.sock:/run/podman/podman.sock
      - /var/lib/containers:/var/lib/containers:ro
    ports:
      - "8080:8080"
    restart: unless-stopped

volumes:
  postgres_data:
  ollama_data:
```

## Metrics and Monitoring

The dashboard will collect and display the following metrics:

1. **Container Health**
   - Container status (running, stopped, exited, etc.)
   - Uptime
   - Exit codes for stopped containers
   - Restart count

2. **Resource Usage**
   - CPU usage (percentage)
   - Memory usage (current and limit)
   - Disk I/O
   - Network I/O

3. **Application-Specific Metrics**
   - Number of tasks in the system
   - Number of research plans
   - Number of search queries
   - API endpoint response times
   - Database metrics

## Configuration Management

The dashboard will provide a UI to manage configuration:

1. **Environment Variables Editor**
   - Edit `.env` file through UI
   - Validate settings before applying
   - View variable descriptions and defaults

2. **Component Configuration**
   - Database connection settings
   - LLM service settings
   - API timeout and retry settings

3. **System Topology Editor**
   - Visualize and modify component relationships
   - Add/remove components

## Future Enhancements (Post-MVP)

1. **User Authentication**
   - Secure login system
   - Role-based access control
   - Audit logging

2. **Enhanced Visualizations**
   - Historical metric graphs
   - Request flow visualization
   - Performance bottleneck identification

3. **Automated Management**
   - Auto-scaling based on load
   - Health-based recovery actions
   - Scheduled maintenance

4. **System Backup and Restore**
   - Automated backups
   - Point-in-time system restoration
   - Configuration versioning

5. **Alerting System**
   - Email/Slack notifications
   - Alert thresholds configuration
   - Alert escalation rules

## MVP Implementation Timeline

1. **Week 1: Backend Development**
   - Set up FastAPI application
   - Implement Podman API integration
   - Create container management endpoints

2. **Week 2: Frontend Development**
   - Create Vue.js application
   - Implement container list and controls
   - Develop basic visualization

3. **Week 3: Integration and Testing**
   - Connect frontend and backend
   - Implement WebSocket for real-time updates
   - Test with Research System components

4. **Week 4: Deployment and Documentation**
   - Containerize dashboard application
   - Update compose file and test deployment
   - Create user documentation

## Conclusion

This System Dashboard MVP will provide a solid foundation for monitoring and managing the Research System components. By focusing on essential features first, we can quickly deliver value while establishing a framework that can be extended in the future.

The container-based approach ensures the dashboard itself follows the same deployment patterns as the rest of the system, making it easy to integrate into existing workflows and deployment pipelines.