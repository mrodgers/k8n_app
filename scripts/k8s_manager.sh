#!/bin/bash

# K8s Environment Manager for macOS with Podman
# This script helps set up, manage, and troubleshoot a local Kubernetes environment

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
K8S_VERSION="v1.27.1"
CONTAINER_RUNTIME="containerd"
MEMORY="3072"  # Reduced to 3GB for ARM Mac compatibility
CPUS="2"
DISK_SIZE="40"
DRIVER="podman"

# Set fallback driver based on architecture
if [[ $(uname -m) == "arm64" ]]; then
    # For ARM Macs, use docker driver as fallback
    FALLBACK_DRIVER="docker"
else
    # For Intel Macs, can use hyperkit
    FALLBACK_DRIVER="hyperkit"
fi

# Function to display help
show_help() {
    echo -e "${BLUE}Kubernetes Environment Manager for Research System${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  setup         Check for required tools and install missing dependencies"
    echo "  precheck      Run comprehensive pre-start checks without making changes"
    echo "  start         Start or reset the Kubernetes environment"
    echo "  deploy        Deploy the Research System to Kubernetes"
    echo "  status        Check status of the Kubernetes environment"
    echo "  logs          View logs from the Research System"
    echo "  stop          Stop the Kubernetes environment"
    echo "  clean         Clean up all resources"
    echo "  help          Show this help message"
    echo ""
    echo "Options:"
    echo "  --driver=<driver>            Kubernetes driver (podman, docker, hyperkit) (default: $DRIVER)"
    echo "  --memory=<MB>                Memory allocation in MB (default: $MEMORY)"
    echo "  --cpus=<count>               CPU count (default: $CPUS)"
    echo "  --k8s-version=<version>      Kubernetes version (default: $K8S_VERSION)"
    echo "  --container-runtime=<rt>     Container runtime (default: $CONTAINER_RUNTIME)"
    echo "  --skip-checks                Skip dependency checks"
    echo "  --force                      Force recreation of resources"
    echo ""
    echo "Examples:"
    echo "  $0 setup              # Check and install dependencies"
    echo "  $0 precheck           # Run comprehensive pre-start checks"
    echo "  $0 start              # Start Kubernetes with default settings"
    echo "  $0 start --driver=docker --memory=8192    # Start with custom settings"
    echo "  $0 deploy             # Deploy the Research System"
    echo "  $0 status             # Check status"
    echo "  $0 clean              # Clean up all resources"
    echo ""
    echo "Alternative Commands for Podman-only Testing (No Kubernetes):"
    echo "  podman-start          # Start containers using podman-compose"
    echo "  podman-stop           # Stop podman containers"
}

# Function to check required dependencies
check_dependencies() {
    echo -e "${BLUE}Checking for required dependencies...${NC}"
    local missing_deps=false
    
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}❌ Homebrew is not installed${NC}"
        echo -e "   Install with: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        missing_deps=true
    else
        echo -e "${GREEN}✓ Homebrew installed${NC}"
    fi
    
    # Check for Podman
    if ! command -v podman &> /dev/null; then
        echo -e "${RED}❌ Podman is not installed${NC}"
        echo -e "   Install with: brew install podman"
        missing_deps=true
    else
        echo -e "${GREEN}✓ Podman installed ($(podman version --format '{{.Client.Version}}'))${NC}"
        
        # Check if podman machine is running
        if ! podman machine list --format "{{.Name}} {{.Running}}" | grep -q "podman-machine-default.*Running"; then
            echo -e "${YELLOW}⚠️ Podman machine is not running${NC}"
            echo -e "   Starting podman machine..."
            podman machine start 2>/dev/null || podman machine init --now --cpus=$CPUS --memory=$MEMORY --disk-size=$DISK_SIZE
        else
            echo -e "${GREEN}✓ Podman machine is running${NC}"
        fi
    fi
    
    # Check for Minikube
    if ! command -v minikube &> /dev/null; then
        echo -e "${RED}❌ Minikube is not installed${NC}"
        echo -e "   Install with: brew install minikube"
        missing_deps=true
    else
        echo -e "${GREEN}✓ Minikube installed ($(minikube version --short))${NC}"
    fi
    
    # Check for kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed${NC}"
        echo -e "   Install with: brew install kubectl"
        missing_deps=true
    else
        KUBE_VERSION=$(kubectl version --client 2>/dev/null | grep "Client Version" || kubectl version --client | head -n 1)
        echo -e "${GREEN}✓ kubectl installed ($KUBE_VERSION)${NC}"
    fi
    
    # Check for GNU coreutils (for timeout command)
    if ! command -v gtimeout &> /dev/null; then
        echo -e "${YELLOW}⚠️ GNU coreutils not installed (needed for timeout command)${NC}"
        echo -e "   Install with: brew install coreutils"
        missing_deps=true
    else
        echo -e "${GREEN}✓ GNU coreutils installed${NC}"
    fi
    
    # Check for podman-compose
    if ! command -v podman-compose &> /dev/null; then
        echo -e "${YELLOW}⚠️ podman-compose is not installed${NC}"
        echo -e "   Install with: pip3 install podman-compose"
        echo -e "   This is optional but recommended for local development"
    else
        echo -e "${GREEN}✓ podman-compose installed${NC}"
    fi
    
    # Check if required tools are present for installing missing dependencies
    if [ "$missing_deps" = true ]; then
        if [[ "$1" == "--auto-install" ]]; then
            install_dependencies
        else
            echo -e "${YELLOW}Some dependencies are missing. Install them with:${NC}"
            echo -e "   $0 setup --auto-install"
            exit 1
        fi
    fi
}

