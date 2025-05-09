#!/bin/bash
# Stop the Research System Dashboard

if [ -f dashboard.pid ]; then
    PID=$(cat dashboard.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Dashboard with PID $PID..."
        kill $PID
        rm dashboard.pid
        echo "Dashboard stopped."
    else
        echo "Dashboard not running (PID $PID not found)"
        rm dashboard.pid
    fi
else
    echo "Dashboard PID file not found. Dashboard may not be running."
fi