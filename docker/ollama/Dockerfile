# Dockerfile for Ollama server
FROM ollama/ollama:latest

# Install necessary utilities
RUN apt-get update && \
    apt-get install -y curl jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create directory for persistent model storage
WORKDIR /root/.ollama

# Copy startup script
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

# Expose the Ollama API port
EXPOSE 11434

# Start Ollama
ENTRYPOINT ["/startup.sh"]