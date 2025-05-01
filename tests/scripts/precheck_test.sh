#!/bin/bash

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
        echo -e "${RED}❌ Some dependencies are missing. Run './scripts/k8s_manager.sh setup --auto-install' to install them.${NC}"
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
    echo -e "  ./scripts/k8s_manager.sh start"
    echo -e ""
}

# Run the pre-start check
pre_start_check