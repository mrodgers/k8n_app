"""
Research System Dashboard MVP - Backend Prototype (Direct Podman Command Version)

This module implements a simple FastAPI backend for visualizing and managing
the Research System components using direct podman commands.
"""

import os
import subprocess
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
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
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Return plain text for non-JSON responses
                return {"text": result.stdout}
        return {}
    except subprocess.CalledProcessError as e:
        # Handle podman command errors
        raise HTTPException(
            status_code=500,
            detail=f"Podman command failed: {e.stderr}"
        )
    except Exception as e:
        # Handle JSON parsing errors
        raise HTTPException(
            status_code=500, 
            detail=f"Error: {str(e)}"
        )

# API Endpoints

@app.get("/")
async def read_root():
    """Root endpoint for status check."""
    return {"status": "ok", "message": "Dashboard API is running"}

@app.get("/containers")
def list_containers():
    """List all containers with their basic information."""
    try:
        # Direct command line approach
        result = subprocess.run(
            ["podman", "ps", "-a", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stdout.strip():
            try:
                containers = json.loads(result.stdout)
                return containers
            except json.JSONDecodeError:
                # Return error for debugging
                return {"error": "JSON parse error", "raw_output": result.stdout[:1000]}

        return []
    except subprocess.CalledProcessError as e:
        # Return error for debugging
        return {"error": "Command error", "stderr": e.stderr}
    except Exception as e:
        # Return any other error
        return {"error": "Exception", "message": str(e)}

@app.get("/debug/containers")
def debug_containers():
    """Get raw container data for debugging."""
    try:
        # Direct command line approach
        result = subprocess.run(
            ["podman", "ps", "-a"],
            capture_output=True,
            text=True,
            check=True
        )

        raw_json = subprocess.run(
            ["podman", "ps", "-a", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )

        return HTMLResponse(
            f"""
            <html>
            <head><title>Container Debug</title></head>
            <body>
                <h1>Raw Podman Output</h1>
                <pre>{result.stdout}</pre>

                <h1>JSON Format</h1>
                <pre>{raw_json.stdout}</pre>
            </body>
            </html>
            """
        )
    except Exception as e:
        return HTMLResponse(f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

@app.get("/containers/{container_id}")
def get_container_info(container_id: str):
    """Get detailed information about a specific container."""
    try:
        result = subprocess.run(
            ["podman", "inspect", container_id],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            container = json.loads(result.stdout)
            if not container or len(container) == 0:
                raise HTTPException(status_code=404, detail="Container not found")
            return container[0]
        
        raise HTTPException(status_code=404, detail="Container not found")
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Podman command failed: {e.stderr}"
        )

@app.post("/containers/{container_id}/action")
def container_action(container_id: str, action: ContainerAction):
    """Perform an action (start, stop, restart) on a container."""
    if action.action not in ["start", "stop", "restart"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {action.action}. Must be 'start', 'stop', or 'restart'"
        )
    
    try:
        subprocess.run(
            ["podman", action.action, container_id],
            capture_output=True,
            text=True,
            check=True
        )
        return {"success": True, "container_id": container_id, "action": action.action}
    except subprocess.CalledProcessError as e:
        return {"success": False, "container_id": container_id, "error": e.stderr}

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
        result = subprocess.run(
            ["podman", "stats", "--no-stream", "--format", "json", container_id],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            stats = json.loads(result.stdout)
            if not stats or not isinstance(stats, list) or len(stats) == 0:
                raise HTTPException(status_code=404, detail="No stats found for container")
            return stats[0]
        
        raise HTTPException(status_code=404, detail="No stats found for container")
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {e.stderr}"
        )

@app.get("/system/info")
def get_system_info():
    """Get system-wide information about Podman."""
    try:
        result = subprocess.run(
            ["podman", "info", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            return json.loads(result.stdout)
        
        return {}
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system info: {e.stderr}"
        )

@app.get("/images")
def list_images():
    """List all images available in the system."""
    try:
        result = subprocess.run(
            ["podman", "images", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            return json.loads(result.stdout)
        
        return []
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list images: {e.stderr}"
        )

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
    
    return {"success": True, "key": update.key}

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
                # Get container list
                result = subprocess.run(
                    ["podman", "ps", "-a", "--format", "json"],
                    capture_output=True,
                    text=True
                )
                
                containers = []
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        containers = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        containers = []
                
                # Broadcast to all connected clients
                for connection in self.active_connections:
                    await connection.send_json({
                        "type": "stats",
                        "data": containers
                    })
                
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

# Add route to serve index.html explicitly
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML page."""
    with open(os.path.join(static_dir, "index.html"), "r") as f:
        return f.read()

@app.get("/", response_class=RedirectResponse, status_code=303)
async def redirect_to_dashboard():
    """Redirect root to dashboard."""
    return "/dashboard"

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8099)