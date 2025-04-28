#!/bin/bash

# Research System Management Script
# This script provides commands for running and managing the Research System

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure logs directory exists
mkdir -p logs

# Check for required tools
check_dependencies() {
    # Check for gunicorn
    if ! command -v gunicorn &> /dev/null; then
        echo -e "${RED}gunicorn is not installed. Please install required dependencies.${NC}"
        echo -e "Run one of the following commands to install dependencies:"
        echo -e "${YELLOW}pip install -r requirements.txt${NC}"
        
        # Check if uv is available
        if command -v uv &> /dev/null; then
            echo -e "or using uv (faster):"
            echo -e "${YELLOW}uv venv && source .venv/bin/activate && uv pip install -r requirements.txt${NC}"
        fi
        return 1
    fi
    
    # Check for pytest (only when running tests)
    if [ "$1" == "test" ] && ! command -v pytest &> /dev/null; then
        echo -e "${RED}pytest is not installed. Please install required dependencies.${NC}"
        echo -e "Run one of the following commands to install dependencies:"
        echo -e "${YELLOW}pip install -r requirements.txt${NC}"
        
        # Check if uv is available
        if command -v uv &> /dev/null; then
            echo -e "or using uv (faster):"
            echo -e "${YELLOW}uv venv && source .venv/bin/activate && uv pip install -r requirements.txt${NC}"
        fi
        return 1
    fi
    
    return 0
}

# Function to show help
show_help() {
    echo -e "${BLUE}Research System Management Script${NC}"
    echo ""
    echo "Usage: ./app_manager.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start            Start the web server"
    echo "  stop             Stop the web server"
    echo "  status           Check if the server is running"
    echo "  logs             View server logs"
    echo "  search <query>   Perform a search query"
    echo "  task <subcommand> Manage research tasks"
    echo "  result <subcommand> Manage research results"
    echo "  plan <subcommand> Manage research plans"
    echo "  test             Run tests"
    echo "  build [options]  Build application and container"
    echo "  version          Show current version information"
    echo "  ollama <subcommand> Manage Ollama LLM service"
    echo "  help             Show this help message"
    echo ""
    echo "Build options:"
    echo "  --patch          Increment patch version (1.0.0 -> 1.0.1)"
    echo "  --minor          Increment minor version (1.0.0 -> 1.1.0)"
    echo "  --major          Increment major version (1.0.0 -> 2.0.0)"
    echo "  --tag            Create git tag for the release"
    echo "  --no-git         Skip git operations"
    echo "  --build-only     Update version but skip container build"
    echo ""
    echo "Examples:"
    echo "  ./app_manager.sh start"
    echo "  ./app_manager.sh search \"artificial intelligence\""
    echo "  ./app_manager.sh task create --title \"AI Research\" --description \"Research on AI trends\""
    echo "  ./app_manager.sh build --patch"
    echo "  ./app_manager.sh ollama start"
    echo "  ./app_manager.sh test"
    echo ""
    echo "Setup Instructions:"
    echo "  1. Create a virtual environment (choose one):"
    echo "     - Standard Python: python -m venv venv && source venv/bin/activate"
    echo "     - Using uv (faster): uv venv && source .venv/bin/activate"
    echo "  2. Install dependencies (choose one):"
    echo "     - Standard pip: pip install -r requirements.txt"
    echo "     - Using uv (faster): uv pip install -r requirements.txt"
}

# Function to start the server
start_server() {
    echo -e "${BLUE}Starting Research System server...${NC}"
    
    # Check for required dependencies
    if ! check_dependencies; then
        return 1
    fi
    
    # Check if server is already running
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${YELLOW}Server is already running.${NC}"
        return 0
    fi
    
    # Create data directory if it doesn't exist
    mkdir -p data
    
    # Start the server with gunicorn using uvicorn worker (using port 8181 instead of 8080)
    PYTHONPATH=$(pwd) gunicorn --bind 0.0.0.0:8181 --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --log-file logs/server.log --daemon src.app:app
    
    # Check if server started correctly
    sleep 2
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${GREEN}Server started successfully.${NC}"
        echo -e "API is accessible at ${BLUE}http://localhost:8181${NC}"
    else
        echo -e "${RED}Failed to start server. Check logs for details.${NC}"
        cat logs/server.log | tail -n 20
        return 1
    fi
}

