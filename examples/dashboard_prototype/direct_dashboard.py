#!/usr/bin/env python3
"""
Research System Dashboard - Fixed Direct Podman Command Version

This is a simplified version that properly parses Podman command output
for reliable container display.
"""

import os
import subprocess
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

# Container descriptions and dashboard links
CONTAINER_INFO = {
    # Core system containers
    "research-system": {
        "description": "Main Research System API server that manages research tasks, search queries, and results",
        "role": "Core Service",
        "dashboard_link": "/dashboard?container=research-system",
        "doc_link": "/docs/API_DOCUMENTATION.md"
    },
    "research-coordinator": {
        "description": "Orchestrates interactions between agents and services, ensuring workflow coordination",
        "role": "Core Service",
        "dashboard_link": None,
        "doc_link": "/docs/architecture.md"
    },
    "memory-db": {
        "description": "PostgreSQL database for persistent storage of research data, documents and agent memory",
        "role": "Database",
        "dashboard_link": "http://localhost:8080",
        "doc_link": "/docs/DATABASE.md"
    },

    # Agent containers
    "planner-agent": {
        "description": "LLM-based agent that creates structured research plans from user queries",
        "role": "Agent",
        "dashboard_link": None,
        "doc_link": "/docs/agent/planner.md"
    },
    "search-agent": {
        "description": "Performs intelligent web searches and extracts relevant information",
        "role": "Agent",
        "dashboard_link": None,
        "doc_link": "/docs/agent/search.md"
    },
    "verification-agent": {
        "description": "Verifies accuracy and relevance of research findings before inclusion",
        "role": "Agent",
        "dashboard_link": None,
        "doc_link": "/docs/agent/verification.md"
    },

    # LLM containers
    "ollama": {
        "description": "Ollama LLM server running local models for agents and system components",
        "role": "LLM Service",
        "dashboard_link": None,
        "doc_link": "/docs/ollama_api.md"
    },
    "memory-server": {
        "description": "Manages vector storage and retrieval of context for agent memory",
        "role": "Memory Service",
        "dashboard_link": None,
        "doc_link": "/docs/AGENT_MEMORY_ARCHITECTURE.md"
    },

    # Default for unknown containers
    "default": {
        "description": "Container with unknown role",
        "role": "Unknown",
        "dashboard_link": None,
        "doc_link": None
    }
}

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
class ContainerAction(BaseModel):
    action: str  # start, stop, restart

# Helper functions
def parse_podman_ps(output: str) -> List[Dict[str, Any]]:
    """
    Parse the output of podman ps command into a structured format.
    """
    lines = output.strip().split('\n')
    
    # Need at least header and one container
    if len(lines) < 2:
        return []
    
    # Extract header and convert to lowercase for consistent keys
    header = [h.lower() for h in lines[0].split()]
    
    containers = []
    for line in lines[1:]:
        parts = line.split(None, len(header) - 1)
        if len(parts) < len(header):
            continue  # Skip if can't parse line
            
        container = dict(zip(header, parts))
        
        # Add or adjust some fields for our frontend
        container['id'] = container.get('container id', container.get('id', ''))
        
        # Handle "names" being singular in command output
        name = container.get('names', container.get('name', 'unknown'))
        container['names'] = [name]
        
        # Status field
        status = container.get('status', 'unknown')
        container['status'] = status
        
        containers.append(container)
    
    return containers

# Helper function to get container info
def get_container_info(container_name: str) -> Dict[str, Any]:
    """
    Get description and role information for a container based on its name.
    Uses pattern matching to find the closest match in our predefined container info.
    """
    # Clean the container name (remove prefixes like 'k8s_' or suffixes like '-1234')
    clean_name = container_name

    # Remove leading slash if present
    if clean_name.startswith('/'):
        clean_name = clean_name[1:]

    # Try exact match first
    if clean_name in CONTAINER_INFO:
        return CONTAINER_INFO[clean_name]

    # Try pattern matching
    for known_name, info in CONTAINER_INFO.items():
        if known_name != 'default' and known_name in clean_name:
            return info

    # Return default info if no match found
    return CONTAINER_INFO['default']

