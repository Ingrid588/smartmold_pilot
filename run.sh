#!/bin/bash
# SmartMold Pilot V3 - Application Launcher

echo "================================"
echo "SmartMold Pilot V3 - Launcher"
echo "================================"
echo ""

# Check if running from correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found!"
    echo "Please run this script from the SmartMold_Pilot directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "Please create and activate the virtual environment first."
    exit 1
fi

# Run the application
echo "🚀 Starting SmartMold Pilot V3..."
echo ""
echo "App will be available at: http://localhost:9091"
echo "Press Ctrl+C to stop the application."
echo ""

/Users/aaa/SmartMold_Pilot/.venv/bin/python3 main.py