# Function to stop the server
stop_server() {
    echo -e "${BLUE}Stopping Research System server...${NC}"
    if ! pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${YELLOW}Server is not running.${NC}"
        return 0
    fi
    
    # Kill gunicorn processes
    pkill -f "gunicorn.*app:app"
    sleep 2
    
    # Check if server stopped correctly
    if ! pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${GREEN}Server stopped successfully.${NC}"
    else
        echo -e "${RED}Failed to stop server. Try killing the process manually.${NC}"
        echo -e "Use: ${YELLOW}pkill -9 -f \"gunicorn.*app:app\"${NC}"
        return 1
    fi
}

# Function to check server status
check_status() {
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${GREEN}Server is running.${NC}"
        echo -e "API is accessible at ${BLUE}http://localhost:8181${NC}"
        
        # Try to get server status via API
        echo -e "\n${BLUE}Checking server health...${NC}"
        HEALTH=$(curl -s http://localhost:8181/health)
        if [[ $HEALTH == *"healthy"* ]]; then
            echo -e "${GREEN}Server health check: OK${NC}"
        else
            echo -e "${RED}Server health check failed.${NC}"
        fi
    else
        echo -e "${RED}Server is not running.${NC}"
    fi
}

# Function to view logs
view_logs() {
    if [ -f "logs/server.log" ]; then
        echo -e "${BLUE}Displaying server logs (last 20 lines):${NC}"
        tail -n 20 logs/server.log
    else
        echo -e "${RED}No log file found.${NC}"
    fi
}

# Function to run CLI commands
run_cli() {
    # Check for required dependencies
    if ! check_dependencies; then
        return 1
    fi
    
    # Add current directory to PYTHONPATH to ensure modules can be found
    CLI_COMMAND="PYTHONPATH=$(pwd) python -m src.research_system.cli.main $@"
    echo -e "${BLUE}Executing: ${YELLOW}$CLI_COMMAND${NC}"
    eval "$CLI_COMMAND"
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}Running tests...${NC}"
    
    # Check for required dependencies
    if ! check_dependencies "test"; then
        return 1
    fi
    
    # Add current directory to PYTHONPATH to ensure modules can be found
    PYTHONPATH="$(pwd):${PYTHONPATH}" python -m pytest
}

# Function to manage Ollama
manage_ollama() {
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is required to run Ollama but not found.${NC}"
        echo -e "Please install Docker and try again."
        return 1
    fi

    OLLAMA_CONTAINER="research-ollama"
    MODEL="${3:-gemma3:1b}"  # Default model is gemma3:1b
    
    case "$2" in
        start)
            echo -e "${BLUE}Starting Ollama service...${NC}"
            
            # Check if Ollama is already running
            if docker ps | grep -q "$OLLAMA_CONTAINER"; then
                echo -e "${YELLOW}Ollama is already running.${NC}"
                docker ps | grep "$OLLAMA_CONTAINER"
                return 0
            fi
            
            # Start Ollama container
            docker run -d \
                --name $OLLAMA_CONTAINER \
                -p 11434:11434 \
                -v ollama-data:/root/.ollama \
                ollama/ollama
            
            echo -e "${GREEN}Ollama started successfully.${NC}"
            echo -e "Waiting for Ollama to initialize..."
            sleep 3
            
            # Pull the specified model if provided
            if [ ! -z "$MODEL" ]; then
                echo -e "${BLUE}Pulling model: $MODEL${NC}"
                curl -s -X POST "http://localhost:11434/api/pull" -d "{\"model\":\"$MODEL\"}"
                echo -e "${GREEN}Model $MODEL is now available.${NC}"
            fi
            
            echo -e "${GREEN}Ollama is ready at ${BLUE}http://localhost:11434${NC}"
            ;;
            
        stop)
            echo -e "${BLUE}Stopping Ollama service...${NC}"
            if ! docker ps | grep -q "$OLLAMA_CONTAINER"; then
                echo -e "${YELLOW}Ollama is not running.${NC}"
                return 0
            fi
            
            docker stop $OLLAMA_CONTAINER
            docker rm $OLLAMA_CONTAINER
            echo -e "${GREEN}Ollama stopped successfully.${NC}"
            ;;
            
        status)
            echo -e "${BLUE}Checking Ollama status...${NC}"
            if docker ps | grep -q "$OLLAMA_CONTAINER"; then
                echo -e "${GREEN}Ollama is running.${NC}"
                docker ps | grep "$OLLAMA_CONTAINER"
                
                # Get version information
                VERSION=$(curl -s http://localhost:11434/api/version)
                echo -e "Ollama version: ${BLUE}$(echo $VERSION | grep -o '"version":"[^"]*' | cut -d'"' -f4)${NC}"
                
                # List models
                echo -e "\n${BLUE}Available models:${NC}"
                MODELS=$(curl -s http://localhost:11434/api/tags)
                echo "$MODELS" | grep -o '"name":"[^"]*' | cut -d'"' -f4 | nl
            else
                echo -e "${RED}Ollama is not running.${NC}"
            fi
            ;;
            
        pull)
            echo -e "${BLUE}Pulling Ollama model: $MODEL${NC}"
            if ! docker ps | grep -q "$OLLAMA_CONTAINER"; then
                echo -e "${RED}Ollama is not running. Start it first with: ${YELLOW}./app_manager.sh ollama start${NC}"
                return 1
            fi
            
            curl -s -X POST "http://localhost:11434/api/pull" -d "{\"model\":\"$MODEL\"}"
            echo -e "${GREEN}Model $MODEL is now available.${NC}"
            ;;
            
        logs)
            echo -e "${BLUE}Viewing Ollama logs...${NC}"
            if ! docker ps | grep -q "$OLLAMA_CONTAINER"; then
                echo -e "${RED}Ollama is not running.${NC}"
                return 1
            fi
            
            docker logs $OLLAMA_CONTAINER
            ;;
            
        test)
            echo -e "${BLUE}Testing Ollama with LLM functionality...${NC}"
            if [ ! -x "./scripts/run_llm_tests.sh" ]; then
                echo -e "${RED}Test script not found or not executable.${NC}"
                echo -e "Please check if ./scripts/run_llm_tests.sh exists and is executable."
                return 1
            fi
            
            # Run tests with mock by default
            TEST_ARGS="${@:3}"  # Get all arguments after "ollama test"
            if [ -z "$TEST_ARGS" ]; then
                # No args provided, just run with mock tests
                ./scripts/run_llm_tests.sh
            else
                # Pass all additional args to the test script
                ./scripts/run_llm_tests.sh $TEST_ARGS
            fi
            ;;
            
        *)
            echo -e "${RED}Unknown Ollama command: $2${NC}"
            echo -e "Available Ollama commands: start, stop, status, pull, logs, test"
            return 1
            ;;
    esac
}

