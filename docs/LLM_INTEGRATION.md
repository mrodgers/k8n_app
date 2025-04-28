# LLM Integration in the Research System

This document describes the integration of Large Language Models (LLMs) into the Research System, using Ollama for local model hosting.

## Overview

The Research System now leverages LLMs through Ollama to enhance the following capabilities:

1. **Research Planning**: Generate structured, intelligent research plans
2. **Content Extraction**: Extract and summarize content from web pages
3. **Relevance Ranking**: Evaluate search results for relevance to the query
4. **Fallback Mechanisms**: Continue to function when LLM services are unavailable

## Architecture

The LLM integration architecture consists of the following components:

```
┌──────────────────┐       ┌──────────────────┐
│                  │       │                  │
│  Research System ├───────►      Ollama      │
│                  │       │                  │
└────────┬─────────┘       └──────────────────┘
         │
         │
┌────────▼─────────┐
│                  │
│    PostgreSQL    │
│                  │
└──────────────────┘
```

- **Research System**: Includes LLM-enhanced planner and search agents
- **Ollama**: Provides local LLM capabilities through a containerized service
- **PostgreSQL**: Stores tasks, plans, and results

## Configuration

LLM integration can be configured through:

1. **Environment Variables**:
   - `OLLAMA_URL`: URL of the Ollama server (default: http://localhost:11434)
   - `OLLAMA_MODEL`: Default model to use (default: gemma3:1b)
   - `PLANNER_LLM_MODEL`: Model for the planner agent (defaults to OLLAMA_MODEL)
   - `SEARCH_LLM_MODEL`: Model for the search agent (defaults to OLLAMA_MODEL)
   - `USE_LLM`: Enable/disable LLM features (true/false)

2. **Configuration File** (config.yaml):
   ```yaml
   llm:
     enabled: true
     model: gemma3:1b
     url: http://localhost:11434
     timeout: 120
   ```

3. **Kubernetes ConfigMap**:
   ```yaml
   llm:
     enabled: true
     model: gemma3:1b
     url: http://ollama-service:11434
     timeout: 120
   ```

## Supported Models

The system has been tested with the following models:

- **gemma3:1b** (default): A lightweight yet capable model from Google
- **mistral** and **mixtral**: Excellent open-source models with strong performance
- **llama3** models: Versatile models from Meta
- **orca-mini**: Alternative smaller model suitable for testing

To use different models, they must be pulled into Ollama. For example:

```bash
./app_manager.sh ollama pull llama3
```

## Fallback Mechanisms

The system is designed to function even when LLM capabilities are unavailable:

1. **Planner Agent**: Falls back to template-based planning
2. **Search Agent**: Uses keyword matching instead of LLM-based relevance ranking
3. **Content Extraction**: Uses basic HTML parsing when LLM is unavailable

## Implementation Details

### Client Implementation

The Ollama client (`src/research_system/llm/ollama_client.py`) implements:

- Both synchronous and asynchronous APIs
- Completion and chat interfaces
- Embedding generation
- Model management (pulling, listing)
- Streaming support
- Error handling and fallbacks

### Agent Integration

1. **Planner Agent** (`src/research_system/agents/planner.py`):
   - Uses LLM to generate intelligent, structured research plans
   - Parses and validates LLM responses for consistent output

2. **Search Agent** (`src/research_system/agents/search.py`):
   - Uses LLM for content extraction from webpages
   - Evaluates search result relevance using LLM
   - Generates more relevant citations and summaries

## Testing

The LLM integration includes comprehensive tests:

1. **Unit Tests**: Test client with mocked responses
2. **Integration Tests**: Test against a real Ollama server
3. **Agent Tests**: Test LLM-enhanced agent functionality

To run tests:

```bash
# Run tests with mocked LLM responses only
./scripts/run_llm_tests.sh

# Run tests with a live Ollama server
./scripts/run_llm_tests.sh --with-integration

# Run all tests including actual agent LLM calls
./scripts/run_llm_tests.sh --with-all
```

## Kubernetes Deployment

The Ollama component can be deployed to Kubernetes:

```bash
kubectl apply -f kubernetes/ollama.yaml
```

Key features of the Kubernetes deployment:

- Persistent volume for model storage
- Resource limits appropriately set for LLM inference
- Readiness/liveness probes for health monitoring
- Automatic model preloading
- Init containers for ensuring dependencies

## Development Workflow

For local development with LLM capabilities:

1. Start Ollama:
   ```bash
   ./app_manager.sh ollama start
   ```

2. Start the Research System:
   ```bash
   ./app_manager.sh start
   ```

3. Test LLM features:
   ```bash
   ./scripts/test_ollama_features.sh
   ```

## Troubleshooting

Common issues and solutions:

1. **Ollama connection errors**:
   - Verify Ollama is running: `./app_manager.sh ollama status`
   - Check URL configuration: `OLLAMA_URL` environment variable or config setting

2. **Model not found errors**:
   - Pull the model: `./app_manager.sh ollama pull gemma3:1b`
   - Verify model is available: `./app_manager.sh ollama status`

3. **High memory usage**:
   - Use a smaller model (e.g., orca-mini) if gemma3:1b is too resource-intensive
   - Adjust the resources in Kubernetes manifests

4. **Slow performance**:
   - Ensure model is preloaded: `./app_manager.sh ollama pull <model>`
   - Switch to a smaller/faster model if needed
   - Consider GPU acceleration for production deployments

## Next Steps

Future enhancements for LLM integration:

1. **Response Caching**: Implement caching for common LLM requests
2. **GPU Support**: Add GPU acceleration for Ollama
3. **Multi-Model Support**: Allow different agents to use different models
4. **Hybrid Search**: Combine embedding-based and keyword search
5. **Content Generation**: Add report generation capabilities