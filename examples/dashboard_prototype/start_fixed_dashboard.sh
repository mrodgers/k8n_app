#!/bin/bash
# Start the Research System Dashboard (Fixed Version)
# This script starts the fixed dashboard on port 8299

echo "Starting Research System Dashboard (Fixed Version) on port 8299..."
echo "Access the dashboard at http://localhost:8299"

# Run in the background with nohup
nohup python fixed_dashboard.py > fixed_dashboard.log 2>&1 &

# Save the PID
echo $! > fixed_dashboard.pid

echo "Dashboard started with PID $(cat fixed_dashboard.pid)"
echo "To stop the dashboard, run: ./stop_fixed_dashboard.sh"