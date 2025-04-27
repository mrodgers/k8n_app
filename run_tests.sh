#!/bin/bash

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
CONTAINER_NAME="research-system-test"
EXIT_CODE=0

# Function to show usage information
show_help() {
    echo -e "${BLUE}Test Runner for Research System${NC}"
    echo ""
    echo "Usage: ./run_tests.sh [OPTIONS] [TEST_PATH]"
    echo ""
    echo "Options:"
    echo "  --no-build        Skip building the container"
    echo "  --clean           Remove stale containers and images before running"
    echo "  --help            Show this help message"
    echo "  --db-url URL      Specify a custom PostgreSQL test database URL" 
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh                              # Run all tests"
    echo "  ./run_tests.sh tests/test_integration       # Run integration tests"
    echo "  ./run_tests.sh --no-build tests/test_cli    # Run CLI tests without rebuilding"
    echo "  ./run_tests.sh tests/test_app.py::test_health_endpoint  # Run a specific test"
    echo "  ./run_tests.sh --clean                      # Clean up stale containers and run tests"
    echo "  ./run_tests.sh --db-url postgresql://user:pass@localhost:5432/testdb  # Use custom DB"
}

# Function to check if podman is available
check_podman() {
    if ! command -v podman &> /dev/null; then
        echo -e "${RED}Error: podman is not installed or not in PATH${NC}"
        echo "Please install podman to run the tests in containers."
        exit 1
    fi
    
    echo -e "${BLUE}Checking podman status...${NC}"
    if ! podman info &> /dev/null; then
        echo -e "${RED}Error: podman is not running or has configuration issues${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Podman is properly configured${NC}"
}

# Function to clean up stale containers and images
cleanup_containers() {
    echo -e "${BLUE}Cleaning up test resources...${NC}"
    
    # Stop and remove any stale test containers
    STALE_CONTAINERS=$(podman ps -a --filter "name=${CONTAINER_NAME}" --format "{{.ID}}")
    if [ -n "$STALE_CONTAINERS" ]; then
        echo -e "${YELLOW}Found stale test containers, removing...${NC}"
        podman rm -f $STALE_CONTAINERS
    fi
    
    # Remove dangling images (optional, can be quite aggressive)
    if podman images --filter "dangling=true" --format "{{.ID}}" | grep -q .; then
        echo -e "${YELLOW}Found dangling images, cleaning up...${NC}"
        podman rmi $(podman images --filter "dangling=true" --format "{{.ID}}") 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Function to handle errors and cleanup
handle_error() {
    echo -e "${RED}An error occurred during test execution${NC}"
    
    # Check for running containers related to our tests
    RUNNING_CONTAINERS=$(podman ps --filter "name=${CONTAINER_NAME}" --format "{{.ID}}")
    if [ -n "$RUNNING_CONTAINERS" ]; then
        echo -e "${YELLOW}Stopping leftover test containers...${NC}"
        podman stop $RUNNING_CONTAINERS
    fi
    
    exit 1
}

# Set trap for error handling
trap handle_error ERR

# Parse arguments
BUILD=true
CLEAN=false
TEST_PATH=""
DB_URL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help)
            show_help
            exit 0
            ;;
        --no-build)
            BUILD=false
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --db-url)
            DB_URL="$2"
            shift 2
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

# Check podman status first
check_podman

# Clean up if requested
if [ "$CLEAN" = true ]; then
    cleanup_containers
fi

# Build container if needed
if [ "$BUILD" = true ]; then
    echo -e "${BLUE}Building test container...${NC}"
    podman build -t ${CONTAINER_NAME} -f Dockerfile.test . || { 
        echo -e "${RED}Container build failed${NC}"
        exit 1
    }
fi

# Set up database URL environment variable if provided
DB_ENV=""
if [ -n "$DB_URL" ]; then
    echo -e "${BLUE}Using custom database URL for tests${NC}"
    DB_ENV="-e TEST_DATABASE_URL=${DB_URL}"
fi

# Run tests with appropriate error handling
echo -e "${BLUE}Running tests in container...${NC}"
if [ -z "$TEST_PATH" ]; then
    echo -e "${YELLOW}Running all tests${NC}"
    podman run --rm $DB_ENV ${CONTAINER_NAME} pytest -v
    EXIT_CODE=$?
else
    # Check if this is a specific command or a path
    if [[ "$TEST_PATH" == *"--cov"* ]]; then
        echo -e "${YELLOW}Running coverage tests${NC}"
        podman run --rm $DB_ENV ${CONTAINER_NAME} pytest --cov=src -v
        EXIT_CODE=$?
    else
        echo -e "${YELLOW}Running tests in: $TEST_PATH${NC}"
        podman run --rm $DB_ENV ${CONTAINER_NAME} pytest -v "$TEST_PATH"
        EXIT_CODE=$?
    fi
fi

# Check for test failures
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Tests failed with exit code: $EXIT_CODE${NC}"
else
    echo -e "${GREEN}✓ All tests passed successfully${NC}"
fi

# Final cleanup of any remaining resources
REMAINING_CONTAINERS=$(podman ps -a --filter "name=${CONTAINER_NAME}" --format "{{.ID}}")
if [ -n "$REMAINING_CONTAINERS" ]; then
    echo -e "${YELLOW}Cleaning up remaining test containers...${NC}"
    podman rm -f $REMAINING_CONTAINERS 2>/dev/null || true
fi

exit $EXIT_CODE