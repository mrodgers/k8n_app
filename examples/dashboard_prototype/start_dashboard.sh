#!/bin/bash
# Start the Research System Dashboard
# This script starts the dashboard on port 8199

echo "Starting Research System Dashboard on port 8299..."
echo "Access the dashboard at http://localhost:8299"

# Run in the background with nohup
nohup python direct_dashboard.py > dashboard.log 2>&1 &

# Save the PID
echo $! > dashboard.pid

echo "Dashboard started with PID $(cat dashboard.pid)"
echo "To stop the dashboard, run: ./stop_dashboard.sh"