"""
Research System Dashboard MVP - Backend Prototype

This module implements a simple FastAPI backend for visualizing and managing
the Research System components using Podman API.
"""

import os
import subprocess
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel

app = FastAPI(
    title="Research System Dashboard",
    description="Management interface for Research System components",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ContainerInfo(BaseModel):
    id: str
    name: str
    image: str
    status: str
    created: str
    ports: Optional[List[Dict[str, Any]]] = None
    labels: Optional[Dict[str, str]] = None

class ContainerStats(BaseModel):
    id: str
    name: str
    cpu_percent: float
    mem_usage: str
    mem_limit: str
    mem_percent: float
    net_in: str
    net_out: str

class ContainerAction(BaseModel):
    action: str  # start, stop, restart

class EnvVarUpdate(BaseModel):
    key: str
    value: str

# Helper functions to interact with podman
def run_podman_command(args: List[str]) -> Dict[str, Any]:
    """Run a podman command and return the parsed JSON result."""
    try:
        # Execute podman command
        result = subprocess.run(
            ["podman"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON output
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {}
    except subprocess.CalledProcessError as e:
        # Handle podman command errors
        raise HTTPException(
            status_code=500,
            detail=f"Podman command failed: {e.stderr}"
        )
    except json.JSONDecodeError:
        # Handle JSON parsing errors
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse podman output as JSON"
        )

# API Endpoints

@app.get("/containers", response_model=List[ContainerInfo])
def list_containers():
    """List all containers with their basic information."""
    containers = run_podman_command(["ps", "-a", "--format", "json"])
    
    if not isinstance(containers, list):
        return []
    
    return containers

@app.get("/containers/{container_id}")
def get_container_info(container_id: str):
    """Get detailed information about a specific container."""
    container = run_podman_command(["inspect", container_id])
    if not container or not isinstance(container, list) or len(container) == 0:
        raise HTTPException(status_code=404, detail="Container not found")
    return container[0]

@app.post("/containers/{container_id}/action")
def container_action(container_id: str, action: ContainerAction):
    """Perform an action (start, stop, restart) on a container."""
    if action.action not in ["start", "stop", "restart"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {action.action}. Must be 'start', 'stop', or 'restart'"
        )
    
    try:
        run_podman_command([action.action, container_id])
        return {"success": True, "container_id": container_id, "action": action.action}
    except HTTPException as e:
        return {"success": False, "container_id": container_id, "error": str(e.detail)}

@app.get("/containers/{container_id}/logs")
def get_container_logs(container_id: str, tail: int = 100):
    """Get the logs from a specific container."""
    try:
        result = subprocess.run(
            ["podman", "logs", "--tail", str(tail), container_id],
            capture_output=True,
            text=True,
            check=True
        )
        return {"container_id": container_id, "logs": result.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get logs: {e.stderr}"
        )

@app.get("/containers/{container_id}/stats")
def get_container_stats(container_id: str):
    """Get real-time statistics for a specific container."""
    try:
        stats = run_podman_command(["stats", "--no-stream", "--format", "json", container_id])
        if not stats or not isinstance(stats, list) or len(stats) == 0:
            raise HTTPException(status_code=404, detail="No stats found for container")
        return stats[0]
    except HTTPException:
        raise

@app.get("/system/info")
def get_system_info():
    """Get system-wide information about Podman."""
    return run_podman_command(["info", "--format", "json"])

@app.get("/images")
def list_images():
    """List all images available in the system."""
    return run_podman_command(["images", "--format", "json"])

# Environment variable management
@app.get("/env")
def get_env_vars():
    """Get all environment variables from .env file."""
    env_vars = {}
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    
    if os.path.exists(env_file_path):
        with open(env_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value
    
    return env_vars

@app.put("/env")
def update_env_var(update: EnvVarUpdate):
    """Update an environment variable in the .env file."""
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    
    if not os.path.exists(env_file_path):
        raise HTTPException(status_code=404, detail=".env file not found")
    
    # Read current environment variables
    env_vars = {}
    with open(env_file_path, "r") as f:
        lines = f.readlines()
    
    # Update the variable
    updated = False
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith("#"):
            if "=" in line:
                key, _ = line.strip().split("=", 1)
                if key == update.key:
                    lines[i] = f"{update.key}={update.value}\n"
                    updated = True
    
    # Add the variable if it doesn't exist
    if not updated:
        lines.append(f"{update.key}={update.value}\n")
    
    # Write back to file
    with open(env_file_path, "w") as f:
        f.writelines(lines)
    
    return {"success": True, "key": update.key, "value": update.value}

# WebSocket for real-time monitoring
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.running = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        if not self.running:
            self.running = True
            asyncio.create_task(self.broadcast_stats())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if len(self.active_connections) == 0:
            self.running = False

    async def broadcast_stats(self):
        while self.running and len(self.active_connections) > 0:
            try:
                # Get stats for all containers
                stats = run_podman_command(["stats", "--no-stream", "--format", "json"])
                
                # Broadcast to all connected clients
                for connection in self.active_connections:
                    await connection.send_json({"type": "stats", "data": stats})
                
                # Wait before next update
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error broadcasting stats: {e}")
                await asyncio.sleep(5)  # Wait longer on error

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for possible client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            # Process other client commands as needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve static files for frontend
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Create static directory if it doesn't exist (for development)
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    with open(os.path.join(static_dir, "index.html"), "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Research System Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                h1 { color: #333; }
                .container { margin-top: 20px; }
                .container-card { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
                .running { border-left: 5px solid green; }
                .exited { border-left: 5px solid red; }
                .created { border-left: 5px solid blue; }
                button { padding: 5px 10px; margin-right: 5px; }
            </style>
        </head>
        <body>
            <h1>Research System Dashboard</h1>
            
            <div id="containers" class="container">
                <h2>Containers</h2>
                <div id="container-list"></div>
            </div>
            
            <div id="logs" class="container">
                <h2>Container Logs</h2>
                <select id="container-select">
                    <option value="">Select a container</option>
                </select>
                <pre id="log-output" style="background: #f5f5f5; padding: 10px; margin-top: 10px; height: 300px; overflow: auto;"></pre>
            </div>
            
            <script>
                // Fetch containers and update the UI
                async function fetchContainers() {
                    const response = await fetch('/containers');
                    const containers = await response.json();
                    
                    const containerList = document.getElementById('container-list');
                    containerList.innerHTML = '';
                    
                    const containerSelect = document.getElementById('container-select');
                    // Keep the first option and remove the rest
                    while (containerSelect.options.length > 1) {
                        containerSelect.remove(1);
                    }
                    
                    containers.forEach(container => {
                        // Add to container list
                        const containerCard = document.createElement('div');
                        containerCard.className = `container-card ${container.status}`;
                        containerCard.innerHTML = `
                            <h3>${container.names[0]}</h3>
                            <p>Status: ${container.status}</p>
                            <p>Image: ${container.image}</p>
                            <div class="controls">
                                <button onclick="containerAction('${container.id}', 'start')">Start</button>
                                <button onclick="containerAction('${container.id}', 'stop')">Stop</button>
                                <button onclick="containerAction('${container.id}', 'restart')">Restart</button>
                            </div>
                        `;
                        containerList.appendChild(containerCard);
                        
                        // Add to container select
                        const option = document.createElement('option');
                        option.value = container.id;
                        option.text = container.names[0];
                        containerSelect.appendChild(option);
                    });
                }
                
                // Perform an action on a container
                async function containerAction(id, action) {
                    try {
                        const response = await fetch(`/containers/${id}/action`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ action })
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            alert(`${action} successful!`);
                        } else {
                            alert(`Error: ${result.error}`);
                        }
                        
                        // Refresh the container list
                        fetchContainers();
                    } catch (error) {
                        alert(`Error: ${error.message}`);
                    }
                }
                
                // Fetch logs for a container
                async function fetchLogs(containerId) {
                    if (!containerId) return;
                    
                    try {
                        const response = await fetch(`/containers/${containerId}/logs`);
                        const data = await response.json();
                        
                        document.getElementById('log-output').textContent = data.logs;
                    } catch (error) {
                        document.getElementById('log-output').textContent = `Error: ${error.message}`;
                    }
                }
                
                // Set up event listeners
                document.getElementById('container-select').addEventListener('change', (e) => {
                    fetchLogs(e.target.value);
                });
                
                // Initial data fetch
                fetchContainers();
                
                // Set up periodic refresh
                setInterval(fetchContainers, 10000);
            </script>
        </body>
        </html>
        """)

# Mount static files directory
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)