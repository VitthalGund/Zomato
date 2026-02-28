#!/bin/bash
# Backend startup script

echo "Starting Zomato EdgeVision Backend..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the server
uvicorn main:app --reload --port 8000
