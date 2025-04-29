# Environment Variables Guide

This document describes all environment variables used by the Research System, their purposes, and how they interact with the configuration system.

## Configuration Precedence

The Research System loads configuration in the following order of precedence:

1. **Environment Variables** (highest priority)
2. **Configuration File** (config.yaml)
3. **Default Values** (built-in defaults)

This means environment variables will always override settings in the config file or defaults.

## Environment Variable Naming

The Research System supports two naming conventions for environment variables:

1. **Recommended Naming** - Uses the `RESEARCH_` prefix (e.g., `RESEARCH_APP_PORT`)
2. **Legacy Naming** - Uses traditional names without the prefix (e.g., `PORT`)

The recommended naming convention is preferred for new deployments to avoid conflicts with other applications.

## Common Environment Variables

### Application Settings

| Environment Variable | Legacy Variable | Description | Default |
|---------------------|-----------------|-------------|---------|
| `RESEARCH_APP_PORT` | `PORT` | The port on which the application listens | `8181` |
| `RESEARCH_APP_MAX_WORKERS` | `MAX_WORKERS` | Number of worker processes | `4` |
| `RESEARCH_ENV_MODE` | `ENV_MODE` | Application environment mode | `development` |
| `CONFIG_PATH` | - | Path to the configuration file | `config.yaml` |

### Logging

| Environment Variable | Legacy Variable | Description | Default |
|---------------------|-----------------|-------------|---------|
| `RESEARCH_LOG_LEVEL` | `LOG_LEVEL` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | `INFO` |

### Database Settings

| Environment Variable | Legacy Variable | Description | Default |
|---------------------|-----------------|-------------|---------|
| `RESEARCH_DB_TYPE` | - | Database type (tinydb, postgres) | `tinydb` |
| `RESEARCH_DB_PATH` | `DB_TINYDB_PATH` | Path to TinyDB database file | `data/research.json` |
| `RESEARCH_DB_USE_POSTGRES` | `USE_POSTGRES`, `DB_USE_POSTGRES` | Whether to use PostgreSQL | `false` |
| `RESEARCH_DB_URL` | `DATABASE_URL` | PostgreSQL connection URL | - |

#### PostgreSQL-specific Settings

| Environment Variable | Legacy Variable | Description | Default |
|---------------------|-----------------|-------------|---------|
| `RESEARCH_DB_HOST` | `DB_POSTGRES_HOST`, `POSTGRES_SERVICE_HOST` | PostgreSQL host | `localhost` |
| `RESEARCH_DB_PORT` | `DB_POSTGRES_PORT`, `POSTGRES_SERVICE_PORT` | PostgreSQL port | `5432` |
| `RESEARCH_DB_NAME` | `DB_POSTGRES_DBNAME`, `POSTGRES_DB` | PostgreSQL database name | `research` |
| `RESEARCH_DB_USER` | `DB_POSTGRES_USER`, `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `RESEARCH_DB_PASSWORD` | `DB_POSTGRES_PASSWORD`, `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |

### LLM Settings

| Environment Variable | Legacy Variable | Description | Default |
|---------------------|-----------------|-------------|---------|
| `RESEARCH_LLM_ENABLED` | - | Whether to enable LLM integration | `true` |
| `RESEARCH_LLM_MODEL` | `OLLAMA_MODEL` | Ollama model to use | `gemma3:1b` |
| `RESEARCH_LLM_URL` | `OLLAMA_URL` | Ollama API URL | Auto-detected* |
| `RESEARCH_LLM_TIMEOUT` | - | Timeout for LLM requests (seconds) | `120` |

*Auto-detection: In Kubernetes, uses `http://ollama-service:11434`, otherwise defaults to `http://localhost:11434`

### Brave Search API Settings

| Environment Variable | Legacy Variable | Description | Default |
|---------------------|-----------------|-------------|---------|
| `RESEARCH_BRAVE_API_KEY` | `BRAVE_SEARCH_API_KEY` | Brave Search API key | - |

## Local Development with .env Files

For local development, you can use a `.env` file to set environment variables. The application will automatically load variables from a `.env` file if it exists in the project root. An example is provided in `.env.example`.

To use:

1. Copy `.env.example` to `.env`
2. Modify variables as needed
3. Run the application

```bash
cp .env.example .env
# Edit .env with your preferred editor
# Start the application
python src/app.py
```

## Kubernetes Configuration

In Kubernetes, you should set environment variables using ConfigMaps and Secrets:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: research-system-config
data:
  RESEARCH_ENV_MODE: "production"
  RESEARCH_APP_PORT: "8181"
  RESEARCH_LOG_LEVEL: "INFO"
  RESEARCH_DB_USE_POSTGRES: "true"
  RESEARCH_DB_HOST: "postgres-service"
  RESEARCH_DB_PORT: "5432"
  RESEARCH_DB_NAME: "research"
  RESEARCH_LLM_ENABLED: "true"
  RESEARCH_LLM_MODEL: "gemma3:1b"
  RESEARCH_LLM_URL: "http://ollama-service:11434"
---
apiVersion: v1
kind: Secret
metadata:
  name: research-system-secrets
type: Opaque
data:
  RESEARCH_DB_USER: <base64-encoded-username>
  RESEARCH_DB_PASSWORD: <base64-encoded-password>
  RESEARCH_BRAVE_API_KEY: <base64-encoded-api-key>
```

Then reference these in your deployment:

```yaml
env:
  - name: RESEARCH_ENV_MODE
    valueFrom:
      configMapKeyRef:
        name: research-system-config
        key: RESEARCH_ENV_MODE
  # ... other environment variables ...
```

## Troubleshooting

If you're experiencing configuration issues:

1. Use the health endpoint (`/health`) to view the current configuration
2. Set `RESEARCH_LOG_LEVEL=DEBUG` to see detailed configuration loading logs
3. Check logs for configuration validation warnings or errors