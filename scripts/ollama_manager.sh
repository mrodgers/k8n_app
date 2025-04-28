#!/bin/bash

# Ollama Manager Script for Research System
# Manages Ollama services in both Docker and Kubernetes environments

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_DOCKER_DIR="./docker/ollama"
OLLAMA_KUBE_MANIFEST="./kubernetes/ollama.yaml"
OLLAMA_PORT=11434
DEFAULT_MODELS="gemma3:1b"

# Function to display help
show_help() {
    echo -e "${BLUE}Ollama Manager for Research System${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start-docker    Start Ollama in Docker"
    echo "  stop-docker     Stop Ollama in Docker"
    echo "  status-docker   Check status of Ollama in Docker"
    echo "  logs-docker     View logs of Ollama in Docker"
    echo "  deploy-k8s      Deploy Ollama to Kubernetes"
    echo "  remove-k8s      Remove Ollama from Kubernetes"
    echo "  status-k8s      Check status of Ollama in Kubernetes"
    echo "  logs-k8s        View logs of Ollama in Kubernetes"
    echo "  test-conn       Test connection to Ollama server"
    echo "  pull-model      Pull a model to Ollama"
    echo "  list-models     List available models in Ollama"
    echo "  help            Show this help message"
    echo ""
    echo "Options:"
    echo "  --model=<model>     Specify a model (for pull-model)"
    echo "  --port=<port>       Specify a port (default: 11434)"
    echo "  --host=<host>       Specify a host (default: localhost)"
    echo ""
    echo "Examples:"
    echo "  $0 start-docker            # Start Ollama in Docker"
    echo "  $0 deploy-k8s              # Deploy Ollama to Kubernetes"
    echo "  $0 pull-model --model=llama2 # Pull the llama2 model"
    echo "  $0 test-conn               # Test connection to Ollama"
}

# Function to start Ollama in Docker
start_docker() {
    echo -e "${BLUE}Starting Ollama in Docker...${NC}"
    
    # Check if Docker is running
    if ! docker info &>/dev/null; then
        echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
    
    # Create .env file with default models
    echo "DEFAULT_MODELS=${DEFAULT_MODELS}" > "${OLLAMA_DOCKER_DIR}/.env"
    
    # Check if ollama directory exists
    if [ ! -d "$OLLAMA_DOCKER_DIR" ]; then
        echo -e "${RED}Ollama Docker directory not found at: $OLLAMA_DOCKER_DIR${NC}"
        exit 1
    fi
    
    # Start Ollama with docker-compose
    cd "$OLLAMA_DOCKER_DIR" || exit 1
    docker-compose up -d
    
    # Check if successfully started
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Ollama started successfully in Docker.${NC}"
        echo -e "${YELLOW}It may take a few moments to be ready.${NC}"
        echo -e "Ollama API is accessible at: ${BLUE}http://localhost:$OLLAMA_PORT${NC}"
    else
        echo -e "${RED}Failed to start Ollama in Docker.${NC}"
        exit 1
    fi
}

# Function to stop Ollama in Docker
stop_docker() {
    echo -e "${BLUE}Stopping Ollama in Docker...${NC}"
    
    # Check if Docker is running
    if ! docker info &>/dev/null; then
        echo -e "${RED}Docker is not running.${NC}"
        exit 1
    fi
    
    # Check if ollama directory exists
    if [ ! -d "$OLLAMA_DOCKER_DIR" ]; then
        echo -e "${RED}Ollama Docker directory not found at: $OLLAMA_DOCKER_DIR${NC}"
        exit 1
    fi
    
    # Stop Ollama with docker-compose
    cd "$OLLAMA_DOCKER_DIR" || exit 1
    docker-compose down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Ollama stopped successfully.${NC}"
    else
        echo -e "${RED}Failed to stop Ollama.${NC}"
        exit 1
    fi
}

# Function to check status of Ollama in Docker
status_docker() {
    echo -e "${BLUE}Checking Ollama status in Docker...${NC}"
    
    # Check if Docker is running
    if ! docker info &>/dev/null; then
        echo -e "${RED}Docker is not running.${NC}"
        exit 1
    fi
    
    # Check Ollama container status
    CONTAINER_ID=$(docker ps -qf "name=research-ollama")
    
    if [ -z "$CONTAINER_ID" ]; then
        echo -e "${YELLOW}Ollama is not running in Docker.${NC}"
        exit 1
    else
        echo -e "${GREEN}Ollama is running in Docker.${NC}"
        docker ps -f "name=research-ollama" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
        
        # Test API connection
        test_connection "localhost" "$OLLAMA_PORT"
    fi
}

