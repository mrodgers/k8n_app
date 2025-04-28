#!/bin/bash
# Script to run tests for the Ollama integration

set -e

# Default values
OLLAMA_URL="http://localhost:11434"
TEST_MODEL="gemma3:1b"
RUN_MODES=("mock") # Default to mock tests only

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --with-integration)
      RUN_MODES+=("integration")
      shift
      ;;
    --with-agent)
      RUN_MODES+=("agent")
      shift
      ;;
    --with-all)
      RUN_MODES=("mock" "integration" "agent")
      shift
      ;;
    --only-integration)
      RUN_MODES=("integration")
      shift
      ;;
    --only-agent)
      RUN_MODES=("agent")
      shift
      ;;
    --ollama-url=*)
      OLLAMA_URL="${1#*=}"
      shift
      ;;
    --test-model=*)
      TEST_MODEL="${1#*=}"
      shift
      ;;
    --ollama-url)
      OLLAMA_URL="$2"
      shift
      shift
      ;;
    --test-model)
      TEST_MODEL="$2"
      shift
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --with-integration   Run Ollama integration tests"
      echo "  --with-agent         Run agent tests with actual LLM calls"
      echo "  --with-all           Run all test types"
      echo "  --only-integration   Run only Ollama integration tests"
      echo "  --only-agent         Run only agent tests with LLM"
      echo "  --ollama-url         Specify Ollama URL (default: http://localhost:11434)"
      echo "  --test-model         Specify model to use for tests (default: gemma3:1b)"
      echo "  --help               Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Verify Docker is available if running integration tests
if [[ " ${RUN_MODES[*]} " =~ "integration" ]] || [[ " ${RUN_MODES[*]} " =~ "agent" ]]; then
  if ! command -v docker &> /dev/null; then
    echo "Docker is required for integration tests but not found"
    exit 1
  fi
fi

echo "==========================================="
echo "Running tests with the following settings:"
echo "Ollama URL: $OLLAMA_URL"
echo "Test model: $TEST_MODEL"
echo "Run modes: ${RUN_MODES[*]}"
echo "==========================================="

# Check if we need to start Ollama
if [[ " ${RUN_MODES[*]} " =~ "integration" ]] || [[ " ${RUN_MODES[*]} " =~ "agent" ]]; then
  echo "Checking if Ollama is available at $OLLAMA_URL"
  
  # Try to connect to Ollama
  if ! curl -s "$OLLAMA_URL/api/version" > /dev/null; then
    echo "Ollama not found at $OLLAMA_URL, starting local container..."
    
    # Clean up any existing container
    docker rm -f research-ollama 2>/dev/null || true
    
    # Start Ollama container
    docker run -d \
      --name research-ollama \
      -p 11434:11434 \
      -v ollama-data:/root/.ollama \
      ollama/ollama
    
    echo "Waiting for Ollama to start..."
    for i in {1..30}; do
      if curl -s "http://localhost:11434/api/version" > /dev/null; then
        echo "Ollama started successfully"
        break
      fi
      
      if [ $i -eq 30 ]; then
        echo "Failed to start Ollama container"
        docker logs research-ollama
        exit 1
      fi
      
      sleep 1
    done
  else
    echo "Ollama is already running at $OLLAMA_URL"
  fi
  
  # Check if test model is available
  echo "Checking if model $TEST_MODEL is available"
  if ! curl -s "$OLLAMA_URL/api/tags" | grep -q "\"name\":\"$TEST_MODEL\""; then
    echo "Pulling model $TEST_MODEL..."
    curl -X POST "$OLLAMA_URL/api/pull" -d "{\"model\":\"$TEST_MODEL\"}"
    echo "Model $TEST_MODEL pulled successfully"
  else
    echo "Model $TEST_MODEL is already available"
  fi
fi

# Run tests
for mode in "${RUN_MODES[@]}"; do
  case $mode in
    "mock")
      echo "Running mock tests..."
      # Run unit tests with LLM mocks
      PYTHONPATH=$(pwd) python -m pytest tests/test_llm -v
      ;;
      
    "integration")
      echo "Running Ollama integration tests..."
      # Run integration tests with Ollama
      OLLAMA_HOST=$(echo $OLLAMA_URL | sed 's|http://||' | sed 's|:.*||') \
      OLLAMA_PORT=$(echo $OLLAMA_URL | sed 's|.*:||') \
      OLLAMA_TEST_MODEL=$TEST_MODEL \
      SKIP_OLLAMA_INTEGRATION=false \
      PYTHONPATH=$(pwd) python -m pytest tests/test_integration/test_ollama_integration.py -v
      ;;
      
    "agent")
      echo "Running agent tests with LLM..."
      # Run agent tests with LLM
      OLLAMA_URL=$OLLAMA_URL \
      OLLAMA_MODEL=$TEST_MODEL \
      SKIP_LLM_TESTS=false \
      PYTHONPATH=$(pwd) python -m pytest tests/test_agents/test_planner_llm.py tests/test_agents/test_search_llm.py -v
      ;;
  esac
done

echo "All tests completed successfully!"