# Function to install missing dependencies
install_dependencies() {
    echo -e "${BLUE}Installing missing dependencies...${NC}"
    
    # Install Homebrew if missing
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Podman if missing
    if ! command -v podman &> /dev/null; then
        echo -e "${YELLOW}Installing Podman...${NC}"
        brew install podman
    fi
    
    # Initialize Podman machine if needed
    if ! podman machine list | grep -q "podman-machine-default"; then
        echo -e "${YELLOW}Initializing Podman machine...${NC}"
        podman machine init --cpus=$CPUS --memory=$MEMORY --disk-size=$DISK_SIZE
        podman machine start
    elif ! podman machine list | grep -q "Running"; then
        echo -e "${YELLOW}Starting Podman machine...${NC}"
        podman machine start
    fi
    
    # Install Minikube if missing
    if ! command -v minikube &> /dev/null; then
        echo -e "${YELLOW}Installing Minikube...${NC}"
        brew install minikube
    fi
    
    # Install kubectl if missing
    if ! command -v kubectl &> /dev/null; then
        echo -e "${YELLOW}Installing kubectl...${NC}"
        brew install kubectl
    fi
    
    # Install podman-compose if missing
    if ! command -v podman-compose &> /dev/null; then
        echo -e "${YELLOW}Installing podman-compose...${NC}"
        pip3 install podman-compose
    fi
    
    echo -e "${GREEN}Dependencies installation completed.${NC}"
}

