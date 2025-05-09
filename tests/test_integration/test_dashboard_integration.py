"""
Integration tests for the System Dashboard.

This module tests the interaction between the Research System and the Dashboard.
"""

import os
import time
import subprocess
import requests
import json
import pytest
from pathlib import Path

# Path to the dashboard directory
DASHBOARD_DIR = Path(__file__).parents[2] / "examples" / "dashboard_prototype"
PROJECT_ROOT = Path(__file__).parents[2]

# Dashboard URL when running
DASHBOARD_URL = "http://localhost:8090"

@pytest.fixture(scope="module")
def research_system():
    """Start the research system for testing."""
    # Change to project root
    original_dir = os.getcwd()
    os.chdir(PROJECT_ROOT)
    
    # Check if the system is already running
    result = subprocess.run(["./app_manager.sh", "status"], 
                           capture_output=True, text=True)
    
    if "Server is running" not in result.stdout:
        # Start the research system
        subprocess.run(["./app_manager.sh", "start"], check=True)
        # Wait for the system to start
        time.sleep(5)
    
    yield
    
    # Change back to original directory
    os.chdir(original_dir)

@pytest.fixture(scope="module")
def dashboard_container():
    """Start the dashboard container for testing."""
    os.chdir(DASHBOARD_DIR)
    
    # Build the image if it doesn't exist
    result = subprocess.run(["podman", "image", "exists", "system-dashboard"],
                           capture_output=True)
    if result.returncode != 0:
        subprocess.run(["podman", "build", "-t", "system-dashboard", "."], 
                      check=True)
    
    # Check if the container is already running
    result = subprocess.run(["podman", "ps", "--filter", "name=system-dashboard"],
                           capture_output=True, text=True)
    
    if "system-dashboard" not in result.stdout:
        # Start the dashboard container
        subprocess.run([
            "podman", "run", "-d", "--name", "system-dashboard",
            "-v", "/run/podman/podman.sock:/run/podman/podman.sock",
            "-v", f"{PROJECT_ROOT}/.env:/app/.env:ro",
            "-p", "8090:8080",
            "system-dashboard"
        ], check=True)
        
        # Wait for the container to start
        time.sleep(5)
    
    # Verify the dashboard is running
    attempts = 0
    while attempts < 5:
        try:
            response = requests.get(f"{DASHBOARD_URL}")
            if response.status_code == 200:
                break
        except requests.RequestException:
            pass
        
        attempts += 1
        time.sleep(2)
    
    yield
    
    # Don't stop the dashboard so it can be used for further manual testing

def test_dashboard_api_endpoints(research_system, dashboard_container):
    """Test the dashboard API endpoints."""
    
    # Test containers endpoint
    response = requests.get(f"{DASHBOARD_URL}/containers")
    assert response.status_code == 200
    containers = response.json()
    assert isinstance(containers, list)
    
    # Find research system container
    research_container = None
    for container in containers:
        # Container name might be in container.names or container.Names
        names = container.get('names', container.get('Names', []))
        if not isinstance(names, list):
            continue
            
        for name in names:
            if 'research' in name.lower():
                research_container = container
                break
    
    # Verify we found the research system container
    assert research_container is not None, "Research system container not found"
    
    # Test container info endpoint
    response = requests.get(f"{DASHBOARD_URL}/containers/{research_container['id']}")
    assert response.status_code == 200
    container_info = response.json()
    assert container_info['Id'] == research_container['id']
    
    # Test logs endpoint
    response = requests.get(f"{DASHBOARD_URL}/containers/{research_container['id']}/logs")
    assert response.status_code == 200
    logs_data = response.json()
    assert 'logs' in logs_data
    
    # Test system info endpoint
    response = requests.get(f"{DASHBOARD_URL}/system/info")
    assert response.status_code == 200
    system_info = response.json()
    assert isinstance(system_info, dict)
    
    # Test images endpoint
    response = requests.get(f"{DASHBOARD_URL}/images")
    assert response.status_code == 200
    images = response.json()
    assert isinstance(images, list)

def test_dashboard_with_research_operations(research_system, dashboard_container):
    """Test dashboard integration with research system operations."""
    
    # Create a task using the app_manager
    os.chdir(PROJECT_ROOT)
    task_process = subprocess.run(
        ["./app_manager.sh", "task", "create", 
         "--title", "Dashboard Integration Test",
         "--description", "Testing integration between dashboard and research system"],
        capture_output=True, text=True
    )
    
    # Extract task ID from output
    import re
    task_id_match = re.search(r'ID: ([a-f0-9-]+)', task_process.stdout)
    assert task_id_match, "Failed to create task"
    task_id = task_id_match.group(1)
    
    # Create a plan for the task
    plan_process = subprocess.run(
        ["./app_manager.sh", "plan", "create", "--task-id", task_id],
        capture_output=True, text=True
    )
    
    # Verify the plan was created
    assert "Plan created successfully" in plan_process.stdout
    
    # Run a search query
    search_process = subprocess.run(
        ["./app_manager.sh", "search", "--query", "Dashboard integration testing", "--max-results", "3"],
        capture_output=True, text=True
    )
    
    # Verify the search was executed
    assert "Search Results" in search_process.stdout
    
    # Check dashboard logs again after operations
    # Get container ID first
    response = requests.get(f"{DASHBOARD_URL}/containers")
    containers = response.json()
    
    research_container = None
    for container in containers:
        names = container.get('names', container.get('Names', []))
        if not isinstance(names, list):
            continue
            
        for name in names:
            if 'research' in name.lower():
                research_container = container
                break
    
    assert research_container is not None
    
    # Check logs through the dashboard
    response = requests.get(f"{DASHBOARD_URL}/containers/{research_container['id']}/logs")
    assert response.status_code == 200
    logs_data = response.json()
    
    # Verify we see evidence of our operations in the logs
    assert logs_data['logs']
    # We may not see the exact task ID in the logs snippet, 
    # but we should see some indication of activity
    assert "task" in logs_data['logs'].lower() or "plan" in logs_data['logs'].lower()

def test_dashboard_websocket(dashboard_container):
    """Test the dashboard WebSocket for real-time updates."""
    import websocket
    import threading
    import time
    
    # Event to signal we received data
    received_data = threading.Event()
    message_data = []
    
    def on_message(ws, message):
        message_data.append(json.loads(message))
        received_data.set()
    
    def on_error(ws, error):
        print(f"WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print("WebSocket connection closed")
    
    def on_open(ws):
        print("WebSocket connection opened")
    
    # Create WebSocket connection
    ws = websocket.WebSocketApp(
        f"ws://localhost:8090/ws",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Start WebSocket connection in a thread
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait up to 10 seconds to receive data
    received = received_data.wait(10)
    
    # Close the WebSocket
    ws.close()
    
    # Verify we received data
    assert received, "Did not receive any data from WebSocket"
    assert len(message_data) > 0, "No messages received from WebSocket"
    assert "type" in message_data[0], "Message missing 'type' field"
    assert message_data[0]["type"] == "stats", "Message is not a stats update"
    assert "data" in message_data[0], "Message missing 'data' field"
    assert isinstance(message_data[0]["data"], list), "Stats data is not a list"