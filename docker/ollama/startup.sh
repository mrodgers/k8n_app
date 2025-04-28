#!/bin/bash
# Startup script for Ollama container

# Log the start time
echo "Starting Ollama server at $(date)"

# Set default models if specified
if [ -n "$DEFAULT_MODELS" ]; then
  echo "Pulling default models: $DEFAULT_MODELS"
  for model in $(echo $DEFAULT_MODELS | tr "," " "); do
    echo "Pulling model: $model"
    ollama pull $model &
  done
  # Wait for models to be pulled
  wait
fi

# Start ollama server in the foreground
OLLAMA_HOST=0.0.0.0 exec ollama serve