# Function to build the application
build_app() {
    echo -e "${BLUE}Building Research System...${NC}"
    
    # Parse build arguments
    local build_args=""
    local minor=false
    local patch=false
    local major=false
    local tag=false
    local no_git=false
    local build_only=false
    
    # Skip the first argument which is "build"
    shift
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --minor)
                minor=true
                build_args="$build_args --minor"
                shift
                ;;
            --patch)
                patch=true
                build_args="$build_args --patch"
                shift
                ;;
            --major)
                major=true
                build_args="$build_args --major"
                shift
                ;;
            --tag)
                tag=true
                build_args="$build_args --tag"
                shift
                ;;
            --no-git)
                no_git=true
                build_args="$build_args --no-git"
                shift
                ;;
            --build-only)
                build_only=true
                build_args="$build_args --build-only"
                shift
                ;;
            *)
                echo -e "${RED}Unknown build option: $1${NC}"
                echo -e "Available options: --minor, --patch, --major, --tag, --no-git, --build-only"
                return 1
                ;;
        esac
    done
    
    # Run the build script
    if [ -x "./scripts/build_container.sh" ]; then
        "./scripts/build_container.sh" $build_args
    else
        echo -e "${RED}Build script not found or not executable${NC}"
        echo -e "Please make sure scripts/build_container.sh exists and is executable"
        return 1
    fi
}

# Function to show the current version
show_version() {
    if [ -f "src/research_system/version.py" ]; then
        echo -e "${BLUE}Research System Version Information:${NC}"
        python -c "
from src.research_system.version import get_version_info
info = get_version_info()
print(f'  Version:      {info[\"version\"]}')
print(f'  Build Number: {info[\"build_number\"]}')
print(f'  Build Date:   {info[\"build_date\"]}')
print(f'  Git Revision: {info[\"git_revision\"] or \"N/A\"}')
"
    else
        echo -e "${RED}Version information not available${NC}"
        echo -e "Version module not found at src/research_system/version.py"
        return 1
    fi
}

# Main logic
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    search|task|result|plan)
        run_cli "$@"
        ;;
    test)
        run_tests
        ;;
    build)
        build_app "$@"
        ;;
    version)
        show_version
        ;;
    ollama)
        manage_ollama "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac

exit 0