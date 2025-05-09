#!/bin/bash
# Stop the Research System Dashboard (Fixed Version)

if [ -f fixed_dashboard.pid ]; then
    PID=$(cat fixed_dashboard.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Fixed Dashboard with PID $PID..."
        kill $PID
        rm fixed_dashboard.pid
        echo "Dashboard stopped."
    else
        echo "Fixed Dashboard not running (PID $PID not found)"
        rm fixed_dashboard.pid
    fi
else
    echo "Fixed Dashboard PID file not found. Dashboard may not be running."
fi