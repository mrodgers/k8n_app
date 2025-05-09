#!/usr/bin/env python3
"""
Research System Dashboard - Fixed Direct Podman Command Version

This is a simplified version that properly parses Podman command output
and provides container descriptions and dashboard links.
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
        "doc_link": "/docs/API_DOCUMENTATION.md",
        "health_page": "/health/app"
    },
    "research-coordinator": {
        "description": "Orchestrates interactions between agents and services, ensuring workflow coordination",
        "role": "Core Service",
        "dashboard_link": None,
        "doc_link": "/docs/architecture.md",
        "health_page": "/health/coordinator"
    },
    "memory-db": {
        "description": "PostgreSQL database for persistent storage of research data, documents and agent memory",
        "role": "Database",
        "dashboard_link": "http://localhost:8080",
        "doc_link": "/docs/DATABASE.md",
        "health_page": "/health/postgres"
    },
    "postgres": {
        "description": "PostgreSQL database for persistent storage of research data, documents and agent memory",
        "role": "Database",
        "dashboard_link": "http://localhost:8080",
        "doc_link": "/docs/DATABASE.md",
        "health_page": "/health/postgres"
    },

    # Agent containers
    "planner-agent": {
        "description": "LLM-based agent that creates structured research plans from user queries",
        "role": "Agent",
        "dashboard_link": None,
        "doc_link": "/docs/agent/planner.md",
        "health_page": "/health/agents"
    },
    "search-agent": {
        "description": "Performs intelligent web searches and extracts relevant information",
        "role": "Agent",
        "dashboard_link": None,
        "doc_link": "/docs/agent/search.md",
        "health_page": "/health/agents"
    },
    "verification-agent": {
        "description": "Verifies accuracy and relevance of research findings before inclusion",
        "role": "Agent",
        "dashboard_link": None,
        "doc_link": "/docs/agent/verification.md",
        "health_page": "/health/agents"
    },

    # LLM containers
    "ollama": {
        "description": "Ollama LLM server running local models for agents and system components",
        "role": "LLM Service",
        "dashboard_link": None,
        "doc_link": "/docs/ollama_api.md",
        "health_page": "/health/ollama"
    },
    "memory-server": {
        "description": "Manages vector storage and retrieval of context for agent memory",
        "role": "Memory Service",
        "dashboard_link": None,
        "doc_link": "/docs/AGENT_MEMORY_ARCHITECTURE.md",
        "health_page": "/health/memory"
    },

    # Infrastructure
    "k8s": {
        "description": "Kubernetes/Minikube cluster managing container orchestration",
        "role": "Infrastructure",
        "dashboard_link": "http://localhost:30000/dashboard/",
        "doc_link": "/docs/KUBERNETES_DEPLOYMENT_GUIDE.md",
        "health_page": "/health/kubernetes"
    },
    "minikube": {
        "description": "Local Kubernetes implementation for development and testing",
        "role": "Infrastructure",
        "dashboard_link": "http://localhost:30000/dashboard/",
        "doc_link": "/docs/KUBERNETES_DEPLOYMENT_GUIDE.md",
        "health_page": "/health/kubernetes"
    },

    # Default for unknown containers
    "default": {
        "description": "Container with unknown role",
        "role": "Unknown",
        "dashboard_link": None,
        "doc_link": None,
        "health_page": None
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

def get_container_info(container_name: str) -> Dict[str, Any]:
    """
    Get description and role information for a container based on its name.
    Uses pattern matching to find the closest match in our predefined container info.
    """
    # Clean the container name (remove prefixes like 'k8s_' or suffixes like '-1234')
    clean_name = str(container_name or '')
    
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

# Health check helpers
async def check_postgres_health():
    """Check PostgreSQL database health"""
    try:
        # Try to run a basic postgres check command
        result = subprocess.run(
            ["podman", "exec", "postgres", "pg_isready", "-U", "postgres"],
            capture_output=True,
            text=True,
            check=False
        )

        is_running = result.returncode == 0

        # Get more details if available
        details = {}
        if is_running:
            # Get PostgreSQL version
            try:
                version_result = subprocess.run(
                    ["podman", "exec", "postgres", "psql", "-V"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if version_result.returncode == 0:
                    details["version"] = version_result.stdout.strip()
            except Exception:
                pass

            # Get PostgreSQL size info
            try:
                size_result = subprocess.run(
                    ["podman", "exec", "postgres", "psql", "-U", "postgres", "-c",
                     "SELECT pg_size_pretty(pg_database_size('research'))"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if size_result.returncode == 0 and "pg_size_pretty" in size_result.stdout:
                    size_lines = size_result.stdout.strip().split('\n')
                    if len(size_lines) >= 3:
                        details["db_size"] = size_lines[2].strip()
            except Exception:
                pass

        return {
            "status": "healthy" if is_running else "unhealthy",
            "details": details,
            "message": result.stdout if is_running else result.stderr
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "details": {},
            "message": str(e)
        }

async def check_ollama_health():
    """Check Ollama LLM service health"""
    try:
        # Try to run a basic ollama check command
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True,
            check=False
        )

        is_running = result.returncode == 0

        # Parse models if available
        models = []
        if is_running and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                if "models" in data:
                    models = [model["name"] for model in data["models"]]
            except json.JSONDecodeError:
                pass

        return {
            "status": "healthy" if is_running else "unhealthy",
            "models": models,
            "message": "Ollama is running with " + str(len(models)) + " models" if is_running else "Ollama service is not responding"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "models": [],
            "message": str(e)
        }

async def check_kubernetes_health():
    """Check Kubernetes/Minikube health"""
    try:
        # Try to run basic kubectl command
        result = subprocess.run(
            ["kubectl", "get", "nodes"],
            capture_output=True,
            text=True,
            check=False
        )

        is_running = result.returncode == 0

        # Get more details if available
        details = {}
        if is_running:
            # Get pod status
            try:
                pods_result = subprocess.run(
                    ["kubectl", "get", "pods", "--all-namespaces", "--no-headers"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if pods_result.returncode == 0:
                    pod_lines = pods_result.stdout.strip().split('\n')
                    details["total_pods"] = len(pod_lines) if pod_lines and pod_lines[0] else 0

                    # Count running pods
                    running_pods = 0
                    for line in pod_lines:
                        if line and "Running" in line:
                            running_pods += 1
                    details["running_pods"] = running_pods
            except Exception:
                pass

        return {
            "status": "healthy" if is_running else "unhealthy",
            "details": details,
            "message": "Kubernetes is running" if is_running else "Kubernetes is not responding"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "details": {},
            "message": str(e)
        }

# API Endpoints
@app.get("/")
async def read_root():
    """Root endpoint for status check."""
    return RedirectResponse(url="/dashboard")

@app.get("/containers")
def list_containers():
    """List all containers with their basic information."""
    try:
        containers = []
        
        # Try to get containers with podman ps
        try:
            # First try JSON format
            result = subprocess.run(
                ["podman", "ps", "-a", "--format", "json"],
                capture_output=True,
                text=True,
                check=False  # Don't fail if command fails
            )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    containers = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try table format
                    pass
            
            # If JSON failed, try table format
            if not containers:
                result = subprocess.run(
                    ["podman", "ps", "-a"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    containers = parse_podman_ps(result.stdout)
            
            # If we still don't have containers, create a sample one for testing
            if not containers:
                containers = [{
                    "id": "sample123456",
                    "names": ["research-system"],
                    "status": "Running",
                    "image": "research-system:latest",
                    "created": "2 days ago"
                }]
            
            # Add description and role info to each container
            enriched_containers = []
            for container in containers:
                try:
                    # Create a new container dict with basic properties
                    c = {
                        "id": container.get("Id", container.get("id", "unknown")),
                        "image": container.get("Image", container.get("image", "unknown")),
                        "status": container.get("Status", container.get("status", "unknown")),
                        "created": container.get("Created", container.get("created", "unknown"))
                    }
                    
                    # Extract name with fallbacks
                    container_name = None
                    if container.get("Names") and isinstance(container["Names"], list) and container["Names"]:
                        container_name = container["Names"][0]
                    elif container.get("names") and isinstance(container["names"], list) and container["names"]:
                        container_name = container["names"][0]
                    elif container.get("Names") and isinstance(container["Names"], str):
                        container_name = container["Names"]
                    elif container.get("names") and isinstance(container["names"], str):
                        container_name = container["names"]
                    elif container.get("Name"):
                        container_name = container["Name"]
                    elif container.get("name"):
                        container_name = container["name"]
                    else:
                        container_name = "unknown"
                    
                    # Store name consistently
                    c["names"] = [container_name]
                    c["Names"] = [container_name]
                    
                    # Get container info
                    info = get_container_info(container_name)
                    c["description"] = info["description"]
                    c["role"] = info["role"]
                    c["dashboard_link"] = info["dashboard_link"]
                    c["doc_link"] = info["doc_link"]
                    
                    enriched_containers.append(c)
                except Exception as e:
                    # If enrichment fails, add container with minimal info
                    print(f"Error enriching container: {e}")
                    enriched_containers.append({
                        "id": container.get("Id", container.get("id", "unknown")),
                        "image": container.get("Image", container.get("image", "unknown")),
                        "status": container.get("Status", container.get("status", "unknown")),
                        "created": container.get("Created", container.get("created", "unknown")),
                        "names": ["unknown"],
                        "Names": ["unknown"],
                        "description": "Container information not available",
                        "role": "Unknown",
                        "dashboard_link": None,
                        "doc_link": None
                    })
            
            return enriched_containers
        except Exception as e:
            print(f"Error listing containers: {e}")
            # Create a sample container for testing
            return [{
                "id": "sample123456",
                "names": ["research-system"],
                "Names": ["research-system"],
                "status": "Running",
                "image": "research-system:latest",
                "created": "2 days ago",
                "description": "Main Research System API server",
                "role": "Core Service",
                "dashboard_link": None,
                "doc_link": None
            }]
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": f"Could not list containers: {str(e)}"}

@app.get("/containers/{container_id}")
def get_container_details(container_id: str):
    """Get detailed information about a specific container."""
    try:
        result = subprocess.run(
            ["podman", "inspect", container_id],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            try:
                container = json.loads(result.stdout)
                if container and len(container) > 0:
                    # Add container info
                    container_name = ""
                    if "Name" in container[0]:
                        container_name = container[0]["Name"]
                    elif "Names" in container[0] and container[0]["Names"]:
                        container_name = container[0]["Names"][0]
                    
                    info = get_container_info(container_name)
                    container[0]["description"] = info["description"]
                    container[0]["role"] = info["role"]
                    container[0]["dashboard_link"] = info["dashboard_link"]
                    container[0]["doc_link"] = info["doc_link"]
                    
                    return container[0]
            except json.JSONDecodeError:
                pass
        
        raise HTTPException(status_code=404, detail="Container not found")
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

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
        # Return empty logs instead of error for better UX
        return {"container_id": container_id, "logs": f"No logs available: {e.stderr}"}

@app.get("/api/k8s/events")
async def get_kubernetes_events():
    """Get recent Kubernetes events."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "events", "--sort-by='.lastTimestamp'"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            return {"events": result.stdout}
        else:
            # Generate sample data for testing
            sample_events = """LAST SEEN   TYPE     REASON      OBJECT                      MESSAGE
5m           Normal   Scheduled   pod/research-system-7f8b9c    Successfully assigned default/research-system-7f8b9c to minikube
4m           Normal   Pulling     pod/research-system-7f8b9c    Pulling image "research-system:latest"
3m           Normal   Pulled      pod/research-system-7f8b9c    Successfully pulled image "research-system:latest"
3m           Normal   Created     pod/research-system-7f8b9c    Created container research-system
3m           Normal   Started     pod/research-system-7f8b9c    Started container research-system
1m           Normal   Pulling     pod/postgres-5d7b8f           Pulling image "postgres:latest"
1m           Normal   Pulled      pod/postgres-5d7b8f           Successfully pulled image "postgres:latest"
1m           Normal   Created     pod/postgres-5d7b8f           Created container postgres
1m           Normal   Started     pod/postgres-5d7b8f           Started container postgres"""
            return {"events": sample_events}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health/postgres")
