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
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./app_manager.sh start"
    echo "  ./app_manager.sh search \"artificial intelligence\""
    echo "  ./app_manager.sh task create --title \"AI Research\" --description \"Research on AI trends\""
    echo "  ./app_manager.sh test"
}

# Function to start the server
start_server() {
    echo -e "${BLUE}Starting Research System server...${NC}"
    # Check if server is already running
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${YELLOW}Server is already running.${NC}"
        return 0
    fi
    
    # Start the server with gunicorn
    gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 --log-file logs/server.log --daemon src.app:app
    
    # Check if server started correctly
    sleep 2
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo -e "${GREEN}Server started successfully.${NC}"
        echo -e "API is accessible at ${BLUE}http://localhost:8080${NC}"
    else
        echo -e "${RED}Failed to start server. Check logs for details.${NC}"
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
        echo -e "API is accessible at ${BLUE}http://localhost:8080${NC}"
        
        # Try to get server status via API
        echo -e "\n${BLUE}Checking server health...${NC}"
        HEALTH=$(curl -s http://localhost:8080/health)
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
    CLI_COMMAND="python -m src.research_system.cli.main $@"
    echo -e "${BLUE}Executing: ${YELLOW}$CLI_COMMAND${NC}"
    $CLI_COMMAND
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}Running tests...${NC}"
    python -m pytest
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