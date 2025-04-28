#!/bin/bash
# Container build script that includes version information

# Set colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure we're in the project root directory
cd "$(dirname "$0")/.." || { echo "Failed to change to project directory"; exit 1; }

# Parse arguments
PATCH_VERSION=false
MINOR_VERSION=false
MAJOR_VERSION=false
SKIP_GIT=false
CREATE_TAG=false
BUILD_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --patch)
      PATCH_VERSION=true
      shift
      ;;
    --minor)
      MINOR_VERSION=true
      shift
      ;;
    --major)
      MAJOR_VERSION=true
      shift
      ;;
    --no-git)
      SKIP_GIT=true
      shift
      ;;
    --tag)
      CREATE_TAG=true
      shift
      ;;
    --build-only)
      BUILD_ONLY=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Usage: $0 [--patch|--minor|--major] [--no-git] [--tag] [--build-only]"
      exit 1
      ;;
  esac
done

# Increment version number
echo -e "${BLUE}Updating build number...${NC}"
VERSION_ARGS=""
if [ "$PATCH_VERSION" = true ]; then
  VERSION_ARGS="--patch"
elif [ "$MINOR_VERSION" = true ]; then
  VERSION_ARGS="--minor"
elif [ "$MAJOR_VERSION" = true ]; then
  VERSION_ARGS="--major"
fi

if [ "$SKIP_GIT" = true ]; then
  VERSION_ARGS="$VERSION_ARGS --no-git"
fi

if [ "$CREATE_TAG" = true ]; then
  VERSION_ARGS="$VERSION_ARGS --release"
fi

# Run the Python build script to update version information
python scripts/build.py $VERSION_ARGS

# Get version information for the build
VERSION=$(python -c "from src.research_system.version import __version__; print(__version__)")
BUILD_NUMBER=$(python -c "from src.research_system.version import BUILD_NUMBER; print(BUILD_NUMBER)")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo -e "${GREEN}Building version ${VERSION} (build ${BUILD_NUMBER})${NC}"

# Skip container build if --build-only is specified
if [ "$BUILD_ONLY" = true ]; then
  echo -e "${YELLOW}Skipping container build (--build-only specified)${NC}"
  exit 0
fi

# Build the container with version information
echo -e "${BLUE}Building container image...${NC}"
podman build \
  --build-arg VERSION="${VERSION}" \
  --build-arg BUILD_NUMBER="${BUILD_NUMBER}" \
  --build-arg BUILD_DATE="${BUILD_DATE}" \
  -t localhost/research-system:latest \
  -t localhost/research-system:"${VERSION}-${BUILD_NUMBER}" \
  .

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Container built successfully${NC}"
  echo -e "Tags:"
  echo -e "  - localhost/research-system:latest"
  echo -e "  - localhost/research-system:${VERSION}-${BUILD_NUMBER}"
  
  # Display version information
  echo -e "\n${BLUE}Version Information:${NC}"
  echo -e "  Version:      ${GREEN}${VERSION}${NC}"
  echo -e "  Build Number: ${GREEN}${BUILD_NUMBER}${NC}"
  echo -e "  Build Date:   ${GREEN}${BUILD_DATE}${NC}"
  
  # Suggest next steps
  echo -e "\n${BLUE}Next Steps:${NC}"
  echo -e "  - Start the application:  ${YELLOW}./app_manager.sh start${NC}"
  echo -e "  - Check status:           ${YELLOW}./app_manager.sh status${NC}"
  echo -e "  - Push to registry:       ${YELLOW}podman push localhost/research-system:${VERSION}-${BUILD_NUMBER} registry.example.com/research-system:${VERSION}-${BUILD_NUMBER}${NC}"
  
  exit 0
else
  echo -e "${RED}Container build failed${NC}"
  exit 1
fi