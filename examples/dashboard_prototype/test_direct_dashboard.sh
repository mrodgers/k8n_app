#!/bin/bash
# Test script for the direct dashboard implementation

echo "Testing Research System Dashboard (Direct Version)..."

# Check if the dashboard is already running on port 8299
if lsof -i:8299 >/dev/null 2>&1; then
    echo "Dashboard is already running on port 8299"
else
    echo "Starting dashboard for testing..."
    # Start dashboard in background
    nohup python direct_dashboard.py > test_dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    echo "Dashboard started with PID $DASHBOARD_PID"
    sleep 2  # Give it time to start
fi

echo
echo "=== Running tests ==="
echo

# Test the API endpoints
echo "1. Testing container listing endpoint..."
CONTAINERS=$(curl -s http://localhost:8299/containers)
echo "Response length: ${#CONTAINERS} characters"
if [[ "$CONTAINERS" == *"error"* ]]; then
    echo "❌ Error in container listing: $CONTAINERS"
else
    echo "✅ Container listing endpoint works"
fi

echo
echo "2. Testing debug endpoint..."
DEBUG_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8299/debug/containers)
if [[ "$DEBUG_RESPONSE" == "200" ]]; then
    echo "✅ Debug endpoint works"
else
    echo "❌ Error in debug endpoint: $DEBUG_RESPONSE"
fi

echo
echo "3. Testing dashboard home page..."
HOME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8299/dashboard)
if [[ "$HOME_RESPONSE" == "200" ]]; then
    echo "✅ Dashboard home page works"
else
    echo "❌ Error in dashboard home page: $HOME_RESPONSE"
fi

echo
echo "=== Test results ==="
echo
echo "API health: $(if [[ "$CONTAINERS" != *"error"* ]]; then echo "✅ GOOD"; else echo "❌ FAILED"; fi)"
echo "Dashboard UI: $(if [[ "$HOME_RESPONSE" == "200" ]]; then echo "✅ GOOD"; else echo "❌ FAILED"; fi)"
echo

# If we started the dashboard for this test, stop it
if [[ -n "$DASHBOARD_PID" ]]; then
    echo "Stopping test dashboard (PID $DASHBOARD_PID)..."
    kill $DASHBOARD_PID
    echo "Dashboard stopped"
fi

echo
echo "You can manually access the dashboard at: http://localhost:8299/dashboard"
echo "To start the dashboard, run: ./start_dashboard.sh"