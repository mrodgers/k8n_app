# Research System API Documentation

This document provides comprehensive documentation for the Research System API endpoints. The API allows you to interact with the research system, create and manage research tasks, generate research plans, and perform searches.

> **Note:** For detailed information about health monitoring, see [HEALTH_ENDPOINTS.md](./HEALTH_ENDPOINTS.md).

## Base URL

All API endpoints are relative to the base URL of your deployment. For local development, this is typically:

```
http://localhost:8181
```

## API Versioning

The current API version is `1.0.0` as specified in the root endpoint response. Future versions may include API versioning in the path.

## Authentication

The API currently does not implement authentication. For production deployments, it is recommended to implement an appropriate authentication mechanism.

## Content Type

All requests and responses use JSON format. Include the following header in your requests:

```
Content-Type: application/json
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure of requests:

* `200 OK`: The request was successful
* `201 Created`: A new resource was successfully created
* `400 Bad Request`: The request was invalid or cannot be served
* `404 Not Found`: The resource does not exist
* `500 Internal Server Error`: An error occurred on the server
* `503 Service Unavailable`: A required service (database, LLM) is unavailable

Error responses include a JSON object with a `detail` field providing more information about the error.

## Service Health and Status

### Get System Information

```
GET /
```

Returns basic information about the API service including version, environment, and available components.

**Example Response:**
```json
{
  "message": "Research System API",
  "version": "1.0.0",
  "environment": "development",
  "llm": {
    "enabled": true,
    "model": "gemma3:1b"
  },
  "components": {
    "agents": ["ollama", "planner", "search"],
    "services": ["planner", "search", "coordinator", "ollama"]
  }
}
```

### Check System Health

```
GET /health
```

Unified health check endpoint used for monitoring and Kubernetes probes. This simple endpoint provides basic health information and uptime metrics.

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": 1745848433.424399,
  "service": "research-system",
  "version": "1.0.0",
  "uptime": 141.339483976
}
```

This endpoint is designed to be reliable and fast, making it suitable for both Kubernetes liveness and readiness probes.

## Research Tasks

Research tasks are the core entity in the Research System. They represent research questions or topics that need investigation.

### List All Tasks

```
GET /api/tasks
```

Returns a list of all research tasks.

**Example Response:**
```json
{
  "tasks": [
    {
      "id": "7e13e5aa-7b01-462e-bfcd-bd3f326452a4",
      "title": "Why the sky is blue",
      "description": "Please explain the latest research that might impact theory about why the sky is blue",
      "status": "pending",
      "created_at": 1745814333.034767,
      "updated_at": 1745814341.150649,
      "assigned_to": null,
      "tags": ["bluesky"],
      "metadata": {
        "has_plan": true,
        "plan_id": "609e6572-d7f9-402a-b96a-33871258033e"
      }
    },
    ...
  ]
}
```

### Create a New Task

```
POST /api/tasks
```

Creates a new research task.

**Request Body:**
```json
{
  "title": "Climate Change Research",
  "description": "Research on the effects of climate change on coastal cities",
  "tags": ["climate", "research", "coastal"],
  "assigned_to": null
}
```

**Example Response:**
```json
{
  "task": {
    "id": "0772908a-4463-47d0-a4ab-91f75affe71e",
    "title": "Climate Change Research",
    "description": "Research on the effects of climate change on coastal cities",
    "status": "pending",
    "created_at": 1745806008.469761,
    "updated_at": 1745806008.484454,
    "assigned_to": null,
    "tags": ["climate", "research", "coastal"],
    "metadata": {}
  }
}
```

### Get Task by ID

```
GET /api/tasks/{task_id}
```

Returns details of a specific task.

**Parameters:**
- `task_id`: The unique identifier of the task

**Example Response:**
```json
{
  "task": {
    "id": "0772908a-4463-47d0-a4ab-91f75affe71e",
    "title": "Climate Change Research",
    "description": "Research on the effects of climate change on coastal cities",
    "status": "pending",
    "created_at": 1745806008.469761,
    "updated_at": 1745814497.996314,
    "assigned_to": null,
    "tags": ["climate", "research", "coastal"],
    "metadata": {
      "has_plan": true,
      "plan_id": "b0986c42-abb2-4fe7-894d-4eaec9aa27d6"
    }
  }
}
```

### Create Research Plan for Task

```
POST /api/tasks/{task_id}/plan
```

Generates a structured research plan for a task.

**Parameters:**
- `task_id`: The unique identifier of the task

**Example Response:**
```json
{
  "plan": {
    "id": "b0986c42-abb2-4fe7-894d-4eaec9aa27d6",
    "task_id": "0772908a-4463-47d0-a4ab-91f75affe71e",
    "created_at": 1745814497.996314,
    "steps": [
      {
        "step": 1,
        "description": "Identify key coastal cities at risk from climate change",
        "expected_output": "List of 10-15 coastal cities with high vulnerability"
      },
      {
        "step": 2,
        "description": "Research sea level rise projections for next 50 years",
        "expected_output": "Summary of scientific consensus on sea level rise"
      },
      ...
    ]
  }
}
```

### Execute Search for Task

```
POST /api/tasks/{task_id}/search
```

Performs a search query associated with a specific task.

**Parameters:**
- `task_id`: The unique identifier of the task

**Request Body:**
```json
{
  "query": "sea level rise coastal cities",
  "max_results": 10
}
```

