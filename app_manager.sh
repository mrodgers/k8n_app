#!/bin/bash
set -e

# Configuration variables
APP_NAME="python-app"
DEFAULT_PORT="8080"
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/app_manager_v2_$(date +"%Y%m%d_%H%M%S").log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function for logging
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to display usage information
show_usage() {
  echo "Python App Manager v2 - Simplified Management Script"
  echo ""
  echo "Usage: ./app_manager_v2.sh COMMAND [OPTIONS]"
  echo ""
  echo "Commands:"
  echo "  start       Start the application"
  echo "  stop        Stop the application"
  echo "  restart     Restart the application"
  echo "  status      Show current status of the application"
  echo "  logs        View application logs"
  echo "  connect     Connect to the application (set up port forwarding)"
  echo "  clean       Clean up all resources"
  echo "  help        Show this help message"
  echo ""
  echo "Options:"
  echo "  -p, --port PORT       Port for accessing the application (default: ${DEFAULT_PORT})"
  echo "  -d, --debug           Enable debug mode with verbose output"
  echo ""
  echo "Examples:"
  echo "  ./app_manager_v2.sh start           # Start app with default settings"
  echo "  ./app_manager_v2.sh start -p 8081   # Start app on port 8081"
  echo "  ./app_manager_v2.sh status          # Check status of the application"
  echo "  ./app_manager_v2.sh connect         # Set up port forwarding to access the app"
}

# Default values
PORT="${DEFAULT_PORT}"
DEBUG=false

# Parse command line arguments
if [ $# -lt 1 ]; then
  show_usage
  exit 1
fi

COMMAND="$1"
shift

# Parse remaining options
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--port)
      PORT="$2"
      shift 2
      ;;
    -d|--debug)
      DEBUG=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      exit 1
      ;;
  esac
done

# Function to print debug information
print_debug_info() {
  if [ "$DEBUG" = true ]; then
    log "Debug mode enabled"
    log "Podman version: $(podman --version 2>&1 || echo 'Not installed')"
    log "Current directory: $(pwd)"
    
    # Check Podman machine status
    if command -v podman &> /dev/null; then
      log "Podman machine status:"
      podman machine list 2>&1 | tee -a "$LOG_FILE"
      
      # Try to get Podman machine IP
      if podman machine inspect --format '{{.NetworkSettings.IPAddress}}' 2>/dev/null; then
        PODMAN_IP=$(podman machine inspect --format '{{.NetworkSettings.IPAddress}}' 2>/dev/null)
        log "Podman machine IP: $PODMAN_IP"
      else
        log "No Podman machine IP found"
      fi
    fi
  fi
}

# Function to check if Podman machine is running
ensure_podman_running() {
  if ! podman machine list | grep -q "Currently running"; then
    log "Starting Podman machine..."
    podman machine start
  else
    log "Podman machine is already running"
  fi
}

# Function to check if port is in use
check_port_in_use() {
  local port=$1
  if podman ps | grep -q ":${port}->"; then
    log "WARNING: Port ${port} is already in use by another container"
    podman ps | grep ":${port}->" | tee -a "$LOG_FILE"
    return 0  # Port is in use
  fi
  return 1  # Port is not in use
}

# Function to find an available port starting from the given port
find_available_port() {
  local start_port=$1
  local port=$start_port
  local max_attempts=10
  local attempts=0
  
  log "Finding available port starting from $start_port"
  
  while [ $attempts -lt $max_attempts ]; do
    if ! check_port_in_use $port; then
      log "Port $port is available"
      echo $port
      return 0
    fi
    
    log "Port $port is in use, trying next port"
    port=$((port + 1))
    attempts=$((attempts + 1))
  done
  
  log "Failed to find available port after $max_attempts attempts"
  return 1
}

# Function to check application status
check_status() {
  log "Checking application status"
  
  # Check for all instances of the application
  log "Standalone container status:"
  if podman ps | grep -q "$APP_NAME"; then
    podman ps | grep "$APP_NAME" | tee -a "$LOG_FILE"
    CONTAINER_ID=$(podman ps | grep "$APP_NAME" | awk '{print $1}' | head -1)
    PORT_MAPPING=$(podman inspect "$CONTAINER_ID" --format '{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{end}}')
    log "Container port mapping: $PORT_MAPPING"
    log "Application is RUNNING"
    return 0
  else
    if podman ps -a | grep -q "$APP_NAME"; then
      log "Application container exists but is not running"
      podman ps -a | grep "$APP_NAME" | tee -a "$LOG_FILE"
      return 1
    else
      log "Application is NOT RUNNING"
      return 1
    fi
  fi
}

# Function to clean up any existing resources
clean_resources() {
  log "Cleaning up existing resources"
  
  # Stop and remove any existing containers with our app name
  for container in $(podman ps -a --format "{{.Names}}" | grep "$APP_NAME"); do
    log "Stopping and removing container: $container"
    podman stop "$container" 2>/dev/null || true
    podman rm "$container" 2>/dev/null || true
  done
  
  # Remove any pods related to our app
  for pod in $(podman pod ls -a --format "{{.Name}}" | grep "$APP_NAME"); do
    log "Removing pod: $pod"
    podman pod rm -f "$pod" 2>/dev/null || true
  done
}