# Function to comprehensively check the environment before starting
pre_start_check() {
    echo -e "${BLUE}Running pre-start checks for Kubernetes environment...${NC}"
    
    # Check system requirements
    echo -e "\n${YELLOW}1. System Resources${NC}"
    echo -e "${BLUE}Checking available system resources...${NC}"
    
    # Get total memory
    if [[ $(uname) == "Darwin" ]]; then
        # For macOS
        TOTAL_MEM=$(sysctl -n hw.memsize 2>/dev/null | awk '{print int($1/1024/1024)}')
        FREE_MEM=$(vm_stat | grep "Pages free" | awk '{print int($3*4096/1024/1024)}')
        SYSTEM_LOAD=$(sysctl -n vm.loadavg | awk '{print $2}')
        CPU_COUNT=$(sysctl -n hw.ncpu)
        DISK_SPACE=$(df -h . | tail -1 | awk '{print $4}')
    else
        # For Linux
        TOTAL_MEM=$(free -m | grep -i mem | awk '{print $2}')
        FREE_MEM=$(free -m | grep -i mem | awk '{print $7}')
        SYSTEM_LOAD=$(uptime | awk -F'[a-z]:' '{print $2}' | awk '{print $1}')
        CPU_COUNT=$(nproc)
        DISK_SPACE=$(df -h . | tail -1 | awk '{print $4}')
    fi
    
    echo -e "Total Memory: ${GREEN}${TOTAL_MEM}MB${NC}"
    echo -e "Free Memory: ${GREEN}${FREE_MEM}MB${NC}"
    echo -e "CPU Cores: ${GREEN}${CPU_COUNT}${NC}"
    echo -e "System Load: ${GREEN}${SYSTEM_LOAD}${NC}"
    echo -e "Free Disk Space: ${GREEN}${DISK_SPACE}${NC}"
    
    # Check if we have enough memory for requested allocation
    if [[ $FREE_MEM -lt $MEMORY ]]; then
        echo -e "${RED}⚠️ WARNING: Requested memory (${MEMORY}MB) exceeds available free memory (${FREE_MEM}MB)${NC}"
        echo -e "${YELLOW}This may cause system instability. Consider reducing memory allocation with --memory flag.${NC}"
    fi
    
    # Check dependency executables
    echo -e "\n${YELLOW}2. Required Software${NC}"
    MISSING_DEPS=false
    
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}❌ Homebrew is not installed${NC}"
        MISSING_DEPS=true
    else
        BREW_VERSION=$(brew --version | head -1)
        echo -e "${GREEN}✓ $BREW_VERSION${NC}"
    fi
    
    # Check for Podman
    if ! command -v podman &> /dev/null; then
        echo -e "${RED}❌ Podman is not installed${NC}"
        MISSING_DEPS=true
    else
        PODMAN_VERSION=$(podman version --format '{{.Client.Version}}')
        echo -e "${GREEN}✓ Podman $PODMAN_VERSION${NC}"
    fi
    
    # Check for Minikube
    if ! command -v minikube &> /dev/null; then
        echo -e "${RED}❌ Minikube is not installed${NC}"
        MISSING_DEPS=true
    else
        MINIKUBE_VERSION=$(minikube version --short)
        echo -e "${GREEN}✓ $MINIKUBE_VERSION${NC}"
    fi
    
    # Check for kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed${NC}"
        MISSING_DEPS=true
    else
        KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null || kubectl version --client -o json | grep gitVersion | head -1)
        echo -e "${GREEN}✓ kubectl $KUBECTL_VERSION${NC}"
    fi
    
    # Check podman VM status
    echo -e "\n${YELLOW}3. Podman VM Status${NC}"
    if command -v podman &> /dev/null; then
        PODMAN_VMS=$(podman machine list 2>/dev/null || echo "No machines found")
        echo -e "${BLUE}Podman machine list:${NC}"
        echo "$PODMAN_VMS"
        
        # Check if default podman machine exists
        if podman machine list 2>/dev/null | grep -q "podman-machine-default"; then
            # Check if it's running and accessible
            if podman machine info &>/dev/null; then
                echo -e "${GREEN}✓ Podman default machine is running${NC}"
                
                # Get podman machine details
                echo -e "${BLUE}Podman machine details:${NC}"
                podman machine inspect podman-machine-default 2>/dev/null | grep -E 'CPUs|Memory|DiskSize' || echo "Cannot get machine details"
                
                # Get actual memory available from VM - ensure we get a valid number
                PODMAN_MEM=$(podman machine inspect podman-machine-default | grep -E '"Memory":|"MemoryMiB":' | head -1 | awk '{print $2}' | tr -d ',' || echo 0)
                if [[ -z "$PODMAN_MEM" || "$PODMAN_MEM" == "null" ]]; then
                    PODMAN_MEM=0
                fi
                
                # Only subtract overhead if we have a valid memory value
                if [[ $PODMAN_MEM -gt 0 ]]; then
                    PODMAN_AVAIL_MEM=$((PODMAN_MEM - 200)) # Reserve 200MB for VM overhead
                else
                    PODMAN_AVAIL_MEM=0
                fi
                
                echo -e "Podman VM memory: ${GREEN}${PODMAN_MEM}MB${NC}"
                echo -e "Available for Minikube: ${GREEN}${PODMAN_AVAIL_MEM}MB${NC}"
                
                if [[ $PODMAN_AVAIL_MEM -lt $MEMORY ]]; then
                    echo -e "${YELLOW}⚠️ WARNING: Requested memory for Minikube (${MEMORY}MB) exceeds available Podman VM memory (${PODMAN_AVAIL_MEM}MB)${NC}"
                    echo -e "${YELLOW}The startup script will automatically adjust memory allocation.${NC}"
                fi
                
                # Check podman connectivity
                if podman info &>/dev/null; then
                    echo -e "${GREEN}✓ Podman is properly connected to VM${NC}"
                else
                    echo -e "${RED}❌ Podman cannot connect to VM${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️ Podman default machine exists but is not running correctly${NC}"
                PODMAN_VM_RUNNING=false
            fi
        else
            echo -e "${YELLOW}⚠️ No default podman machine exists${NC}"
            PODMAN_VM_RUNNING=false
        fi
    else
        echo -e "${RED}Cannot check podman VM status - podman not installed${NC}"
    fi
    
    # Check minikube status
    echo -e "\n${YELLOW}4. Minikube Status${NC}"
    if command -v minikube &> /dev/null; then
        if minikube status &>/dev/null; then
            echo -e "${GREEN}✓ Minikube is running${NC}"
            minikube status
            
            # Get minikube configuration
            echo -e "\n${BLUE}Minikube configuration:${NC}"
            minikube config view
            
            # Check minikube profile
            echo -e "\n${BLUE}Minikube profile:${NC}"
            minikube profile list
            
            # Check driver being used
            CURRENT_DRIVER=$(minikube profile list | grep -v DRIVER | awk '{print $3}')
            echo -e "Current driver: ${GREEN}${CURRENT_DRIVER}${NC}"
            
            # Check addons
            echo -e "\n${BLUE}Minikube addons:${NC}"
            minikube addons list | grep enabled
        else
            echo -e "${YELLOW}⚠️ Minikube is not running${NC}"
        fi
    else
        echo -e "${RED}Cannot check minikube status - minikube not installed${NC}"
    fi
    
    # Check Kubernetes cluster resources
    echo -e "\n${YELLOW}5. Kubernetes Resources${NC}"
    if command -v kubectl &> /dev/null && kubectl cluster-info &>/dev/null; then
        echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
        kubectl cluster-info
        
        # Check nodes
        echo -e "\n${BLUE}Kubernetes nodes:${NC}"
        kubectl get nodes
        
        # Check node resources
        echo -e "\n${BLUE}Node resource usage:${NC}"
        kubectl top nodes 2>/dev/null || echo "Metrics server not available"
        
        # Check namespaces
        echo -e "\n${BLUE}Kubernetes namespaces:${NC}"
        kubectl get namespaces
        
        # Check persistent volumes
        echo -e "\n${BLUE}Persistent volumes:${NC}"
        kubectl get pv 2>/dev/null || echo "No persistent volumes found"
        
        # Check for required Secret
        echo -e "\n${BLUE}Checking for required secrets:${NC}"
        if kubectl get secret research-system-db-credentials &>/dev/null; then
            echo -e "${GREEN}✓ Database credentials secret exists${NC}"
        else
            echo -e "${YELLOW}⚠️ Database credentials secret doesn't exist - will be created during deployment${NC}"
        fi
        
        # Check for ConfigMap
        echo -e "\n${BLUE}Checking for required configmaps:${NC}"
        if kubectl get configmap research-system-config &>/dev/null; then
            echo -e "${GREEN}✓ Research system ConfigMap exists${NC}"
        else
            echo -e "${YELLOW}⚠️ Research system ConfigMap doesn't exist - will be created during deployment${NC}"
        fi
        
        # Check for Research System deployment
        echo -e "\n${BLUE}Checking for existing deployment:${NC}"
        if kubectl get deployment research-system &>/dev/null; then
            echo -e "${GREEN}✓ Research system deployment exists${NC}"
            
            # Check deployment status
            DEPLOYMENT_STATUS=$(kubectl get deployment research-system -o jsonpath="{.status.conditions[?(@.type=='Available')].status}")
            if [[ "$DEPLOYMENT_STATUS" == "True" ]]; then
                echo -e "${GREEN}✓ Research system deployment is available${NC}"
                
                # Check replicas
                DESIRED=$(kubectl get deployment research-system -o jsonpath="{.spec.replicas}")
                AVAILABLE=$(kubectl get deployment research-system -o jsonpath="{.status.availableReplicas}")
                echo -e "Replicas: ${GREEN}${AVAILABLE}/${DESIRED} available${NC}"
                
                # Check pod status
                echo -e "\n${BLUE}Pod status:${NC}"
                kubectl get pods -l app=research-system
            else
                echo -e "${RED}❌ Research system deployment is not available${NC}"
                DEPLOYMENT_MESSAGE=$(kubectl get deployment research-system -o jsonpath="{.status.conditions[?(@.type=='Available')].message}")
                echo -e "Reason: ${RED}${DEPLOYMENT_MESSAGE}${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ Research system deployment doesn't exist - will be created during deployment${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ Not connected to any Kubernetes cluster${NC}"
    fi
    
    # Check health endpoints if the service is running
    echo -e "\n${YELLOW}6. Application Health${NC}"
    if command -v kubectl &> /dev/null && kubectl get service research-system &>/dev/null; then
        echo -e "${GREEN}✓ Research system service exists${NC}"
        
        # Check if we can connect to the service
        echo -e "${BLUE}Testing connection to service...${NC}"
        HEALTH_CHECK_PORT=8181
        
        # Try to set up port forwarding temporarily to check health
        (kubectl port-forward svc/research-system ${HEALTH_CHECK_PORT}:80 &>/dev/null &)
        FORWARD_PID=$!
        
        # Give port forwarding time to set up
        sleep 3
        
        # Check health endpoint
        if curl -s http://localhost:${HEALTH_CHECK_PORT}/health &>/dev/null; then
            HEALTH_RESPONSE=$(curl -s http://localhost:${HEALTH_CHECK_PORT}/health)
            echo -e "${GREEN}✓ Health endpoint is accessible${NC}"
            echo -e "Response: ${HEALTH_RESPONSE}"
        else
            echo -e "${RED}❌ Cannot access health endpoint${NC}"
        fi
        
        # Clean up port forwarding
        kill -9 $FORWARD_PID 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️ Research system service doesn't exist - will be created during deployment${NC}"
    fi
    
    # Final assessment
    echo -e "\n${YELLOW}Pre-start Check Summary${NC}"
    
    if [ "$MISSING_DEPS" = true ]; then
        echo -e "${RED}❌ Some dependencies are missing. Run '$0 setup --auto-install' to install them.${NC}"
    fi
    
    if ! command -v podman &> /dev/null || ! podman machine info &>/dev/null; then
        echo -e "${YELLOW}⚠️ Podman VM is not running. It will be started during bootstrap.${NC}"
    else
        echo -e "${GREEN}✓ Podman VM is running.${NC}"
    fi
    
    if ! command -v minikube &> /dev/null || ! minikube status &>/dev/null; then
        echo -e "${YELLOW}⚠️ Minikube is not running. It will be started during bootstrap.${NC}"
    else
        echo -e "${GREEN}✓ Minikube is running.${NC}"
    fi
    
    echo -e "\n${BLUE}To continue with starting the environment:${NC}"
    echo -e "  $0 start"
    echo -e ""
}

