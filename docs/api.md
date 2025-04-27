# API Documentation

This document describes the RESTful API endpoints provided by the k8s-python-app.

## API Overview

The k8s-python-app provides a simple RESTful API for demonstration purposes. The application is built with Flask and returns JSON responses.

## Base URL

When running locally:
```
http://localhost:8080
```

When deployed to Kubernetes, the base URL will depend on your cluster configuration and ingress setup.

## Authentication

The current version does not implement authentication. All endpoints are publicly accessible.

## Endpoints

### Health Check

```
GET /health
```

Returns the health status of the application. Used by Kubernetes for liveness and readiness probes.

#### Response

```json
{
  "status": "healthy"
}
```

#### Status Codes

- `200 OK` - The application is healthy
- `503 Service Unavailable` - The application is unhealthy

### Welcome Message

```
GET /
```

Returns a welcome message from the application.

#### Response

```json
{
  "message": "Welcome to the k8s-python-app!"
}
```

#### Status Codes

- `200 OK` - Request successful

## Error Handling

The API returns standard HTTP status codes to indicate success or failure:

- `200 OK` - The request was successful
- `400 Bad Request` - The request was invalid
- `404 Not Found` - The requested resource was not found
- `500 Internal Server Error` - An error occurred on the server

Error responses include a JSON body with additional information:

```json
{
  "error": "Error message",
  "status_code": 400
}
```

## API Versioning

The current API does not implement versioning. Future versions will use URL prefixes for versioning (e.g., `/v1/health`).

## Rate Limiting

The current version does not implement rate limiting.

## Future Endpoints

The following endpoints are planned for future releases:

### Configuration Information

```
GET /config
```

Will return the current configuration of the application (non-sensitive values only).

### Metrics

```
GET /metrics
```

Will return Prometheus-compatible metrics for monitoring.

## Using the API with cURL

Examples of using the API with cURL:

### Check Health

```bash
curl -X GET http://localhost:8080/health
```

### Get Welcome Message

```bash
curl -X GET http://localhost:8080/
```

## Using the API with Python

Example of using the API with Python's requests library:

```python
import requests

# Check health
response = requests.get('http://localhost:8080/health')
print(response.json())

# Get welcome message
response = requests.get('http://localhost:8080/')
print(response.json())
```