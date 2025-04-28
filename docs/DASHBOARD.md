# Monitoring Dashboard Guide

This document describes the web-based monitoring dashboard included with the Research System.

## Overview

The monitoring dashboard provides real-time visibility into the Research System's components, agents, and resources. It's designed to help developers and operators quickly understand system status and troubleshoot issues during development and production.

## Features

- Real-time system metrics (CPU, memory, disk usage)
- Agent status monitoring and tool inventory
- Database connection status and statistics
- Research task and result listings
- Auto-refresh capability
- JSON API endpoints for programmatic access

## Accessing the Dashboard

When the Research System is running, the dashboard is available at:

```
http://localhost:8181/dashboard/
```

Note the trailing slash is required.

## Dashboard Sections

### System Status

This section displays real-time system resource usage:

- CPU Usage: Current CPU utilization percentage
- Memory Usage: RAM usage with both percentage and absolute values
- Disk Usage: Storage utilization with both percentage and absolute values

### Database

This section shows database connection information:

- Connection Status: Whether the database is connected
- Database Type: TinyDB (development) or PostgreSQL (production)
- Database Location: File path or connection string
- Task Count: Number of research tasks in the database
- Result Count: Number of research results in the database

### Agents Status

This section lists all registered agents in the system:

- Agent Name: Identifier for the agent
- Status: Current operational status (active, error, unknown)
- Description: Purpose of the agent
- Tools: List of tools provided by the agent

### Recent Tasks

This section displays recently created research tasks with:

- Task ID
- Title
- Status
- Creation Date

### Recent Results

This section shows recently generated research results with:

- Result ID
- Associated Task ID
- Format (text, JSON, etc.)
- Status
- Creation Date

## Auto-Refresh

The dashboard automatically refreshes every 10 seconds to provide up-to-date information. This feature can be disabled using the toggle switch on the dashboard.

## API Endpoints

The dashboard provides JSON API endpoints for programmatic access:

| Endpoint | Description |
|----------|-------------|
| `/dashboard/api/status` | Complete system status including all components |
| `/dashboard/api/agents` | Information about registered agents and their tools |
| `/dashboard/api/system` | System resource usage metrics |
| `/dashboard/api/database` | Database connection status and statistics |
| `/dashboard/api/tasks` | Recent research tasks |
| `/dashboard/api/results` | Recent research results |

### Sample API Response

```json
{
  "system": {
    "cpu_percent": 0.0,
    "memory_percent": 16.5,
    "memory_used": "458.8 MB",
    "memory_total": "3894.4 MB",
    "disk_percent": 27.6,
    "disk_used": "10.8 GB",
    "disk_total": "39.1 GB"
  },
  "agents": {
    "ollama": {
      "name": "ollama",
      "server_url": "http://localhost:8080",
      "description": "LLM agent for generating text and embeddings",
      "tools": ["generate_completion", "generate_chat_completion", "generate_embeddings", "extract_content", "assess_relevance", "generate_plan"],
      "status": "active"
    },
    "planner": {
      "name": "planner",
      "server_url": "http://localhost:8080",
      "description": "Research planning agent",
      "tools": ["create_research_task", "create_research_plan", "generate_plan_for_task"],
      "status": "active"
    },
    "search": {
      "name": "search",
      "server_url": "http://localhost:8080",
      "description": "Search agent",
      "tools": ["execute_search", "extract_content_from_url", "filter_results"],
      "status": "active"
    }
  },
  "database": {
    "status": "connected",
    "type": "TinyDB",
    "location": "./data/research.json",
    "tasks_count": 0,
    "recent_tasks": [],
    "results_count": 0,
    "recent_results": []
  },
  "last_update": 1745810696.687
}
```

## Implementation Details

The dashboard is implemented using:

- FastAPI for the backend API endpoints
- Jinja2 Templates for HTML rendering
- Bootstrap for responsive layout
- psutil for system metrics collection
- JavaScript for auto-refresh functionality

## Customization

The dashboard can be customized by:

1. Modifying the HTML template in `/templates/dashboard.html`
2. Updating the CSS styles in `/static/css/dashboard.css`
3. Adjusting cache timeouts and refresh intervals in the dashboard code

## Kubernetes Integration

When running in Kubernetes, the dashboard automatically adapts to the containerized environment:

- System metrics reflect the container resource usage rather than the host
- Database connection shows the Kubernetes service connection
- Agent statuses reflect the health of the respective Kubernetes pods

## Troubleshooting

If the dashboard is not accessible:

1. Ensure the server is running (`./app_manager.sh status`)
2. Verify the correct URL is being used, including the trailing slash
3. Check the server logs for errors (`./app_manager.sh logs`)
4. Confirm Jinja2 is properly installed in your environment