# Function to start the application
start_app() {
  log "Starting application on port ${PORT}"
  
  # Ensure Podman machine is running
  ensure_podman_running
  
  # First clean up any existing resources to avoid conflicts
  clean_resources
  
  # Check if the requested port is in use
  if check_port_in_use "$PORT"; then
    log "WARNING: Port ${PORT} is already in use"
    
    # Try to find an available port
    AVAILABLE_PORT=$(find_available_port "$PORT")
    if [ -n "$AVAILABLE_PORT" ]; then
      log "Using available port: $AVAILABLE_PORT instead of $PORT"
      PORT=$AVAILABLE_PORT
    else
      log "ERROR: Failed to find an available port. Please try again with a different port."
      return 1
    fi
  fi
  
  # Build the container image
  log "Building container image"
  podman build -t localhost/"$APP_NAME":latest . 2>&1 | tee -a "$LOG_FILE"
  
  # Run container with port mapping
  log "Starting container with port mapping ${PORT}:8080"
  podman run -d --name "$APP_NAME" -p "${PORT}:8080" localhost/"$APP_NAME":latest 2>&1 | tee -a "$LOG_FILE"
  
  # Check if container is running
  if podman ps | grep -q "$APP_NAME"; then
    log "Container started successfully"
    
    # Test internal health check
    sleep 2
    log "Testing application health:"
    if podman exec "$APP_NAME" curl -s http://localhost:8080/health 2>/dev/null; then
      log "Health check passed"
    else
      log "Health check not responding yet (this may be normal during startup)"
    fi
    
    log "The application is running"
    log "To access the application, run: ./app_manager_v2.sh connect"
  else
    log "Container failed to start"
    log "Container logs:"
    podman logs "$APP_NAME" 2>&1 | tee -a "$LOG_FILE" || log "No logs available"
  fi
}

# Function to stop the application
stop_app() {
  log "Stopping application"
  
  # Check if container is running
  if podman ps | grep -q "$APP_NAME"; then
    log "Stopping container"
    podman stop "$APP_NAME" 2>&1 | tee -a "$LOG_FILE"
    log "Application stopped"
  else
    log "Application is not running"
  fi
}

# Function to view application logs
view_logs() {
  log "Viewing application logs"
  
  # Find the right container
  CONTAINER_ID=$(podman ps -a | grep "$APP_NAME" | awk '{print $1}' | head -1)
  
  if [ -n "$CONTAINER_ID" ]; then
    log "Container logs for $CONTAINER_ID:"
    podman logs "$CONTAINER_ID" --tail=50 2>&1 | tee -a "$LOG_FILE"
  else
    log "No container found for $APP_NAME"
  fi
}

# Function to connect to the application (port forwarding)
connect_app() {
  log "Setting up connection to the application"
  
  # Check if application is running
  if ! podman ps | grep -q "$APP_NAME"; then
    log "Application is not running. Start it first with: ./app_manager_v2.sh start"
    return 1
  fi
  
  # Get the port the container is using
  CONTAINER_ID=$(podman ps | grep "$APP_NAME" | awk '{print $1}' | head -1)
  HOST_PORT=$(podman inspect "$CONTAINER_ID" --format '{{range $p, $conf := .NetworkSettings.Ports}}{{(index $conf 0).HostPort}}{{end}}')
  
  if [ -z "$HOST_PORT" ]; then
    log "Cannot determine port mapping for container"
    HOST_PORT="$PORT"  # Fallback to the default port
  fi
  
  # Get Podman machine IP
  PODMAN_IP=$(podman machine inspect --format '{{.NetworkSettings.IPAddress}}' 2>/dev/null)
  
  if [ -n "$PODMAN_IP" ]; then
    log "Setting up SSH port forwarding from localhost:${HOST_PORT} to ${PODMAN_IP}:${HOST_PORT}"
    log "The application will be available at http://localhost:${HOST_PORT}"
    
    # Open browser in background
    (sleep 2; open "http://localhost:${HOST_PORT}") &
    
    # Start SSH port forwarding
    ssh -N -L "${HOST_PORT}:${PODMAN_IP}:${HOST_PORT}" "$(whoami)@localhost"
  else
    log "Cannot get Podman machine IP for port forwarding"
    log "Try accessing the application at http://localhost:${HOST_PORT} directly"
  fi
}

# Function to clean all resources
clean_all() {
  log "Cleaning all resources"
  
  # Clean existing resources
  clean_resources
  
  # Remove image
  log "Removing application image"
  podman rmi localhost/"$APP_NAME":latest 2>/dev/null || log "No image to remove"
  
  log "Cleaning completed"
}

# Print debug info if enabled
print_debug_info

# Execute the requested command
case $COMMAND in
  start)
    start_app
    ;;
  
  stop)
    stop_app
    ;;
  
  restart)
    log "Restarting application"
    stop_app
    sleep 2
    start_app
    ;;
  
  status)
    check_status
    ;;
  
  logs)
    view_logs
    ;;
  
  connect)
    connect_app
    ;;
  
  clean)
    clean_all
    ;;
  
  help)
    show_usage
    ;;
  
  *)
    echo "Unknown command: $COMMAND"
    show_usage
    exit 1
    ;;
esac

log "Command '$COMMAND' completed"
log "Log file saved to: $LOG_FILE"