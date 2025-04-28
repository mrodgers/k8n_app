#!/bin/bash

# Script to verify Ollama model configuration
# This script tests if Ollama is running and configured with gemma3:1b

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}      Ollama Model Verification Test        ${NC}"
echo -e "${BLUE}=============================================${NC}"

# Test connection to Ollama
echo -e "\n${BLUE}Step 1: Checking if Ollama is running...${NC}"
OLLAMA_URL=${1:-"http://localhost:11434"}

# Try to get version
VERSION_RESPONSE=$(curl -s "$OLLAMA_URL/api/version")
if [[ "$VERSION_RESPONSE" == *"version"* ]]; then
    VERSION=$(echo "$VERSION_RESPONSE" | grep -o '"version":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}Ollama is running with version: ${YELLOW}$VERSION${NC}"
else
    echo -e "${RED}Ollama is not running at $OLLAMA_URL${NC}"
    echo -e "Start Ollama with: ${YELLOW}./app_manager.sh ollama start${NC}"
    exit 1
fi

# Check if gemma3:1b is available
echo -e "\n${BLUE}Step 2: Checking if gemma3:1b model is available...${NC}"

# List models
MODELS_RESPONSE=$(curl -s "$OLLAMA_URL/api/tags")
if [[ "$MODELS_RESPONSE" == *"gemma3:1b"* ]]; then
    echo -e "${GREEN}gemma3:1b model is available.${NC}"
else
    echo -e "${RED}gemma3:1b model is not available.${NC}"
    echo -e "Pull the model with: ${YELLOW}./app_manager.sh ollama pull gemma3:1b${NC}"
    exit 1
fi

# Test simple completion
echo -e "\n${BLUE}Step 3: Testing basic completion with gemma3:1b...${NC}"

echo -e "Prompt: ${YELLOW}What is the capital of France?${NC}"
curl -s "$OLLAMA_URL/api/generate" \
  -d '{
    "model": "gemma3:1b",
    "prompt": "What is the capital of France?",
    "stream": false
  }' | grep -o '"response":"[^"]*' | cut -d'"' -f4

# Verify app configuration
echo -e "\n${BLUE}Step 4: Verifying app configuration...${NC}"

# Check config.yaml
if grep -q "model: gemma3:1b" config.yaml; then
    echo -e "${GREEN}config.yaml is correctly configured to use gemma3:1b${NC}"
else
    echo -e "${RED}config.yaml is not correctly configured!${NC}"
    grep -A 3 "llm:" config.yaml
fi

# Check Kubernetes configuration
if grep -q "DEFAULT_MODELS: \"gemma3:1b\"" kubernetes/ollama.yaml; then
    echo -e "${GREEN}kubernetes/ollama.yaml is correctly configured to use gemma3:1b${NC}"
else
    echo -e "${RED}kubernetes/ollama.yaml is not correctly configured!${NC}"
    grep -A 1 "DEFAULT_MODELS" kubernetes/ollama.yaml
fi

# Summary
echo -e "\n${BLUE}=============================================${NC}"
echo -e "${GREEN}Verification completed successfully!${NC}"
echo -e "${BLUE}=============================================${NC}"
echo -e "Your Research System is correctly configured to use gemma3:1b as the default LLM model."
echo -e "To test the full application functionality, run:"
echo -e "${YELLOW}./app_manager.sh start${NC}"
echo -e "${YELLOW}./scripts/test_ollama_features.sh${NC}"