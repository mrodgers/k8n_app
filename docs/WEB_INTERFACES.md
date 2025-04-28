# Research System Web Interfaces

This document provides an overview of the web interfaces implemented in the Research System. The system includes two main web interfaces:

1. **System Monitoring Dashboard** - For monitoring system resources, agent status, and database operations
2. **Research Portal** - For creating and managing research tasks and viewing results

## System Monitoring Dashboard

### Purpose

The dashboard provides a simple web-based UI for monitoring the status of agents, services, system resources, and overall health. It is designed primarily for debugging and development purposes, allowing administrators to quickly assess the system's operational status.

### Access

The dashboard is accessible at: `/dashboard/`

### Components

1. **System Status Section**
   - Real-time metrics for CPU, memory, and disk usage
   - Visual progress bars for resource utilization

2. **Database Status Card**
   - Connection status (connected/error)
   - Database type (PostgreSQL/TinyDB)
   - Location information
   - Task and result counts

3. **Agents Status Section**
   - List of all registered agents
   - Status indicators (active, error, unknown, unreachable)
   - Description of each agent
   - Available tools for each agent

4. **Recent Tasks Section**
   - Table of the 5 most recent research tasks
   - Task ID, title, status, and creation date

5. **Recent Results Section**
   - Table of the 5 most recent research results
   - Result ID, task ID, format, status, and creation date

### Features

- **Auto-refresh**: Toggle for automatic refreshing of dashboard data
- **Manual refresh**: Button to manually refresh all dashboard data
- **Status caching**: Prevents excessive database queries and system calls
- **Visual indicators**: Color-coded status badges and progress bars
- **Navigation**: Direct link to the Research Portal

### Technical Implementation

- Implemented as a FastAPI router at the `/dashboard` prefix
- Uses Jinja2 templates for HTML rendering
- Includes client-side JavaScript for dynamic content updates
- Uses Bootstrap for responsive design and mobile compatibility
- Maintains a status cache with a 5-second timeout to prevent excessive system calls

## Research Portal

### Purpose

The Research Portal provides a user-friendly interface for creating research tasks, generating research plans, running searches, and viewing research results. It serves as the main interaction point for researchers using the system.

### Access

The Research Portal is accessible at: `/research/`

### Components

1. **Task Creation Form**
   - Fields for research title, description, and tags
   - Submit button to create new research tasks

2. **Research Tasks List**
   - Cards showing all research tasks
   - Basic task information with status indicators
   - Buttons for viewing results and creating plans

3. **Task Detail View**
   - Detailed view of the selected task
   - Full task description
   - Tags and metadata
   - Creation date and status information
   - Action buttons for running searches and creating plans

4. **Results Section**
   - List of all results for the selected task
   - Result content previews
   - Format information and status indicators

### Features

- **Task Management**: Create, view, and manage research tasks
- **Research Plan Generation**: Generate structured research plans for tasks
- **Search Integration**: Run search queries directly from the interface
- **Result Viewing**: View and explore research results
- **Dynamic Updates**: Asynchronous updates without page reloads
- **Responsive Design**: Mobile-friendly layout

### Technical Implementation

- Implemented as a FastAPI router at the `/research` prefix
- Uses Jinja2 templates for HTML rendering
- Leverages client-side JavaScript for API communication
- Uses fetch API for asynchronous data loading
- Implements template-based rendering for dynamic content
- Built with Bootstrap for responsive layout and styling

## API Integration

Both web interfaces interact with the Research System backend through RESTful API endpoints:

1. **Dashboard API Endpoints**:
   - `/dashboard/api/status` - Get all status data as JSON
   - `/dashboard/api/agents` - Get agent status data
   - `/dashboard/api/system` - Get system status data
   - `/dashboard/api/database` - Get database status data
   - `/dashboard/api/tasks` - Get recent tasks
   - `/dashboard/api/results` - Get recent results

2. **Research API Endpoints**:
   - `/api/tasks` - List all research tasks or create a new task
   - `/api/tasks/{task_id}` - Get a task by ID
   - `/api/tasks/{task_id}/plan` - Create a research plan for a task
   - `/api/tasks/{task_id}/search` - Execute a search for a task
   - `/api/tasks/{task_id}/results` - Get all results for a task
   - `/api/results/{result_id}` - Get a specific result by ID

## Container Integration

Both web interfaces are properly integrated into the Docker container:

- Template files are copied to the `/app/templates` directory
- Static files are copied to the `/app/static` directory
- The FastAPI app correctly mounts the static files directory
- Non-root user permissions are set for security

## Future Improvements

Potential enhancements for the web interfaces include:

1. **User Authentication**: Add user login and permission controls
2. **Advanced Filtering**: Add filtering and sorting capabilities for tasks and results
3. **Visualization**: Add charts and graphs for research results analysis
4. **Real-time Updates**: Implement WebSockets for real-time updates
5. **Expanded Test Coverage**: Add dedicated UI tests for web components
6. **Result Editing**: Allow editing and annotation of research results
7. **Export Functionality**: Add options to export research data in various formats
8. **Dark Mode**: Add theme support including dark mode