# API Endpoints
@app.get("/")
async def read_root():
    """Root endpoint for status check."""
    return RedirectResponse(url="/dashboard")

@app.get("/containers")
def list_containers():
    """List all containers with their basic information."""
    try:
        # Try first with JSON format
        try:
            result = subprocess.run(
                ["podman", "ps", "-a", "--format", "json"],
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                containers = json.loads(result.stdout)
                # Add description and role info to each container
                for container in containers:
                    # Get container name
                    container_name = ""
                    if container.get("Names") and isinstance(container["Names"], list) and container["Names"]:
                        container_name = container["Names"][0]
                    elif container.get("names") and isinstance(container["names"], list) and container["names"]:
                        container_name = container["names"][0]
                    elif container.get("Name"):
                        container_name = container["Name"]
                    elif container.get("name"):
                        container_name = container["name"]

                    # Add system info
                    info = get_container_info(container_name)
                    container["description"] = info["description"]
                    container["role"] = info["role"]
                    container["dashboard_link"] = info["dashboard_link"]
                    container["doc_link"] = info["doc_link"]

                return containers
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            # Fall back to regular format if JSON fails
            result = subprocess.run(
                ["podman", "ps", "-a"],
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                containers = parse_podman_ps(result.stdout)
                # Add description and role info to each container
                for container in containers:
                    # Get container name from various possible fields
                    container_name = container.get("names", container.get("name", ""))

                    # Add system info
                    info = get_container_info(container_name)
                    container["description"] = info["description"]
                    container["role"] = info["role"]
                    container["dashboard_link"] = info["dashboard_link"]
                    container["doc_link"] = info["doc_link"]

                return containers

        return []
    except Exception as e:
        # Return error for debugging
        return {"error": str(e)}

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
            check=False  # Don't fail if JSON format isn't supported
        )
        
        parsed = []
        if result.stdout.strip():
            parsed = parse_podman_ps(result.stdout)

        return HTMLResponse(
            f"""
            <html>
            <head>
                <title>Container Debug</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; overflow: auto; }}
                </style>
            </head>
            <body>
                <h1>Raw Podman Output</h1>
                <pre>{result.stdout}</pre>

                <h1>JSON Format</h1>
                <pre>{raw_json.stdout or "JSON format not available"}</pre>
                
                <h1>Parsed Containers</h1>
                <pre>{json.dumps(parsed, indent=2)}</pre>
            </body>
            </html>
            """
        )
    except Exception as e:
        return HTMLResponse(f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# Serve static files for frontend
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Create static directory if it doesn't exist (for development)
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Add route to serve dashboard HTML page
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML page."""
    dashboard_html = """<!DOCTYPE html>
<html>
<head>
    <title>Research System Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            color: #333;
            background-color: #f5f7fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 15px 0;
            margin-bottom: 20px;
        }
        
        .header h1 {
            margin: 0;
            padding: 0 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            overflow: hidden;
        }

        .card-header {
            background-color: #f8f9fa;
            padding: 12px 15px;
            font-weight: bold;
            border-bottom: 1px solid #e9ecef;
        }

        .card-body {
            padding: 15px;
        }

        .container-card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            padding: 15px;
            border-left: 4px solid #ddd;
        }
        
        .running {
            border-left-color: #2ecc71;
        }
        
        .exited, .stopped {
            border-left-color: #e74c3c;
        }
        
        .created {
            border-left-color: #3498db;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
            background-color: #95a5a6;
            color: white;
        }
        
        .running .status-badge {
            background-color: #2ecc71;
        }
        
        .exited .status-badge, .stopped .status-badge {
            background-color: #e74c3c;
        }
        
        .created .status-badge {
            background-color: #3498db;
        }
        
        .btn {
            padding: 8px 12px;
            margin-right: 5px;
            margin-top: 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        
        .btn-success {
            background-color: #2ecc71;
            color: white;
        }
        
        .btn-success:hover {
            background-color: #27ae60;
        }
        
        .btn-success:disabled {
            background-color: #95a5a6;
            cursor: not-allowed;
        }
        
        .btn-danger {
            background-color: #e74c3c;
            color: white;
        }
        
        .btn-danger:hover {
            background-color: #c0392b;
        }
        
        .btn-danger:disabled {
            background-color: #95a5a6;
            cursor: not-allowed;
        }
        
        .btn-primary {
            background-color: #3498db;
            color: white;
        }
        
        .btn-primary:hover {
            background-color: #2980b9;
        }
        
        .btn-secondary {
            background-color: #95a5a6;
            color: white;
        }
        
        .btn-secondary:hover {
            background-color: #7f8c8d;
        }
        
        .refresh-button {
            padding: 8px 15px;
            margin-bottom: 20px;
            border: none;
            border-radius: 4px;
            background-color: #3498db;
            color: white;
            cursor: pointer;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .refresh-button:hover {
            background-color: #2980b9;
        }
        
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        
        .logs-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }
        
        .logs-content {
            position: relative;
            margin: 50px auto;
            width: 80%;
            max-width: 1000px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            max-height: 80vh;
            overflow: hidden;
        }
        
        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            border-bottom: 1px solid #ddd;
        }
        
        .logs-body {
            padding: 0;
            overflow: auto;
            flex-grow: 1;
        }
        
        .logs-output {
            font-family: monospace;
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            margin: 0;
            white-space: pre-wrap;
            min-height: 200px;
        }
        
        .close-button {
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
        }
        
        #status-message {
            padding: 10px 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            display: none;
        }
        
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .role-badge {
            display: inline-block;
            padding: 3px 8px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
            background-color: #f1f1f1;
            color: #333;
            border-radius: 12px;
        }

        .container-description {
            margin: 10px 0;
            font-style: italic;
            color: #555;
        }

        .container-links {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }

        .link-button {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            font-size: 12px;
            text-decoration: none;
            color: #3498db;
            border: 1px solid #3498db;
            border-radius: 4px;
            transition: all 0.2s ease;
        }

        .link-button:hover {
            background-color: #3498db;
            color: white;
        }

        /* Role-based colors */
        .role-core {
            border-top: 4px solid #8e44ad;
        }

        .role-agent {
            border-top: 4px solid #27ae60;
        }

        .role-database {
            border-top: 4px solid #f39c12;
        }

        .role-llm {
            border-top: 4px solid #3498db;
        }

        .role-memory {
            border-top: 4px solid #1abc9c;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>Research System Container Dashboard</h1>
        </div>
    </div>
    
    <div class="container">
        <div id="status-message"></div>

        <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">Research System Overview</div>
            <div class="card-body">
                <p>The Research System is a Kubernetes-based microservices application that enables automated research workflows through specialized agents for planning, searching, and analysis. The system consists of the following components:</p>

                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
                    <div class="role-badge" style="background-color: #8e44ad; color: white;">Core Services</div>
                    <div class="role-badge" style="background-color: #27ae60; color: white;">Agents</div>
                    <div class="role-badge" style="background-color: #f39c12; color: white;">Database</div>
                    <div class="role-badge" style="background-color: #3498db; color: white;">LLM Services</div>
                    <div class="role-badge" style="background-color: #1abc9c; color: white;">Memory Services</div>
                </div>

                <p style="margin-top: 15px;">Each container below shows its role, description, and links to specific dashboards or documentation when available.</p>
            </div>
        </div>

        <div class="section-header">
            <h2>Containers</h2>
            <button class="refresh-button" onclick="fetchContainers()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M23 4V10H17"></path>
                    <path d="M1 20V14H7"></path>
                    <path d="M3.51 9.00008C4.01717 7.56686 4.87913 6.28548 6.01547 5.27549C7.1518 4.2655 8.52547 3.55978 10.0083 3.22427C11.4911 2.88876 13.0348 2.93436 14.4952 3.35679C15.9556 3.77922 17.2853 4.56473 18.36 5.64008L23 10.0001M1 14.0001L5.64 18.3601C6.71475 19.4354 8.04437 20.2209 9.50481 20.6434C10.9652 21.0658 12.5089 21.1114 13.9917 20.7759C15.4745 20.4404 16.8482 19.7347 17.9845 18.7247C19.1209 17.7147 19.9828 16.4333 20.49 15.0001"></path>
                </svg>
                Refresh
            </button>
        </div>
        
        <div class="grid" id="container-list">
            <div class="container-card">
                <h3>Loading containers...</h3>
                <p>Please wait while we fetch container information.</p>
            </div>
        </div>
    </div>
    
    <div id="logs-modal" class="logs-modal">
        <div class="logs-content">
            <div class="logs-header">
                <h3 id="logs-title">Container Logs</h3>
                <button class="close-button" onclick="closeLogsModal()">&times;</button>
            </div>
            <div class="logs-body">
                <pre id="logs-output" class="logs-output">Loading logs...</pre>
            </div>
        </div>
    </div>
    
    <script>
        // Fetch containers and update the UI
        async function fetchContainers() {
            try {
                showStatusMessage('Fetching containers...', 'info');
                
                const response = await fetch('/containers');
                const containers = await response.json();
                
                if (containers.error) {
                    showStatusMessage(`Error: ${containers.error}`, 'error');
                    return;
                }
                
                const containerList = document.getElementById('container-list');
                containerList.innerHTML = '';
                
                if (!containers || containers.length === 0) {
                    containerList.innerHTML = `
                        <div class="container-card">
                            <h3>No Containers Found</h3>
                            <p>No containers were found running in the system.</p>
                        </div>
                    `;
                    return;
                }
                
                containers.forEach(container => {
                    // Get container ID (handle different casing)
                    const containerId = container.id || container.Id || '';
                    
                    // Get container name (handle different property names and formats)
                    let containerName = 'Unknown';
                    if (container.names && Array.isArray(container.names) && container.names.length > 0) {
                        containerName = container.names[0];
                    } else if (container.Names && Array.isArray(container.Names) && container.Names.length > 0) {
                        containerName = container.Names[0];
                    } else if (container.names && typeof container.names === 'string') {
                        containerName = container.names;
                    } else if (container.Names && typeof container.Names === 'string') {
                        containerName = container.Names;
                    } else if (container.name) {
                        containerName = container.name;
                    } else if (container.Name) {
                        containerName = container.Name;
                    }
                    
                    // Remove potential forward slash in container name
                    if (containerName.startsWith('/')) {
                        containerName = containerName.substring(1);
                    }
                    
                    // Get container status
                    const status = container.status || container.Status || 'unknown';
                    
                    // Determine if the container is running
                    const isRunning = status.toLowerCase().includes('running') || 
                                     status.toLowerCase().includes('up');
                    
                    // Get container image
                    const image = container.image || container.Image || 'Unknown';
                    
                    // Get container creation time/date
                    let created = container.created || container.Created || 'Unknown';
                    if (typeof created === 'number') {
                        created = new Date(created * 1000).toLocaleString();
                    }
                    
                    // Determine container card status class
                    let statusClass = 'unknown';
                    if (isRunning) {
                        statusClass = 'running';
                    } else if (status.toLowerCase().includes('exited') || status.toLowerCase().includes('stopped')) {
                        statusClass = 'exited';
                    } else if (status.toLowerCase().includes('created')) {
                        statusClass = 'created';
                    }
                    
                    // Get container role and description information
                    const role = container.role || 'Unknown';
                    const description = container.description || 'No description available';
                    const dashboardLink = container.dashboard_link || null;
                    const docLink = container.doc_link || null;

                    // Determine role class for styling
                    let roleClass = '';
                    if (role.includes('Core Service')) {
                        roleClass = 'role-core';
                    } else if (role.includes('Agent')) {
                        roleClass = 'role-agent';
                    } else if (role.includes('Database')) {
                        roleClass = 'role-database';
                    } else if (role.includes('LLM Service')) {
                        roleClass = 'role-llm';
                    } else if (role.includes('Memory Service')) {
                        roleClass = 'role-memory';
                    }

                    const containerCard = document.createElement('div');
                    containerCard.className = `container-card ${statusClass} ${roleClass}`;

                    // Build container card HTML
                    let cardHtml = `
                        <div class="status-badge">${status}</div>
                        <div class="role-badge">${role}</div>
                        <h3>${containerName}</h3>
                        <p class="container-description">${description}</p>
                        <p><strong>ID:</strong> ${containerId.substring(0, 12)}</p>
                        <p><strong>Image:</strong> ${image}</p>
                        <p><strong>Created:</strong> ${created}</p>
                        <div class="controls">
                            <button class="btn btn-success" onclick="containerAction('${containerId}', 'start')" ${isRunning ? 'disabled' : ''}>Start</button>
                            <button class="btn btn-danger" onclick="containerAction('${containerId}', 'stop')" ${!isRunning ? 'disabled' : ''}>Stop</button>
                            <button class="btn btn-primary" onclick="containerAction('${containerId}', 'restart')">Restart</button>
                            <button class="btn btn-secondary" onclick="showLogs('${containerId}', '${containerName}')">Logs</button>
                        </div>
                    `;

                    // Add additional links section if any links are available
                    if (dashboardLink || docLink) {
                        cardHtml += `<div class="container-links">`;

                        if (dashboardLink) {
                            cardHtml += `
                                <a href="${dashboardLink}" target="_blank" class="link-button">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="3" y1="9" x2="21" y2="9"></line>
                                        <line x1="9" y1="21" x2="9" y2="9"></line>
                                    </svg>
                                    Dashboard
                                </a>
                            `;
                        }

                        if (docLink) {
                            cardHtml += `
                                <a href="${docLink}" target="_blank" class="link-button">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                        <polyline points="14 2 14 8 20 8"></polyline>
                                        <line x1="16" y1="13" x2="8" y2="13"></line>
                                        <line x1="16" y1="17" x2="8" y2="17"></line>
                                        <polyline points="10 9 9 9 8 9"></polyline>
                                    </svg>
                                    Documentation
                                </a>
                            `;
                        }

                        cardHtml += `</div>`;
                    }

                    containerCard.innerHTML = cardHtml;
                    containerList.appendChild(containerCard);
                });
                
                hideStatusMessage();
            } catch (error) {
                console.error('Error fetching containers:', error);
                showStatusMessage(`Error fetching containers: ${error.message}`, 'error');
            }
        }
        
        // Perform an action on a container
        async function containerAction(id, action) {
            try {
                showStatusMessage(`Performing ${action} on container...`, 'info');
                
                const response = await fetch(`/containers/${id}/action`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action })
                });
                
                const result = await response.json();
                if (result.success) {
                    showStatusMessage(`Successfully ${action}ed container`, 'success');
                    // Refresh the container list
                    setTimeout(() => {
                        fetchContainers();
                    }, 1000); // Small delay to allow container status to update
                } else {
                    showStatusMessage(`Error: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error(`Error performing ${action}:`, error);
                showStatusMessage(`Error: ${error.message}`, 'error');
            }
        }
        
        // Show logs for a container
        async function showLogs(id, name) {
            try {
                document.getElementById('logs-title').textContent = `Logs for ${name}`;
                document.getElementById('logs-output').textContent = 'Loading logs...';
                document.getElementById('logs-modal').style.display = 'block';
                
                const response = await fetch(`/containers/${id}/logs`);
                const data = await response.json();
                
                document.getElementById('logs-output').textContent = data.logs || 'No logs available';
            } catch (error) {
                console.error('Error fetching logs:', error);
                document.getElementById('logs-output').textContent = `Error fetching logs: ${error.message}`;
            }
        }
        
        // Close the logs modal
        function closeLogsModal() {
            document.getElementById('logs-modal').style.display = 'none';
        }
        
        // Show status message
        function showStatusMessage(message, type) {
            const statusElement = document.getElementById('status-message');
            statusElement.textContent = message;
            statusElement.className = type === 'error' ? 'error' : (type === 'success' ? 'success' : '');
            statusElement.style.display = 'block';
        }
        
        // Hide status message
        function hideStatusMessage() {
            document.getElementById('status-message').style.display = 'none';
        }
        
        // Close logs modal when clicking outside of it
        window.onclick = function(event) {
            const modal = document.getElementById('logs-modal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };
        
        // Initial data loading
        document.addEventListener('DOMContentLoaded', fetchContainers);
    </script>
</body>
</html>
"""
    return dashboard_html

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8299)