# Function to start or reset Kubernetes environment
start_kubernetes() {
    echo -e "${BLUE}Starting Kubernetes environment...${NC}"
    
    # Initialize failure flag
    MINIKUBE_START_FAILED=false
    
    # Check dependencies unless skipped
    if [[ "$SKIP_CHECKS" != "true" ]]; then
        check_dependencies
    fi
    
    # Check if minikube is already running
    if minikube status &>/dev/null; then
        if [[ "$FORCE" == "true" ]]; then
            echo -e "${YELLOW}Stopping and deleting existing minikube cluster...${NC}"
            minikube stop
            minikube delete
        else
            echo -e "${YELLOW}Minikube is already running. Use --force to recreate it.${NC}"
            return 0
        fi
    fi
    
    # Make sure podman machine is running
    if [[ "$DRIVER" == "podman" ]]; then
        if ! podman machine info &>/dev/null; then
            echo -e "${YELLOW}Starting podman machine...${NC}"
            podman machine start || { 
                echo -e "${RED}Failed to start podman machine.${NC}"
                echo -e "${YELLOW}Attempting to recreate podman machine...${NC}"
                podman machine stop 2>/dev/null || true
                podman machine rm 2>/dev/null || true
                podman machine init --cpus=$CPUS --memory=$MEMORY --disk-size=$DISK_SIZE
                podman machine start || {
                    echo -e "${RED}Failed to create and start podman machine. Aborting.${NC}"
                    exit 1
                }
            }
        fi
        
        # Check actual available memory in Podman VM and adjust if needed
        if podman machine info &>/dev/null; then
            echo -e "${YELLOW}Checking Podman VM memory...${NC}"
            # Get actual memory available from VM - ensure we get a valid number
            PODMAN_MEM=$(podman machine inspect podman-machine-default | grep -E '"Memory":|"MemoryMiB":' | head -1 | awk '{print $2}' | tr -d ',' || echo 0)
            if [[ -z "$PODMAN_MEM" || "$PODMAN_MEM" == "null" ]]; then
                PODMAN_MEM=0
            fi
            
            # Only subtract overhead if we have a valid memory value
            if [[ $PODMAN_MEM -gt 0 ]]; then
                PODMAN_AVAIL_MEM=$((PODMAN_MEM - 200)) # Reserve 200MB for VM overhead
            else
                PODMAN_AVAIL_MEM=0
            fi
            
            echo -e "Podman VM memory: ${GREEN}${PODMAN_MEM}MB${NC}"
            echo -e "Available for Minikube: ${GREEN}${PODMAN_AVAIL_MEM}MB${NC}"
            
            if [[ $PODMAN_AVAIL_MEM -lt $MEMORY ]]; then
                echo -e "${YELLOW}Adjusting Minikube memory from ${MEMORY}MB to ${PODMAN_AVAIL_MEM}MB to fit in Podman VM${NC}"
                MEMORY=$PODMAN_AVAIL_MEM
            fi
        fi
    fi
    
    # Start minikube with the specified driver
    echo -e "${YELLOW}Starting minikube with driver: $DRIVER${NC}"
    
    # Construct the minikube start command with all options
    # Ensure memory is a positive value
    if [[ $MEMORY -le 0 ]]; then
        echo -e "${YELLOW}Detected invalid memory value (${MEMORY}MB), setting to minimum 1024MB${NC}"
        MEMORY=1024
    fi
    
    START_CMD="minikube start --driver=$DRIVER --kubernetes-version=$K8S_VERSION --container-runtime=$CONTAINER_RUNTIME --memory=$MEMORY --cpus=$CPUS"
    
    # Add extra configs for podman driver
    if [[ "$DRIVER" == "podman" ]]; then
        START_CMD="$START_CMD --extra-config=kubelet.cgroup-driver=systemd"
    fi
    
    # Echo the command being run
    echo -e "${YELLOW}Running: ${START_CMD}${NC}"
    
    # Try to start minikube with a timeout (using gtimeout if available)
    if command -v gtimeout &> /dev/null; then
        if ! gtimeout 300s bash -c "$START_CMD"; then
            echo -e "${RED}Failed to start minikube with timeout.${NC}"
            MINIKUBE_START_FAILED=true
        fi
    else
        # No timeout available, just run the command
        if ! eval "$START_CMD"; then
            echo -e "${RED}Failed to start minikube.${NC}"
            MINIKUBE_START_FAILED=true
        fi
    fi
    
    # Handle minikube start failure
    if [[ "$MINIKUBE_START_FAILED" == "true" ]]; then
        # Try alternative approach if podman driver fails
        if [[ "$DRIVER" == "podman" ]]; then
            echo -e "${YELLOW}Trying alternative approach with podman driver...${NC}"
            minikube delete 2>/dev/null || true
            
            # Try with a different container runtime
            echo -e "${YELLOW}Attempting to start with cri-o runtime...${NC}"
            if ! minikube start --driver=podman --container-runtime=cri-o --memory=$MEMORY --cpus=$CPUS; then
                echo -e "${RED}Alternative podman approach failed.${NC}"
                
                # Suggest alternative driver as a fallback
                echo -e "${YELLOW}Would you like to try with $FALLBACK_DRIVER driver instead? (y/n)${NC}"
                read -r response
                if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                    if [[ "$FALLBACK_DRIVER" == "hyperkit" ]]; then
                        echo -e "${YELLOW}Installing hyperkit...${NC}"
                        brew install hyperkit
                    elif [[ "$FALLBACK_DRIVER" == "docker" ]]; then
                        echo -e "${YELLOW}Using Docker driver (requires Docker Desktop to be running)...${NC}"
                    fi
                    
                    echo -e "${YELLOW}Starting minikube with $FALLBACK_DRIVER driver...${NC}"
                    if ! minikube start --driver=$FALLBACK_DRIVER --memory=$MEMORY --cpus=$CPUS; then
                        echo -e "${RED}Failed to start minikube with $FALLBACK_DRIVER driver.${NC}"
                        echo -e "${YELLOW}Falling back to podman-only mode (without Kubernetes)${NC}"
                        exit 1
                    fi
                else
                    echo -e "${YELLOW}Falling back to podman-only mode (without Kubernetes)${NC}"
                    exit 1
                fi
            fi
        else
            exit 1
        fi
    fi
    
    # Verify minikube started successfully
    if ! minikube status &>/dev/null; then
        echo -e "${RED}Failed to start minikube.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Kubernetes environment started successfully.${NC}"
    echo -e "${BLUE}Kubernetes version: $(kubectl version --short | grep Server)${NC}"
    
    # Set kubectl context to minikube
    kubectl config use-context minikube
    
    # Wait for core services to be ready
    echo -e "${YELLOW}Waiting for Kubernetes services to be ready...${NC}"
    kubectl wait --for=condition=ready --timeout=120s -n kube-system deployment/coredns || {
        echo -e "${RED}Timeout waiting for core Kubernetes services.${NC}"
        echo -e "${YELLOW}The cluster may still be initializing. Check status with: minikube status${NC}"
    }
    
    echo -e "${GREEN}Kubernetes is ready.${NC}"
}

