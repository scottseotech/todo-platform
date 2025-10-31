#!/bin/bash

# Local development script for todo-mcp with OpenTelemetry

set -e

echo "Starting todo-mcp locally with OpenTelemetry..."

# Service configuration
export TODO_API_URL=${TODO_API_URL:-"http://localhost:8080"}
export SERVER_PORT=${SERVER_PORT:-"8081"}

# OpenTelemetry configuration
export OTEL_ENABLE_STDOUT=${OTEL_ENABLE_STDOUT:-"true"}
export OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT:-""}  # Empty = no OTLP export
export ENVIRONMENT=${ENVIRONMENT:-"development"}
export SERVICE_VERSION=${SERVICE_VERSION:-"local-dev"}

echo "Configuration:"
echo "  Todo API URL: ${TODO_API_URL}"
echo "  Server Port: ${SERVER_PORT}"
echo "  OTLP Endpoint: ${OTEL_EXPORTER_OTLP_ENDPOINT:-"(disabled - using stdout)"}"
echo "  Stdout Export: ${OTEL_ENABLE_STDOUT}"
echo ""

# Run the service
go run main.go
