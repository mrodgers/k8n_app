# Research System Health Monitoring Guide

This document describes the health monitoring approaches and endpoints available in the Research System.

## Overview

The Research System provides a unified health endpoint for monitoring and health checks. 
This endpoint is designed to be reliable, fast, and suitable for both manual checks and automated monitoring.

## Health Endpoint

```
GET /health
```

This endpoint provides:
- Basic health status information
- Service identification
- Version information
- Uptime tracking
- Timestamp for monitoring

### Example Response

```json
{
  "status": "healthy",
  "timestamp": 1745848433.424399,
  "service": "research-system",
  "version": "1.0.0",
  "uptime": 141.339483976
}
```

## Usage in Kubernetes

For Kubernetes deployments, the `/health` endpoint is configured for both liveness and readiness probes:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8181
  initialDelaySeconds: 10
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8181
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
  successThreshold: 1
  failureThreshold: 3
```

## Service Information

For more detailed information about the service and its components, use the root endpoint:

```
GET /
```

This provides comprehensive details about:
- Service components and versions
- Environment information
- LLM configuration (if enabled)
- Registered agents and services

Example response:

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

## Monitoring Best Practices

1. **Regular Health Checks**: Poll the `/health` endpoint at regular intervals (every 15-30 seconds)
2. **Automated Alerts**: Set up alerts for any non-200 responses from the health endpoint
3. **Dashboard Monitoring**: Use the built-in dashboard at `/dashboard/` for visual monitoring
4. **Log Analysis**: Combine health checks with log analysis for comprehensive monitoring
5. **Service Dependency Checks**: For more detailed checks, query the root endpoint (`/`) to verify component availability

## Troubleshooting Health Issues

If the health endpoint returns errors or is not accessible:

1. Check if the server is running: `./app_manager.sh status`
2. Examine the logs for error messages: `./app_manager.sh logs`
3. Verify port availability: `lsof -i :8181`
4. Check network connectivity if running in a containerized environment
5. Restart the service: `./app_manager.sh stop && ./app_manager.sh start`