# Enhanced version of check_status
check_status() {
    echo -e "${BLUE}Checking Kubernetes environment status...${NC}"
    
    # Check system load
    echo -e "\n${YELLOW}System Status${NC}"
    if [[ $(uname) == "Darwin" ]]; then
        # For macOS
        SYSTEM_LOAD=$(sysctl -n vm.loadavg | awk '{print $2}')
        CPU_COUNT=$(sysctl -n hw.ncpu)
        echo -e "CPU Load: ${GREEN}${SYSTEM_LOAD} (${CPU_COUNT} cores)${NC}"
    else
        # For Linux
        SYSTEM_LOAD=$(uptime | awk -F'[a-z]:' '{print $2}' | awk '{print $1}')
        CPU_COUNT=$(nproc)
        echo -e "CPU Load: ${GREEN}${SYSTEM_LOAD} (${CPU_COUNT} cores)${NC}"
    fi
    
    # Check disk space
    DISK_USAGE=$(df -h . | tail -1)
    echo -e "Disk Usage: ${GREEN}$(echo "$DISK_USAGE" | awk '{print $5}') (${DISK_USAGE})${NC}"
    
    # Check podman machine status with more details
    echo -e "\n${YELLOW}Podman Status${NC}"
    if command -v podman &> /dev/null; then
        echo -e "Podman Version: ${GREEN}$(podman --version)${NC}"
        
        echo -e "\nPodman Machines:"
        podman machine list
        
        if podman machine list --format "{{.Name}} {{.Running}}" | grep -q "podman-machine-default.*Running"; then
            echo -e "\n${GREEN}✓ Podman machine resources:${NC}"
            podman machine inspect podman-machine-default 2>/dev/null | grep -E 'CPUs|Memory|DiskSize' || echo "Cannot get machine details"
            
            echo -e "\n${BLUE}Podman Images:${NC}"
            podman images | grep -E 'research-system|postgres'
            
            echo -e "\n${BLUE}Podman Networks:${NC}"
            podman network ls
        else
            echo -e "${RED}❌ Podman machine is not running${NC}"
        fi
    else
        echo -e "${RED}Podman is not installed.${NC}"
    fi
    
    # Enhanced minikube status
    echo -e "\n${YELLOW}Minikube Status${NC}"
    if command -v minikube &> /dev/null; then
        if minikube status &>/dev/null; then
            echo -e "${GREEN}✓ Minikube is running${NC}"
            minikube status
            
            echo -e "\n${BLUE}Minikube IP Address:${NC} $(minikube ip 2>/dev/null || echo "Unknown")"
            echo -e "${BLUE}Driver:${NC} $(minikube config get driver 2>/dev/null || echo "Unknown")"
            echo -e "${BLUE}Container Runtime:${NC} $(minikube config get container-runtime 2>/dev/null || echo "Unknown")"
            
            echo -e "\n${BLUE}Minikube Resources:${NC}"
            minikube ssh "free -h" 2>/dev/null || echo "Cannot access minikube VM"
            
            echo -e "\n${BLUE}Enabled Addons:${NC}"
            minikube addons list | grep enabled
        else
            echo -e "${RED}❌ Minikube is not running.${NC}"
        fi
    else
        echo -e "${RED}Minikube is not installed.${NC}"
    fi
    
    # Enhanced kubectl connection check
    echo -e "\n${YELLOW}Kubernetes Cluster Status${NC}"
    if command -v kubectl &> /dev/null; then
        if kubectl cluster-info &>/dev/null; then
            echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
            kubectl cluster-info
            
            echo -e "\n${BLUE}Kubernetes Version:${NC}"
            kubectl version --short
            
            echo -e "\n${BLUE}Nodes:${NC}"
            kubectl get nodes -o wide
            
            echo -e "\n${BLUE}Namespaces:${NC}"
            kubectl get namespaces
            
            # Get pod counts by namespace
            echo -e "\n${BLUE}Pod Counts by Namespace:${NC}"
            for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
                POD_COUNT=$(kubectl get pods -n $ns --no-headers 2>/dev/null | wc -l | tr -d ' ')
                echo -e "$ns: ${GREEN}$POD_COUNT pods${NC}"
            done
            
            # Check persistent volumes and claims
            echo -e "\n${BLUE}Persistent Volumes:${NC}"
            kubectl get pv 2>/dev/null || echo "No persistent volumes found"
            
            echo -e "\n${BLUE}Persistent Volume Claims:${NC}"
            kubectl get pvc --all-namespaces 2>/dev/null || echo "No persistent volume claims found"
            
            # Check pods in default namespace with more details
            echo -e "\n${BLUE}Pods in default namespace:${NC}"
            kubectl get pods -o wide
            
            # Check services with endpoints
            echo -e "\n${BLUE}Services:${NC}"
            kubectl get services -o wide
            
            # Check for our application resources with detailed info
            echo -e "\n${BLUE}Research System Resources:${NC}"
            
            if kubectl get deployment research-system &>/dev/null; then
                echo -e "\n${GREEN}✓ Research System Deployment Details:${NC}"
                kubectl get deployment research-system -o wide
                
                # Get replica status
                DESIRED=$(kubectl get deployment research-system -o jsonpath="{.spec.replicas}")
                AVAILABLE=$(kubectl get deployment research-system -o jsonpath="{.status.availableReplicas}")
                echo -e "Replicas: ${GREEN}${AVAILABLE}/${DESIRED} available${NC}"
                
                # Get deployment conditions
                echo -e "\nDeployment Conditions:"
                kubectl get deployment research-system -o jsonpath="{.status.conditions}" | jq 2>/dev/null || echo "Cannot parse deployment conditions - jq not installed"
                
                # Get pods with detailed status
                echo -e "\nPods Details:"
                kubectl get pods -l app=research-system -o wide
                
                # Check readiness of pods
                READY_PODS=$(kubectl get pods -l app=research-system -o jsonpath="{.items[*].status.containerStatuses[*].ready}" | tr ' ' '\n' | grep -c true)
                TOTAL_PODS=$(kubectl get pods -l app=research-system --no-headers | wc -l | tr -d ' ')
                echo -e "Ready Pods: ${GREEN}${READY_PODS}/${TOTAL_PODS}${NC}"
                
                # Check resource usage
                echo -e "\nResource Usage:"
                kubectl top pods -l app=research-system 2>/dev/null || echo "Metrics server not available"
                
                # Check logs for any errors (last 5 lines)
                echo -e "\nRecent Pod Logs (last 5 lines):"
                POD_NAME=$(kubectl get pods -l app=research-system -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
                if [ -n "$POD_NAME" ]; then
                    kubectl logs $POD_NAME --tail=5
                else
                    echo "No pods found"
                fi
                
                # Check service status
                echo -e "\nService Status:"
                kubectl get service research-system -o wide 2>/dev/null || echo "Service not found"
                
                # Check endpoints
                echo -e "\nEndpoints:"
                kubectl get endpoints research-system 2>/dev/null || echo "No endpoints found"
                
                # Check if service is accessible
                echo -e "\n${BLUE}Service Accessibility:${NC}"
                echo -e "To access the service, run: kubectl port-forward svc/research-system 8181:80"
                
                # Get application version from deployment labels
                APP_VERSION=$(kubectl get deployment research-system -o jsonpath="{.metadata.labels.app\.kubernetes\.io/version}" 2>/dev/null)
                if [ -n "$APP_VERSION" ]; then
                    echo -e "\nDeployed Version: ${GREEN}${APP_VERSION}${NC}"
                fi
            else
                echo -e "${YELLOW}Research System deployment not found${NC}"
            fi
            
            # Check for PostgreSQL if it's part of our setup
            if kubectl get deployment postgres &>/dev/null; then
                echo -e "\n${GREEN}✓ PostgreSQL Deployment:${NC}"
                kubectl get deployment postgres -o wide
                kubectl get pods -l app=postgres -o wide
                
                echo -e "\nPostgreSQL Service:"
                kubectl get service postgres 2>/dev/null || echo "PostgreSQL service not found"
            fi
        else
            echo -e "${RED}Cannot connect to Kubernetes cluster.${NC}"
        fi
    else
        echo -e "${RED}kubectl is not installed.${NC}"
    fi
    
    # Check for running podman containers (alternative mode)
    echo -e "\n${YELLOW}Podman Containers${NC}"
    if command -v podman &> /dev/null; then
        CONTAINER_COUNT=$(podman ps -q | wc -l | tr -d ' ')
        echo -e "Running containers: ${GREEN}${CONTAINER_COUNT}${NC}"
        
        if [ "$CONTAINER_COUNT" -gt 0 ]; then
            echo -e "\n${BLUE}Container Details:${NC}"
            podman ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
            
            # Check for research-system container
            if podman ps | grep -q research-system; then
                echo -e "\n${GREEN}✓ Research System container is running${NC}"
                
                # Get container stats
                echo -e "\nContainer Stats:"
                podman stats --no-stream research-system 2>/dev/null || echo "Cannot get container stats"
            fi
        else
            echo -e "${YELLOW}No running containers found${NC}"
        fi
    else
        echo -e "${RED}Podman is not installed${NC}"
    fi
    
    # Show how to access the application
    echo -e "\n${BLUE}Application Access:${NC}"
    if kubectl get service research-system &>/dev/null; then
        echo -e "To access via Kubernetes port-forward:"
        echo -e "  kubectl port-forward svc/research-system 8181:80"
        echo -e "  Then visit: http://localhost:8181"
    elif podman ps | grep -q research-system; then
        echo -e "To access via Podman container:"
        CONTAINER_PORT=$(podman ps | grep research-system | grep -o -E '0.0.0.0:[0-9]+->8181/tcp' | cut -d':' -f2 | cut -d'-' -f1)
        if [ -n "$CONTAINER_PORT" ]; then
            echo -e "  Visit: http://localhost:${CONTAINER_PORT}"
        else
            echo -e "  Container ports not exposed or mapped"
        fi
    else
        echo -e "${YELLOW}Application is not running${NC}"
    fi
}

# Function to deploy Research System to Kubernetes
deploy_to_kubernetes() {
    echo -e "${BLUE}Deploying Research System to Kubernetes...${NC}"
    
    # Check if minikube is running
    if ! minikube status &>/dev/null; then
        echo -e "${RED}Minikube is not running. Start it first with: $0 start${NC}"
        exit 1
    fi
    
    # Build the Docker image
    echo -e "${YELLOW}Building Research System image...${NC}"
    podman build -t research-system:latest . || {
        echo -e "${RED}Failed to build the Docker image.${NC}"
        exit 1
    }
    
    # Load the image into minikube
    echo -e "${YELLOW}Loading image into minikube...${NC}"
    minikube image load research-system:latest || {
        echo -e "${RED}Failed to load the image into minikube.${NC}"
        echo -e "${YELLOW}Trying alternative approach...${NC}"
        
        # If using podman driver, try this alternative
        if [[ "$DRIVER" == "podman" ]]; then
            echo -e "${YELLOW}Checking if image is already available in minikube...${NC}"
            if minikube ssh "podman images | grep research-system" &>/dev/null; then
                echo -e "${GREEN}Image already available in minikube.${NC}"
            else
                echo -e "${RED}Cannot load image into minikube. Deployment may fail.${NC}"
            fi
        fi
    }
    
    # Apply Kubernetes resources in proper order
    echo -e "${YELLOW}Applying Kubernetes resources...${NC}"
    
    # Create namespace if it doesn't exist
    kubectl create namespace research-system 2>/dev/null || true
    
    # Apply Secret first (create a dummy one if it doesn't exist)
    if [ -f "kubernetes/secrets.yaml" ]; then
        echo -e "${YELLOW}Applying secrets...${NC}"
        kubectl apply -f kubernetes/secrets.yaml || {
            echo -e "${RED}Failed to apply secrets.${NC}"
            exit 1
        }
    else
        echo -e "${YELLOW}secrets.yaml not found, creating a dummy secret...${NC}"
        kubectl create secret generic research-system-db-credentials \
            --from-literal=DB_POSTGRES_PASSWORD=postgres-password \
            --namespace research-system || true
    fi
    
    # Apply ConfigMap
    if [ -f "kubernetes/configmaps.yaml" ]; then
        echo -e "${YELLOW}Applying ConfigMap...${NC}"
        kubectl apply -f kubernetes/configmaps.yaml || {
            echo -e "${RED}Failed to apply ConfigMap.${NC}"
            exit 1
        }
    fi
    
    # Apply PostgreSQL deployment
    if [ -f "kubernetes/postgres.yaml" ]; then
        echo -e "${YELLOW}Deploying PostgreSQL...${NC}"
        kubectl apply -f kubernetes/postgres.yaml || {
            echo -e "${RED}Failed to deploy PostgreSQL.${NC}"
            exit 1
        }
        
        # Wait for PostgreSQL to be ready
        echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s || {
            echo -e "${RED}Timeout waiting for PostgreSQL.${NC}"
        }
    fi
    
    # Apply the application deployment
    if [ -f "kubernetes/deployment.yaml" ]; then
        echo -e "${YELLOW}Deploying Research System...${NC}"
        kubectl apply -f kubernetes/deployment.yaml || {
            echo -e "${RED}Failed to deploy Research System.${NC}"
            exit 1
        }
    fi
    
    # Apply the service
    if [ -f "kubernetes/service.yaml" ]; then
        echo -e "${YELLOW}Creating service...${NC}"
        kubectl apply -f kubernetes/service.yaml || {
            echo -e "${RED}Failed to create service.${NC}"
            exit 1
        }
    fi
    
    # Wait for deployment to be ready
    echo -e "${YELLOW}Waiting for Research System deployment to be ready...${NC}"
    kubectl wait --for=condition=available deployment/research-system --timeout=120s || {
        echo -e "${RED}Timeout waiting for deployment.${NC}"
        echo -e "${YELLOW}Checking deployment status...${NC}"
        kubectl get pods
        kubectl describe deployment research-system
    }
    
    # Set up port forwarding if service is available
    if kubectl get service research-system &>/dev/null; then
        echo -e "${GREEN}Setting up port forwarding to access the service...${NC}"
        echo -e "${YELLOW}Run this command in a separate terminal to access the service:${NC}"
        echo -e "${BLUE}kubectl port-forward svc/research-system 8181:80${NC}"
        echo -e "${YELLOW}Then access the application at: http://localhost:8181${NC}"
    fi
    
    echo -e "${GREEN}Deployment completed.${NC}"
}

# Function to view logs
view_logs() {
    echo -e "${BLUE}Fetching logs for Research System...${NC}"
    
    # Check if minikube is running
    if ! minikube status &>/dev/null; then
        echo -e "${YELLOW}Minikube is not running, checking podman containers...${NC}"
        
        # Check for podman containers
        if podman ps -a | grep -q research-system; then
            echo -e "${YELLOW}Found Research System container in podman, showing logs:${NC}"
            podman logs -f research-system
            return
        else
            echo -e "${RED}No Research System container found running in podman.${NC}"
            exit 1
        fi
    fi
    
    # Get pod name for research-system
    POD_NAME=$(kubectl get pods -l app=research-system -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    
    if [ -n "$POD_NAME" ]; then
        echo -e "${YELLOW}Showing logs for pod: $POD_NAME${NC}"
        kubectl logs -f "$POD_NAME"
    else
        echo -e "${RED}No Research System pods found.${NC}"
        echo -e "${YELLOW}Available pods:${NC}"
        kubectl get pods --all-namespaces
        exit 1
    fi
}

# Function to stop the Kubernetes environment
stop_kubernetes() {
    echo -e "${BLUE}Stopping Kubernetes environment...${NC}"
    
    if minikube status &>/dev/null; then
        echo -e "${YELLOW}Stopping minikube...${NC}"
        minikube stop || {
            echo -e "${RED}Failed to stop minikube properly.${NC}"
            echo -e "${YELLOW}Attempting to force stop...${NC}"
            minikube delete
        }
    else
        echo -e "${YELLOW}Minikube is not running.${NC}"
    fi
    
    echo -e "${GREEN}Kubernetes environment stopped.${NC}"
}

# Function to clean up all resources
clean_all() {
    echo -e "${BLUE}Cleaning up all resources...${NC}"
    
    # Stop and delete minikube
    if command -v minikube &> /dev/null; then
        echo -e "${YELLOW}Deleting minikube cluster...${NC}"
        minikube delete || echo -e "${RED}Failed to delete minikube cluster.${NC}"
    fi
    
    # Clean up podman containers
    if command -v podman &> /dev/null; then
        # Get list of container IDs
        CONTAINERS=$(podman ps -aq)
        
        if [ -n "$CONTAINERS" ]; then
            echo -e "${YELLOW}Stopping all podman containers...${NC}"
            podman stop $CONTAINERS 2>/dev/null || echo -e "${YELLOW}Failed to stop some containers.${NC}"
            
            echo -e "${YELLOW}Removing all podman containers...${NC}"
            podman rm $CONTAINERS 2>/dev/null || echo -e "${YELLOW}Failed to remove some containers.${NC}"
        else
            echo -e "${YELLOW}No containers to stop or remove.${NC}"
        fi
        
        echo -e "${YELLOW}Removing Research System images...${NC}"
        podman rmi research-system:latest 2>/dev/null || echo -e "${YELLOW}No Research System image to remove.${NC}"
    fi
    
    echo -e "${GREEN}Cleanup completed.${NC}"
}

# Function to start podman-compose (alternative to Kubernetes)
start_podman_compose() {
    echo -e "${BLUE}Starting application with podman-compose...${NC}"
    
    if ! command -v podman-compose &> /dev/null; then
        echo -e "${RED}podman-compose is not installed.${NC}"
        echo -e "${YELLOW}Installing podman-compose...${NC}"
        pip3 install podman-compose || {
            echo -e "${RED}Failed to install podman-compose.${NC}"
            exit 1
        }
    fi
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}docker-compose.yml not found.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Starting containers with podman-compose...${NC}"
    podman-compose up -d || {
        echo -e "${RED}Failed to start containers with podman-compose.${NC}"
        
        echo -e "${YELLOW}Attempting to start containers individually...${NC}"
        
        # Start PostgreSQL container
        echo -e "${YELLOW}Starting PostgreSQL container...${NC}"
        podman run -d --name research-postgres \
            -e POSTGRES_DB=research \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=postgres-password \
            -p 5432:5432 \
            postgres:16 || {
            echo -e "${RED}Failed to start PostgreSQL container.${NC}"
            exit 1
        }
        
        # Build and start the Research System container
        echo -e "${YELLOW}Building and starting Research System container...${NC}"
        podman build -t research-system:latest . || {
            echo -e "${RED}Failed to build Research System image.${NC}"
            exit 1
        }
        
        podman run -d --name research-system \
            -e DB_USE_POSTGRES=true \
            -e DB_POSTGRES_HOST=host.containers.internal \
            -e DB_POSTGRES_PORT=5432 \
            -e DB_POSTGRES_DBNAME=research \
            -e DB_POSTGRES_USER=postgres \
            -e DB_POSTGRES_PASSWORD=postgres-password \
            -p 8181:8181 \
            research-system:latest || {
            echo -e "${RED}Failed to start Research System container.${NC}"
            exit 1
        }
    }
    
    echo -e "${GREEN}Containers started successfully.${NC}"
    echo -e "${YELLOW}Running containers:${NC}"
    podman ps
    
    echo -e "${GREEN}Application is accessible at: http://localhost:8181${NC}"
}

# Function to stop podman containers
stop_podman_compose() {
    echo -e "${BLUE}Stopping podman containers...${NC}"
    
    if command -v podman-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
        echo -e "${YELLOW}Stopping containers with podman-compose...${NC}"
        podman-compose down || {
            echo -e "${RED}Failed to stop containers with podman-compose.${NC}"
            echo -e "${YELLOW}Attempting to stop containers individually...${NC}"
            
            podman stop research-system 2>/dev/null || true
            podman stop research-postgres 2>/dev/null || true
            
            podman rm research-system 2>/dev/null || true
            podman rm research-postgres 2>/dev/null || true
        }
    else
        echo -e "${YELLOW}Stopping containers individually...${NC}"
        podman stop research-system 2>/dev/null || true
        podman stop research-postgres 2>/dev/null || true
        
        podman rm research-system 2>/dev/null || true
        podman rm research-postgres 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Containers stopped.${NC}"
}

# Parse command-line arguments
COMMAND=""
SKIP_CHECKS="false"
FORCE="false"

# Default values have been set at the top

# Parse arguments
for arg in "$@"; do
    case $arg in
        setup|precheck|start|deploy|status|logs|stop|clean|help|podman-start|podman-stop)
            COMMAND="$arg"
            ;;
        --driver=*)
            DRIVER="${arg#*=}"
            ;;
        --memory=*)
            MEMORY="${arg#*=}"
            ;;
        --cpus=*)
            CPUS="${arg#*=}"
            ;;
        --k8s-version=*)
            K8S_VERSION="${arg#*=}"
            ;;
        --container-runtime=*)
            CONTAINER_RUNTIME="${arg#*=}"
            ;;
        --skip-checks)
            SKIP_CHECKS="true"
            ;;
        --force)
            FORCE="true"
            ;;
        --auto-install)
            AUTO_INSTALL="true"
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
    setup)
        check_dependencies "--auto-install"
        ;;
    precheck)
        pre_start_check
        ;;
    start)
        start_kubernetes
        ;;
    deploy)
        deploy_to_kubernetes
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    stop)
        stop_kubernetes
        ;;
    clean)
        clean_all
        ;;
    podman-start)
        start_podman_compose
        ;;
    podman-stop)
        stop_podman_compose
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