# Function to view logs of Ollama in Docker
logs_docker() {
    echo -e "${BLUE}Viewing Ollama logs in Docker...${NC}"
    
    # Check if Docker is running
    if ! docker info &>/dev/null; then
        echo -e "${RED}Docker is not running.${NC}"
        exit 1
    fi
    
    # Get Ollama container ID
    CONTAINER_ID=$(docker ps -qf "name=research-ollama")
    
    if [ -z "$CONTAINER_ID" ]; then
        echo -e "${RED}Ollama is not running in Docker.${NC}"
        exit 1
    else
        docker logs -f "research-ollama"
    fi
}

# Function to deploy Ollama to Kubernetes
deploy_k8s() {
    echo -e "${BLUE}Deploying Ollama to Kubernetes...${NC}"
    
    # Check if kubectl is installed
    if ! command -v kubectl &>/dev/null; then
        echo -e "${RED}kubectl is not installed.${NC}"
        exit 1
    fi
    
    # Check if Kubernetes is running
    if ! kubectl cluster-info &>/dev/null; then
        echo -e "${RED}Kubernetes is not running or not accessible.${NC}"
        exit 1
    fi
    
    # Check if manifest exists
    if [ ! -f "$OLLAMA_KUBE_MANIFEST" ]; then
        echo -e "${RED}Kubernetes manifest not found at: $OLLAMA_KUBE_MANIFEST${NC}"
        exit 1
    fi
    
    # Create namespace if it doesn't exist
    kubectl create namespace research-system 2>/dev/null || true
    
    # Apply the manifest
    kubectl apply -f "$OLLAMA_KUBE_MANIFEST"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Ollama deployed to Kubernetes successfully.${NC}"
        echo -e "${YELLOW}It may take a few minutes to be ready.${NC}"
        echo -e "You can check status with: ${BLUE}$0 status-k8s${NC}"
    else
        echo -e "${RED}Failed to deploy Ollama to Kubernetes.${NC}"
        exit 1
    fi
}

# Function to remove Ollama from Kubernetes
remove_k8s() {
    echo -e "${BLUE}Removing Ollama from Kubernetes...${NC}"
    
    # Check if kubectl is installed
    if ! command -v kubectl &>/dev/null; then
        echo -e "${RED}kubectl is not installed.${NC}"
        exit 1
    fi
    
    # Check if Kubernetes is running
    if ! kubectl cluster-info &>/dev/null; then
        echo -e "${RED}Kubernetes is not running or not accessible.${NC}"
        exit 1
    fi
    
    # Check if manifest exists
    if [ ! -f "$OLLAMA_KUBE_MANIFEST" ]; then
        echo -e "${RED}Kubernetes manifest not found at: $OLLAMA_KUBE_MANIFEST${NC}"
        exit 1
    fi
    
    # Delete the resources
    kubectl delete -f "$OLLAMA_KUBE_MANIFEST"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Ollama removed from Kubernetes successfully.${NC}"
    else
        echo -e "${RED}Failed to remove Ollama from Kubernetes.${NC}"
        exit 1
    fi
}

# Function to check status of Ollama in Kubernetes
status_k8s() {
    echo -e "${BLUE}Checking Ollama status in Kubernetes...${NC}"
    
    # Check if kubectl is installed
    if ! command -v kubectl &>/dev/null; then
        echo -e "${RED}kubectl is not installed.${NC}"
        exit 1
    fi
    
    # Check if Kubernetes is running
    if ! kubectl cluster-info &>/dev/null; then
        echo -e "${RED}Kubernetes is not running or not accessible.${NC}"
        exit 1
    fi
    
    # Check if resources exist
    kubectl get deploy,svc,pvc,pods -n research-system -l app=ollama
    
    # Set up port-forward if needed
    RUNNING_POD=$(kubectl get pods -n research-system -l app=ollama -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -n "$RUNNING_POD" ]; then
        POD_STATUS=$(kubectl get pod -n research-system "$RUNNING_POD" -o jsonpath='{.status.phase}')
        
        if [ "$POD_STATUS" = "Running" ]; then
            echo -e "${GREEN}Ollama pod is running.${NC}"
            echo -e "${YELLOW}Setting up port-forward to test connection...${NC}"
            
            # Start port-forward in background
            kubectl port-forward -n research-system svc/ollama 8080:11434 &
            PORT_FORWARD_PID=$!
            
            # Wait for port-forward to be established
            sleep 2
            
            # Test connection
            test_connection "localhost" "8080"
            
            # Kill port-forward process
            kill $PORT_FORWARD_PID 2>/dev/null
        else
            echo -e "${YELLOW}Ollama pod is not yet running. Status: $POD_STATUS${NC}"
        fi
    else
        echo -e "${RED}No Ollama pods found in Kubernetes.${NC}"
    fi
}

