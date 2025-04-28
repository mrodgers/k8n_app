#!/bin/bash
# Script to test Ollama LLM features in the Research System

set -e

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
API_URL="http://localhost:8181"
TASK_TITLE="Climate Change Research"
TASK_DESC="Research on the effects of climate change on coastal cities"
TASK_TAGS="climate,research,coastal"
SEARCH_QUERY="impacts of rising sea levels on coastal cities"

# Banner
echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}     Research System LLM Features Test      ${NC}"
echo -e "${BLUE}=============================================${NC}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --api-url)
      API_URL="$2"
      shift
      shift
      ;;
    --task-title)
      TASK_TITLE="$2"
      shift
      shift
      ;;
    --task-desc)
      TASK_DESC="$2"
      shift
      shift
      ;;
    --task-tags)
      TASK_TAGS="$2"
      shift
      shift
      ;;
    --search-query)
      SEARCH_QUERY="$2"
      shift
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --api-url       Specify API URL (default: http://localhost:8181)"
      echo "  --task-title    Specify task title"
      echo "  --task-desc     Specify task description"
      echo "  --task-tags     Specify task tags (comma-separated)"
      echo "  --search-query  Specify search query"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo -e "Using API URL: ${YELLOW}$API_URL${NC}"

# Check if the server is running
echo -e "\n${BLUE}Step 1: Checking if Research System server is running...${NC}"
if ! curl -s "$API_URL/health" | grep -q "healthy"; then
    echo -e "${RED}Server is not running or not responding. Please start it with ./app_manager.sh start${NC}"
    exit 1
fi
echo -e "${GREEN}Server is running!${NC}"

# Check if LLM is enabled
echo -e "\n${BLUE}Step 2: Checking if LLM features are enabled...${NC}"
LLM_STATUS=$(curl -s "$API_URL/" | grep -o '"enabled":[^,}]*')
if [[ "$LLM_STATUS" == *"true"* ]]; then
    LLM_MODEL=$(curl -s "$API_URL/" | grep -o '"model":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}LLM features are enabled with model: ${YELLOW}$LLM_MODEL${NC}"
else
    echo -e "${RED}LLM features are not enabled. Please check your configuration.${NC}"
    exit 1
fi

# Create a research task
echo -e "\n${BLUE}Step 3: Creating a research task...${NC}"
TASK_TAGS_JSON="[$(echo $TASK_TAGS | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/' | sed 's/""//g')]"
TASK_JSON="{\"title\":\"$TASK_TITLE\",\"description\":\"$TASK_DESC\",\"tags\":$TASK_TAGS_JSON}"
TASK_RESP=$(curl -s -X POST "$API_URL/api/tasks" -H "Content-Type: application/json" -d "$TASK_JSON")
TASK_ID=$(echo $TASK_RESP | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
    echo -e "${RED}Failed to create task. Response: $TASK_RESP${NC}"
    exit 1
fi
echo -e "${GREEN}Task created with ID: ${YELLOW}$TASK_ID${NC}"

# Generate a research plan using LLM
echo -e "\n${BLUE}Step 4: Generating a research plan with LLM...${NC}"
PLAN_RESP=$(curl -s -X POST "$API_URL/api/tasks/$TASK_ID/plan")
PLAN_ID=$(echo $PLAN_RESP | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$PLAN_ID" ]; then
    echo -e "${RED}Failed to create plan. Response: $PLAN_RESP${NC}"
    exit 1
fi

# Check if the plan has LLM-generated steps
STEP_COUNT=$(echo $PLAN_RESP | grep -o '"steps":\[[^]]*\]' | grep -o 'name' | wc -l)
echo -e "${GREEN}Plan created with ID: ${YELLOW}$PLAN_ID${GREEN} with ${YELLOW}$STEP_COUNT${GREEN} steps${NC}"

# Display the plan steps
echo -e "\n${BLUE}Plan steps:${NC}"
echo $PLAN_RESP | grep -o '"name":"[^"]*' | cut -d'"' -f4 | nl

# Execute a search query
echo -e "\n${BLUE}Step 5: Executing a search query...${NC}"
SEARCH_JSON="{\"query\":\"$SEARCH_QUERY\",\"max_results\":5}"
SEARCH_RESP=$(curl -s -X POST "$API_URL/api/tasks/$TASK_ID/search" -H "Content-Type: application/json" -d "$SEARCH_JSON")
RESULT_COUNT=$(echo $SEARCH_RESP | grep -o '"results":\[[^]]*\]' | grep -o 'title' | wc -l)

if [ "$RESULT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}Search executed successfully with ${YELLOW}$RESULT_COUNT${GREEN} results${NC}"
    
    # Display search results with relevance scores (LLM enhanced)
    echo -e "\n${BLUE}Search results with relevance scores:${NC}"
    echo $SEARCH_RESP | grep -o '"title":"[^"]*' | cut -d'"' -f4 | nl
    
    # Display relevance scores
    echo -e "\n${BLUE}Relevance scores (higher is better):${NC}"
    echo $SEARCH_RESP | grep -o '"relevance_score":[^,}]*' | nl
else
    echo -e "${YELLOW}Search executed but no results were found.${NC}"
fi

echo -e "\n${GREEN}End-to-end test completed successfully!${NC}"
echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}    Key files for Ollama integration:        ${NC}"
echo -e "${BLUE}=============================================${NC}"
echo -e "${YELLOW}* src/research_system/llm/ollama_client.py${NC} - Client for Ollama API"
echo -e "${YELLOW}* src/research_system/agents/planner.py${NC} - Planner agent with LLM capabilities"
echo -e "${YELLOW}* src/research_system/agents/search.py${NC} - Search agent with LLM capabilities"
echo -e "${YELLOW}* kubernetes/ollama.yaml${NC} - Kubernetes deployment for Ollama"
echo -e "${YELLOW}* scripts/run_llm_tests.sh${NC} - Script for testing Ollama integration"