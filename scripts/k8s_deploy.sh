#!/bin/bash
# Deploy to Kubernetes with proper versioning

# Set colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure we're in the project root directory
cd "$(dirname "$0")/.." || { echo "Failed to change to project directory"; exit 1; }

# Default values
NAMESPACE="default"
IMAGE_TAG="latest"
VERSION=""
DRY_RUN=false
SKIP_VERSION_CHECK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --namespace=*)
      NAMESPACE="${1#*=}"
      shift
      ;;
    --tag=*)
      IMAGE_TAG="${1#*=}"
      shift
      ;;
    --version=*)
      VERSION="${1#*=}"
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --skip-version-check)
      SKIP_VERSION_CHECK=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: $0 [--namespace=default] [--tag=latest] [--version=1.0.0] [--dry-run] [--skip-version-check]"
      exit 1
      ;;
  esac
done

# Get version info if not specified
if [ -z "$VERSION" ] && [ "$SKIP_VERSION_CHECK" = false ]; then
  if [ -f "src/research_system/version.py" ]; then
    VERSION=$(python -c "from src.research_system.version import __version__; print(__version__)")
    BUILD_NUMBER=$(python -c "from src.research_system.version import BUILD_NUMBER; print(BUILD_NUMBER)")
    
    if [ -n "$VERSION" ] && [ -n "$BUILD_NUMBER" ]; then
      if [ "$IMAGE_TAG" = "latest" ]; then
        IMAGE_TAG="${VERSION}-${BUILD_NUMBER}"
        echo -e "${BLUE}Using version from version.py: ${VERSION} (build ${BUILD_NUMBER})${NC}"
      fi
      VERSION="${VERSION}"
    else
      echo -e "${YELLOW}Could not determine version from version.py${NC}"
      if [ -z "$VERSION" ]; then
        VERSION="1.0.0"
        echo -e "${YELLOW}Using default version: ${VERSION}${NC}"
      fi
    fi
  else
    echo -e "${YELLOW}version.py not found${NC}"
    if [ -z "$VERSION" ]; then
      VERSION="1.0.0"
      echo -e "${YELLOW}Using default version: ${VERSION}${NC}"
    fi
  fi
fi

# Prepare environment variables for templating
export RESEARCH_SYSTEM_IMAGE="research-system:${IMAGE_TAG}"
export RESEARCH_SYSTEM_VERSION="${VERSION}"

echo -e "${BLUE}Deploying Research System to Kubernetes${NC}"
echo -e "  Namespace:  ${GREEN}${NAMESPACE}${NC}"
echo -e "  Image:      ${GREEN}${RESEARCH_SYSTEM_IMAGE}${NC}"
echo -e "  Version:    ${GREEN}${RESEARCH_SYSTEM_VERSION}${NC}"

# Handle dry run
KUBECTL_ARGS=""
if [ "$DRY_RUN" = true ]; then
  KUBECTL_ARGS="--dry-run=client -o yaml"
  echo -e "${YELLOW}DRY RUN: No changes will be applied${NC}"
fi

# Process and apply Kubernetes manifests with environment variable substitution
echo -e "${BLUE}Applying Kubernetes manifests with version ${VERSION}...${NC}"

# Apply ConfigMap first (if it exists)
if [ -f "kubernetes/configmaps.yaml" ]; then
  echo -e "${BLUE}Applying ConfigMap...${NC}"
  envsubst < kubernetes/configmaps.yaml | kubectl apply -n "${NAMESPACE}" ${KUBECTL_ARGS} -f -
fi

# Apply the Deployment
echo -e "${BLUE}Applying Deployment...${NC}"
envsubst < kubernetes/deployment.yaml | kubectl apply -n "${NAMESPACE}" ${KUBECTL_ARGS} -f -

# Apply the Service
echo -e "${BLUE}Applying Service...${NC}"
envsubst < kubernetes/service.yaml | kubectl apply -n "${NAMESPACE}" ${KUBECTL_ARGS} -f -

if [ "$DRY_RUN" = false ]; then
  echo -e "${GREEN}Deployment completed successfully${NC}"
  
  # Print instructions for checking status
  echo -e "\n${BLUE}To check deployment status:${NC}"
  echo -e "  kubectl -n ${NAMESPACE} get pods"
  echo -e "  kubectl -n ${NAMESPACE} get deployments"
  echo -e "  kubectl -n ${NAMESPACE} get services"
  
  # Print URL for accessing the application
  echo -e "\n${BLUE}To access the application:${NC}"
  echo -e "  kubectl -n ${NAMESPACE} port-forward svc/research-system 8181:80"
  echo -e "  # Then visit http://localhost:8181 in your browser"
  
  # Print how to check logs
  echo -e "\n${BLUE}To check application logs:${NC}"
  echo -e "  kubectl -n ${NAMESPACE} logs -l app=research-system -f"
fi