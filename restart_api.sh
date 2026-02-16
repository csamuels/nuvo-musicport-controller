#!/bin/bash
# Restart API Server Script

echo "Finding API server process..."
API_PID=$(ps aux | grep "[u]vicorn api.main:app" | awk '{print $2}')

if [ -n "$API_PID" ]; then
    echo "Stopping API server (PID: $API_PID)..."
    kill $API_PID
    sleep 2
else
    echo "No API server process found"
fi

echo "Starting API server with auto-reload..."
cd /c/Users/Corey/PycharmProjects/musicport
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &

echo "API server starting..."
sleep 3
echo "Done! API server should be running on http://localhost:8000"
