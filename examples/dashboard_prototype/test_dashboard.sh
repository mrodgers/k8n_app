#!/bin/bash
# Script to test the system dashboard with the Research System

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}      Research System Dashboard Testing Script         ${NC}"
echo -e "${BLUE}=======================================================${NC}"

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is required but not found.${NC}"
    echo "Please install Podman first."
    exit 1
fi

# Ensure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
echo -e "${BLUE}Working directory: $(pwd)${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found.${NC}"
    exit 1
fi

# Function to run dashboard in container mode
run_dashboard_container() {
    echo -e "${YELLOW}Starting dashboard in container mode...${NC}"
    
    # Check if the container image exists
    if ! podman image exists system-dashboard:latest; then
        echo -e "${YELLOW}Building system-dashboard image...${NC}"
        podman build -t system-dashboard .
    fi
    
    # Check if container is already running
    if podman ps | grep -q system-dashboard; then
        echo -e "${YELLOW}Dashboard container is already running.${NC}"
    else
        echo -e "${YELLOW}Starting dashboard container...${NC}"
        podman run -d --name system-dashboard \
            -v /run/podman/podman.sock:/run/podman/podman.sock \
            -v "$(pwd)/../../.env:/app/.env:ro" \
            -p 8090:8080 \
            system-dashboard
        
        # Wait for container to start
        echo -e "${YELLOW}Waiting for dashboard to start...${NC}"
        sleep 3
    fi
    
    # Check if dashboard is running
    if podman ps | grep -q system-dashboard; then
        echo -e "${GREEN}Dashboard container is running.${NC}"
        echo -e "${GREEN}Access the dashboard at: http://localhost:8090${NC}"
    else
        echo -e "${RED}Failed to start dashboard container.${NC}"
        podman logs system-dashboard
        exit 1
    fi
}

# Function to run dashboard in development mode
run_dashboard_dev() {
    echo -e "${YELLOW}Starting dashboard in development mode...${NC}"
    
    # Check if requirements are installed
    if ! python3 -c "import fastapi" &> /dev/null; then
        echo -e "${YELLOW}Installing Python dependencies...${NC}"
        pip install -r requirements.txt
    fi
    
    # Start the dashboard in the background
    echo -e "${YELLOW}Starting dashboard server...${NC}"
    python3 main.py &
    DASHBOARD_PID=$!
    
    # Wait for server to start
    echo -e "${YELLOW}Waiting for dashboard to start...${NC}"
    sleep 3
    
    # Check if process is running
    if ps -p $DASHBOARD_PID > /dev/null; then
        echo -e "${GREEN}Dashboard server is running with PID: $DASHBOARD_PID${NC}"
        echo -e "${GREEN}Access the dashboard at: http://localhost:8080${NC}"
    else
        echo -e "${RED}Failed to start dashboard server.${NC}"
        exit 1
    fi
    
    # Register cleanup function
    trap "echo -e '${YELLOW}Stopping dashboard server...${NC}'; kill $DASHBOARD_PID" EXIT
}

# Function to test Research System with dashboard
test_research_system() {
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}      Testing Research System with Dashboard           ${NC}"
    echo -e "${BLUE}=======================================================${NC}"
    
    # Navigate to the project root directory
    cd "../.."
    
    # Check if Research System is running
    if ! ./app_manager.sh status | grep -q "Server is running"; then
        echo -e "${YELLOW}Research System is not running. Starting it...${NC}"
        ./app_manager.sh start
        
        # Wait for server to start
        echo -e "${YELLOW}Waiting for Research System to start...${NC}"
        sleep 5
    fi
    
    # Check if the system is running
    if ./app_manager.sh status | grep -q "Server is running"; then
        echo -e "${GREEN}Research System is running.${NC}"
    else
        echo -e "${RED}Failed to start Research System.${NC}"
        exit 1
    fi
    
    # Create a test task
    echo -e "${YELLOW}Creating a test task...${NC}"
    TASK_OUTPUT=$(./app_manager.sh task create --title "Dashboard Test Task" --description "Testing system with dashboard" 2>&1)
    TASK_ID=$(echo "$TASK_OUTPUT" | grep -o "ID: [a-f0-9-]\+" | cut -d' ' -f2)
    
    if [ -n "$TASK_ID" ]; then
        echo -e "${GREEN}Created task with ID: $TASK_ID${NC}"
    else
        echo -e "${RED}Failed to create task.${NC}"
        echo "$TASK_OUTPUT"
        exit 1
    fi
    
    # Create a plan for the task
    echo -e "${YELLOW}Creating a research plan...${NC}"
    PLAN_OUTPUT=$(./app_manager.sh plan create --task-id "$TASK_ID" 2>&1)
    PLAN_ID=$(echo "$PLAN_OUTPUT" | grep -o "ID: [a-f0-9-]\+" | cut -d' ' -f2)
    
    if [ -n "$PLAN_ID" ]; then
        echo -e "${GREEN}Created plan with ID: $PLAN_ID${NC}"
    else
        echo -e "${RED}Failed to create plan.${NC}"
        echo "$PLAN_OUTPUT"
        exit 1
    fi
    
    # Run a search query
    echo -e "${YELLOW}Running a search query...${NC}"
    SEARCH_OUTPUT=$(./app_manager.sh search --query "Dashboard testing with Python" --max-results 3 2>&1)
    
    if echo "$SEARCH_OUTPUT" | grep -q "Search Results"; then
        echo -e "${GREEN}Search completed successfully.${NC}"
    else
        echo -e "${YELLOW}Search may have issues:${NC}"
        echo "$SEARCH_OUTPUT"
    fi
    
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${GREEN}Research System tests completed!${NC}"
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${YELLOW}Now check the dashboard to see all the containers and their status.${NC}"
    
    # Return to dashboard directory
    cd "$SCRIPT_DIR"
}

# Main execution
echo -e "${BLUE}Choose dashboard mode:${NC}"
echo -e "1) Run dashboard in container mode (recommended for testing)"
echo -e "2) Run dashboard in development mode"

read -p "Enter your choice (1/2): " choice

case $choice in
    1)
        run_dashboard_container
        test_research_system
        ;;
    2)
        run_dashboard_dev
        test_research_system
        # Keep script running so the dashboard doesn't terminate
        echo -e "${YELLOW}Press Ctrl+C to stop the dashboard.${NC}"
        while true; do sleep 1; done
        ;;
    *)
        echo -e "${RED}Invalid choice.${NC}"
        exit 1
        ;;
esac