**Example Response:**
```json
{
  "results": [
    {
      "id": "result-uuid-1",
      "title": "Sea Level Rise and Coastal Cities",
      "url": "https://example.com/sea-level-rise",
      "snippet": "Recent studies show accelerating sea level rise affecting coastal urban areas...",
      "relevance_score": 0.92
    },
    ...
  ]
}
```

## Research Results

Research results are the outputs of research operations such as searches or analyses.

### Get Result by ID

```
GET /api/results/{result_id}
```

Retrieves a specific research result.

**Parameters:**
- `result_id`: The unique identifier of the result

**Example Response:**
```json
{
  "result": {
    "id": "result-uuid-1",
    "task_id": "0772908a-4463-47d0-a4ab-91f75affe71e",
    "content": "Recent studies show accelerating sea level rise affecting coastal urban areas...",
    "format": "text",
    "status": "final",
    "created_at": 1745814600.123456,
    "updated_at": 1745814600.123456,
    "created_by": "search",
    "tags": ["sea-level", "coastal"],
    "metadata": {
      "source_url": "https://example.com/sea-level-rise"
    }
  }
}
```

### Get Results for Task

```
GET /api/tasks/{task_id}/results
```

Lists all research results associated with a specific task.

**Parameters:**
- `task_id`: The unique identifier of the task

**Example Response:**
```json
{
  "results": [
    {
      "id": "result-uuid-1",
      "task_id": "0772908a-4463-47d0-a4ab-91f75affe71e",
      "content": "Recent studies show accelerating sea level rise affecting coastal urban areas...",
      "format": "text",
      "status": "final",
      "created_at": 1745814600.123456,
      "updated_at": 1745814600.123456,
      "created_by": "search",
      "tags": ["sea-level", "coastal"],
      "metadata": {
        "source_url": "https://example.com/sea-level-rise"
      }
    },
    ...
  ]
}
```

## LLM Services

The Research System integrates with Large Language Models (LLMs) through Ollama. These endpoints provide direct access to LLM functionality.

### Generate Text Completion

```
POST /api/llm/completion
```

Generates a text completion from a prompt.

**Request Body:**
```json
{
  "prompt": "Explain the greenhouse effect in simple terms",
  "model": "gemma3:1b",
  "system": "You are a climate science expert explaining concepts to a general audience.",
  "options": {
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

**Example Response:**
```json
{
  "result": {
    "model": "gemma3:1b",
    "created_at": "2025-04-27T21:30:45Z",
    "response": "The greenhouse effect is like a blanket around Earth. It works like this...",
    "done": true,
    "total_duration": 1500000000,
    "load_duration": 150000000,
    "prompt_eval_count": 25,
    "prompt_eval_duration": 120000000,
    "eval_count": 500,
    "eval_duration": 1230000000
  }
}
```

### Generate Chat Completion

```
POST /api/llm/chat
```

Generates a chat completion from a sequence of messages.

**Request Body:**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a climate science expert."
    },
    {
      "role": "user",
      "content": "What are the main greenhouse gases?"
    }
  ],
  "model": "gemma3:1b",
  "options": {
    "temperature": 0.7
  }
}
```

**Example Response:**
```json
{
  "result": {
    "model": "gemma3:1b",
    "created_at": "2025-04-27T21:31:00Z",
    "message": {
      "role": "assistant",
      "content": "The main greenhouse gases are:\n\n1. Carbon dioxide (CO2)\n2. Methane (CH4)\n3. Nitrous oxide (N2O)\n4. Water vapor (H2O)\n5. Fluorinated gases (like HFCs, PFCs, SF6)\n\nCarbon dioxide and methane are the most significant human-influenced greenhouse gases. CO2 stays in the atmosphere for hundreds of years and comes primarily from burning fossil fuels, while methane is more potent but stays in the atmosphere for less time."
    },
    "done": true,
    "total_duration": 2000000000,
    "prompt_eval_count": 45,
    "prompt_eval_duration": 200000000,
    "eval_count": 700,
    "eval_duration": 1800000000
  }
}
```

### List Available LLM Models

```
GET /api/llm/models
```

Lists all available LLM models that can be used with the system.

**Example Response:**
```json
{
  "models": [
    {
      "name": "gemma3:1b",
      "modified_at": "2025-03-15T10:11:12Z",
      "size": 1610000000
    },
    {
      "name": "llama3:8b",
      "modified_at": "2025-02-20T14:15:16Z",
      "size": 4270000000
    }
  ]
}
```

## Web Interfaces

The Research System provides web interfaces for monitoring and management.

### Dashboard Interface

```
GET /dashboard/
```

Access the system monitoring dashboard showing system status, agent information, and recent tasks.

### Research Portal Interface

```
GET /research/
```

Access the research portal for creating and managing research tasks through a web interface.

## Troubleshooting

If you encounter any issues with the API:

1. Check the service status endpoints (`/healthz` and `/readyz`) to ensure all components are healthy
2. Verify that required services (database, LLM) are running and accessible
3. Check the logs for detailed error messages
4. Ensure your requests include the correct content type and format

## Future API Enhancements

Planned enhancements for future API versions:

1. API versioning in the endpoint paths (e.g., `/api/v1/tasks`)
2. Authentication and authorization
3. Pagination for list endpoints
4. More granular filtering options
5. WebSocket support for real-time updates
6. Rate limiting and usage tracking