# Function to view logs of Ollama in Kubernetes
logs_k8s() {
    echo -e "${BLUE}Viewing Ollama logs in Kubernetes...${NC}"
    
    # Check if kubectl is installed
    if ! command -v kubectl &>/dev/null; then
        echo -e "${RED}kubectl is not installed.${NC}"
        exit 1
    fi
    
    # Check if Kubernetes is running
    if ! kubectl cluster-info &>/dev/null; then
        echo -e "${RED}Kubernetes is not running or not accessible.${NC}"
        exit 1
    fi
    
    # Get Ollama pod
    POD=$(kubectl get pods -n research-system -l app=ollama -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$POD" ]; then
        echo -e "${RED}No Ollama pods found in Kubernetes.${NC}"
        exit 1
    else
        kubectl logs -f -n research-system "$POD"
    fi
}

# Function to test connection to Ollama server
test_connection() {
    local host=$1
    local port=$2
    
    echo -e "${BLUE}Testing connection to Ollama server at ${host}:${port}...${NC}"
    
    # Try to get the version from Ollama API
    VERSION_INFO=$(curl -s -m 5 "http://${host}:${port}/api/version")
    
    if [[ "$VERSION_INFO" == *"version"* ]]; then
        echo -e "${GREEN}Successfully connected to Ollama server.${NC}"
        echo "Ollama version: $(echo "$VERSION_INFO" | grep -o '"version":"[^"]*' | cut -d'"' -f4)"
        return 0
    else
        echo -e "${RED}Failed to connect to Ollama server.${NC}"
        return 1
    fi
}

# Function to pull a model to Ollama
pull_model() {
    local host=$1
    local port=$2
    local model=$3
    
    echo -e "${BLUE}Pulling model ${model} to Ollama server at ${host}:${port}...${NC}"
    
    # Pull model using Ollama API
    PULL_RESPONSE=$(curl -s -X POST "http://${host}:${port}/api/pull" -d "{\"model\": \"${model}\", \"stream\": false}")
    
    if [[ "$PULL_RESPONSE" == *"success"* ]]; then
        echo -e "${GREEN}Successfully pulled model ${model}.${NC}"
        return 0
    else
        echo -e "${RED}Failed to pull model ${model}.${NC}"
        echo "Response: $PULL_RESPONSE"
        return 1
    fi
}

# Function to list available models in Ollama
list_models() {
    local host=$1
    local port=$2
    
    echo -e "${BLUE}Listing available models in Ollama at ${host}:${port}...${NC}"
    
    # List models using Ollama API
    MODELS_INFO=$(curl -s "http://${host}:${port}/api/tags")
    
    if [[ "$MODELS_INFO" == *"models"* ]]; then
        echo -e "${GREEN}Available models:${NC}"
        echo "$MODELS_INFO" | grep -o '"name":"[^"]*' | cut -d'"' -f4
        return 0
    else
        echo -e "${RED}Failed to list models.${NC}"
        echo "Response: $MODELS_INFO"
        return 1
    fi
}

# Parse command-line arguments
COMMAND=""
MODEL=""
HOST="localhost"
PORT="$OLLAMA_PORT"

# Parse arguments
for arg in "$@"; do
    case $arg in
        start-docker|stop-docker|status-docker|logs-docker|deploy-k8s|remove-k8s|status-k8s|logs-k8s|test-conn|pull-model|list-models|help)
            COMMAND="$arg"
            ;;
        --model=*)
            MODEL="${arg#*=}"
            ;;
        --port=*)
            PORT="${arg#*=}"
            ;;
        --host=*)
            HOST="${arg#*=}"
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Execute the requested command
case "$COMMAND" in
    start-docker)
        start_docker
        ;;
    stop-docker)
        stop_docker
        ;;
    status-docker)
        status_docker
        ;;
    logs-docker)
        logs_docker
        ;;
    deploy-k8s)
        deploy_k8s
        ;;
    remove-k8s)
        remove_k8s
        ;;
    status-k8s)
        status_k8s
        ;;
    logs-k8s)
        logs_k8s
        ;;
    test-conn)
        test_connection "$HOST" "$PORT"
        ;;
    pull-model)
        if [ -z "$MODEL" ]; then
            echo -e "${RED}No model specified. Use --model=<model>.${NC}"
            exit 1
        fi
        pull_model "$HOST" "$PORT" "$MODEL"
        ;;
    list-models)
        list_models "$HOST" "$PORT"
        ;;
    help|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

exit 0