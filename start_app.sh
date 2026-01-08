#!/bin/bash
# SmartMold Pilot V3 - Application Launcher
# This script starts the NiceGUI application in the background

set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python3"
LOG_FILE="/tmp/smartmold_app.log"

echo "🚀 Starting SmartMold Pilot V3..."
echo "   Project: $PROJECT_DIR"
echo "   Python:  $VENV_PYTHON"
echo "   Logs:    $LOG_FILE"

# Kill any existing instances on port 8080
if lsof -i :8080 >/dev/null 2>&1; then
    echo "⚠️  Cleaning up existing processes on port 8080..."
    lsof -i :8080 | grep -v COMMAND | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
    sleep 2
fi

# Start the application
cd "$PROJECT_DIR"
$VENV_PYTHON main.py > "$LOG_FILE" 2>&1 &
APP_PID=$!

# Save PID
echo $APP_PID > /tmp/smartmold.pid

# Wait for startup
sleep 3

# Check if running
if kill -0 $APP_PID 2>/dev/null; then
    echo "✅ Application started (PID: $APP_PID)"
    echo "🌐 Open browser at: http://localhost:8080"
    echo "📊 Network access: http://192.168.31.124:8080"
else
    echo "❌ Application failed to start. Check logs:"
    cat "$LOG_FILE"
    exit 1
fi
