#!/bin/bash -e

# Activate virtual environment
export PATH="/opt/venv/bin:$PATH"

# Set up Dagu directories and configuration
echo "Starting dagu (Dagu-based pipeline runner)..."

# Create Dagu configuration directory
# mkdir -p /root/.dagu
mkdir -p ~/.config/dagu || true

export DAGU_DAGS="/dags"
export DAGU_HOME="/root/.config/dagu"

if [[ -f /root/config.yaml ]]; then
    echo "Setting up main configuration..."
    mv /root/config.yaml ~/.config/dagu/
fi

# Set Dagu environment variables
export DAGU_AUTH_BASIC_USERNAME=admin
export DAGU_AUTH_BASIC_PASSWORD=${DAGU_ADMIN_PASSWORD}
export DAGU_PORT=8080

# Verify configuration
echo "Verifying Dagu setup..."
echo "  DAGU_DAGS: $DAGU_DAGS"
echo "  DAGU_HOME: $DAGU_HOME"
echo "  Config files:"
ls -la /root/.config/dagu/ || echo "  No config files found"

# Check if DAGs directory exists and has files
if [[ -d "$DAGU_DAGS" ]]; then
    DAG_COUNT=$(find "$DAGU_DAGS" -name "*.yaml" -o -name "*.yml" | wc -l)
    echo "  Found $DAG_COUNT DAG files in $DAGU_DAGS"
    find "$DAGU_DAGS" -name "*.yaml" -o -name "*.yml" | head -5
else
    echo "  DAGs directory not found: $DAGU_DAGS"
fi

# Validate Dagu installation
echo "Validating Dagu installation..."
dagu version || echo "   Could not get Dagu version"

echo "Starting Dagu ..."
dagu start-all --host=0.0.0.0 --port=8080 &
DAGU_PID=$!

# Function to handle shutdown gracefully
shutdown() {
    echo "Shutting down dagu..."
    echo "Stopping (PID: $DAGU_PID)..."
    kill $DAGU_PID 2>/dev/null || true
    wait $DAGU_PID 2>/dev/null || true
    echo "Shutdown complete"
    exit 0
}

# Set up dagu handlers for graceful shutdown
trap shutdown SIGTERM SIGINT

# Wait for either process to exit
wait $DAGU_PID