#!/bin/bash
# Development script with auto-reload
# Usage: ./dev.sh

echo "🔧 Starting todo-bot in development mode with auto-reload..."
watchmedo auto-restart \
  --directory=. \
  --pattern="*.py" \
  --recursive \
  -- python app.py