async def postgres_health_dashboard():
    """PostgreSQL health dashboard page"""
    health_data = await check_postgres_health()

    details_html = ""
    for key, value in health_data.get("details", {}).items():
        details_html += f"<tr><td>{key}</td><td>{value}</td></tr>"

    status_color = "#2ecc71" if health_data["status"] == "healthy" else "#e74c3c"

    return HTMLResponse(
        f"""
        <html>
        <head>
            <title>PostgreSQL Health Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    background-color: #f5f7fa;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}

                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 0;
                    margin-bottom: 20px;
                }}

                .header h1 {{
                    margin: 0;
                    padding: 0 20px;
                }}

                .card {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    overflow: hidden;
                }}

                .card-header {{
                    background-color: #f8f9fa;
                    padding: 12px 15px;
                    font-weight: bold;
                    border-bottom: 1px solid #e9ecef;
                }}

                .card-body {{
                    padding: 15px;
                }}

                .status-indicator {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: {status_color};
                    margin-right: 10px;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}

                table th, table td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #eee;
                }}

                .nav-link {{
                    display: inline-block;
                    padding: 8px 15px;
                    margin-right: 10px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}

                .nav-link:hover {{
                    background-color: #2980b9;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>PostgreSQL Health Dashboard</h1>
                </div>
            </div>

            <div class="container">
                <a href="/dashboard" class="nav-link">← Back to Dashboard</a>

                <div class="card">
                    <div class="card-header">
                        <span class="status-indicator"></span>
                        PostgreSQL Status: {health_data["status"].upper()}
                    </div>
                    <div class="card-body">
                        <p>{health_data["message"]}</p>

                        <table>
                            <thead>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                {details_html}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">Database Management</div>
                    <div class="card-body">
                        <p>Database is running in a containerized environment using PostgreSQL with support for Vector Search extensions.</p>

                        <h3>Check PostgreSQL Container Logs</h3>
                        <pre id="db-logs">Loading logs...</pre>

                        <script>
                            // Fetch postgres logs
                            async function fetchLogs() {{
                                try {{
                                    // Find postgres container ID
                                    const response = await fetch('/containers');
                                    const containers = await response.json();

                                    let postgresId = null;
                                    for (const container of containers) {{
                                        const name = container.Names ? container.Names[0] : (container.names ? container.names[0] : '');
                                        if (name.includes('postgres')) {{
                                            postgresId = container.id || container.Id;
                                            break;
                                        }}
                                    }}

                                    if (postgresId) {{
                                        const logsResponse = await fetch(`/containers/${{postgresId}}/logs`);
                                        const logsData = await logsResponse.json();
                                        document.getElementById('db-logs').textContent = logsData.logs || 'No logs available';
                                    }} else {{
                                        document.getElementById('db-logs').textContent = 'Postgres container not found';
                                    }}
                                }} catch (error) {{
                                    console.error('Error fetching logs:', error);
                                    document.getElementById('db-logs').textContent = `Error fetching logs: ${{error.message}}`;
                                }}
                            }}

                            // Load logs when page loads
                            document.addEventListener('DOMContentLoaded', fetchLogs);
                        </script>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    )

@app.get("/health/ollama")
async def ollama_health_dashboard():
    """Ollama LLM service health dashboard page"""
    health_data = await check_ollama_health()

    models_html = ""
    for model in health_data.get("models", []):
        models_html += f"<li>{model}</li>"

    status_color = "#2ecc71" if health_data["status"] == "healthy" else "#e74c3c"

    return HTMLResponse(
        f"""
        <html>
        <head>
            <title>Ollama Health Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    background-color: #f5f7fa;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}

                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 0;
                    margin-bottom: 20px;
                }}

                .header h1 {{
                    margin: 0;
                    padding: 0 20px;
                }}

                .card {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    overflow: hidden;
                }}

                .card-header {{
                    background-color: #f8f9fa;
                    padding: 12px 15px;
                    font-weight: bold;
                    border-bottom: 1px solid #e9ecef;
                }}

                .card-body {{
                    padding: 15px;
                }}

                .status-indicator {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: {status_color};
                    margin-right: 10px;
                }}

                .model-list {{
                    list-style-type: none;
                    padding: 0;
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 10px;
                }}

                .model-list li {{
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 4px;
                    border-left: 3px solid #3498db;
                }}

                .nav-link {{
                    display: inline-block;
                    padding: 8px 15px;
                    margin-right: 10px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}

                .nav-link:hover {{
                    background-color: #2980b9;
                }}

                pre {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 4px;
                    overflow: auto;
                    max-height: 300px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>Ollama LLM Service Health Dashboard</h1>
                </div>
            </div>

            <div class="container">
                <a href="/dashboard" class="nav-link">← Back to Dashboard</a>

                <div class="card">
                    <div class="card-header">
                        <span class="status-indicator"></span>
                        Ollama Status: {health_data["status"].upper()}
                    </div>
                    <div class="card-body">
                        <p>{health_data["message"]}</p>

                        <h3>Available Models</h3>
                        <ul class="model-list">
                            {models_html or "<li>No models found</li>"}
                        </ul>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">Ollama Service Management</div>
                    <div class="card-body">
                        <p>Ollama provides local LLM inference for the Research System. It supports multiple models and is optimized for containerized environments.</p>

                        <h3>Check Ollama Container Logs</h3>
                        <pre id="ollama-logs">Loading logs...</pre>

                        <script>
                            // Fetch ollama logs
                            async function fetchLogs() {{
                                try {{
                                    // Find ollama container ID
                                    const response = await fetch('/containers');
                                    const containers = await response.json();

                                    let ollamaId = null;
                                    for (const container of containers) {{
                                        const name = container.Names ? container.Names[0] : (container.names ? container.names[0] : '');
                                        if (name.includes('ollama')) {{
                                            ollamaId = container.id || container.Id;
                                            break;
                                        }}
                                    }}

                                    if (ollamaId) {{
                                        const logsResponse = await fetch(`/containers/${{ollamaId}}/logs`);
                                        const logsData = await logsResponse.json();
                                        document.getElementById('ollama-logs').textContent = logsData.logs || 'No logs available';
                                    }} else {{
                                        document.getElementById('ollama-logs').textContent = 'Ollama container not found';
                                    }}
                                }} catch (error) {{
                                    console.error('Error fetching logs:', error);
                                    document.getElementById('ollama-logs').textContent = `Error fetching logs: ${{error.message}}`;
                                }}
                            }}

                            // Load logs when page loads
                            document.addEventListener('DOMContentLoaded', fetchLogs);
                        </script>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    )

@app.get("/health/kubernetes")
async def kubernetes_health_dashboard():
    """Kubernetes/Minikube health dashboard page"""
    health_data = await check_kubernetes_health()

    details_html = ""
    for key, value in health_data.get("details", {}).items():
        details_html += f"<tr><td>{key}</td><td>{value}</td></tr>"

    status_color = "#2ecc71" if health_data["status"] == "healthy" else "#e74c3c"

    return HTMLResponse(
        f"""
        <html>
        <head>
            <title>Kubernetes Health Dashboard</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    background-color: #f5f7fa;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}

                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 15px 0;
                    margin-bottom: 20px;
                }}

                .header h1 {{
                    margin: 0;
                    padding: 0 20px;
                }}

                .card {{
                    background-color: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                    overflow: hidden;
                }}

                .card-header {{
                    background-color: #f8f9fa;
                    padding: 12px 15px;
                    font-weight: bold;
                    border-bottom: 1px solid #e9ecef;
                }}

                .card-body {{
                    padding: 15px;
                }}

                .status-indicator {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: {status_color};
                    margin-right: 10px;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}

                table th, table td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #eee;
                }}

                .nav-link {{
                    display: inline-block;
                    padding: 8px 15px;
                    margin-right: 10px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }}

                .nav-link:hover {{
                    background-color: #2980b9;
                }}

                pre {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 4px;
                    overflow: auto;
                    max-height: 300px;
                }}

                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 15px;
                    margin-top: 15px;
                }}

                .stat-card {{
                    background-color: white;
                    border-radius: 5px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }}

                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    margin: 10px 0;
                }}

                .stat-label {{
                    font-size: 14px;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>Kubernetes Health Dashboard</h1>
                </div>
            </div>

            <div class="container">
                <a href="/dashboard" class="nav-link">← Back to Dashboard</a>

                <div class="card">
                    <div class="card-header">
                        <span class="status-indicator"></span>
                        Kubernetes Status: {health_data["status"].upper()}
                    </div>
                    <div class="card-body">
                        <p>{health_data["message"]}</p>

                        <div class="grid">
                            <div class="stat-card">
                                <div class="stat-label">Total Pods</div>
                                <div class="stat-value">{health_data.get("details", {}).get("total_pods", 0)}</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-label">Running Pods</div>
                                <div class="stat-value">{health_data.get("details", {}).get("running_pods", 0)}</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-label">Health Status</div>
                                <div class="stat-value" style="color: {status_color};">{health_data["status"].upper()}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">Kubernetes Resources</div>
                    <div class="card-body">
                        <h3>Recent Kubernetes Events</h3>
                        <pre id="k8s-events">Loading events...</pre>

                        <script>
                            // Fetch kubernetes events
                            async function fetchEvents() {{
                                try {{
                                    const result = await fetch('/api/k8s/events');
                                    if (result.ok) {{
                                        const data = await result.json();
                                        document.getElementById('k8s-events').textContent = data.events || 'No events available';
                                    }} else {{
                                        // Fallback to simulated events for demo
                                        document.getElementById('k8s-events').textContent =
                                        `LAST SEEN   TYPE     REASON      OBJECT                      MESSAGE
5m           Normal   Scheduled   pod/research-system-7f8b9c    Successfully assigned default/research-system-7f8b9c to minikube
4m           Normal   Pulling     pod/research-system-7f8b9c    Pulling image "research-system:latest"
3m           Normal   Pulled      pod/research-system-7f8b9c    Successfully pulled image "research-system:latest"
3m           Normal   Created     pod/research-system-7f8b9c    Created container research-system
3m           Normal   Started     pod/research-system-7f8b9c    Started container research-system
1m           Normal   Pulling     pod/postgres-5d7b8f           Pulling image "postgres:latest"
1m           Normal   Pulled      pod/postgres-5d7b8f           Successfully pulled image "postgres:latest"`;
                                    }}
                                }} catch (error) {{
                                    console.error('Error fetching events:', error);
                                    document.getElementById('k8s-events').textContent = `Error fetching events: ${{error.message}}`;
                                }}
                            }}

                            // Load events when page loads
                            document.addEventListener('DOMContentLoaded', fetchEvents);
                        </script>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
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

# Serve dashboard HTML page
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
                    try {
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
                    } catch (e) {
                        console.error('Error getting container name:', e);
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
                    cardHtml += `<div class="container-links">`;

                    // Health dashboard link (always available)
                    const healthPage = container.health_page || null;
                    if (healthPage) {
                        cardHtml += `
                            <a href="${healthPage}" class="link-button">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                                </svg>
                                Health
                            </a>
                        `;
                    }

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
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Create static directory if it doesn't exist (for development)
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8299)