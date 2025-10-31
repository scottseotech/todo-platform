#!/bin/bash

# Local development script for todo-api with OpenTelemetry

set -e

echo "Starting todo-api locally with OpenTelemetry..."

# Database configuration will be loaded from .env file by godotenv in main.go

# OpenTelemetry configuration
export OTEL_ENABLE_STDOUT=${OTEL_ENABLE_STDOUT:-"true"}
export OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT:-""}  # Empty = no OTLP export
export ENVIRONMENT=${ENVIRONMENT:-"development"}
export SERVICE_VERSION=${SERVICE_VERSION:-"local-dev"}

echo "Configuration:"
echo "  Database: (loaded from .env)"
echo "  OTLP Endpoint: ${OTEL_EXPORTER_OTLP_ENDPOINT:-"(disabled - using stdout)"}"
echo "  Stdout Export: ${OTEL_ENABLE_STDOUT}"
echo ""

# Run the service
go run main.go
