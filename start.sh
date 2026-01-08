#!/bin/bash
# SmartMold Pilot V3 - Application Startup Script

echo "🚀 SmartMold Pilot V3 - Starting Application"
echo "Port: 8080"
echo "URL: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

cd /Users/a/SmartMold_Pilot
/Users/a/SmartMold_Pilot/.venv/bin/python3 -c "
import main
" 2>&1
