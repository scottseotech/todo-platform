#!/bin/bash
# Generate static API documentation from OpenAPI specs

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Generating API documentation..."

# Generate todo-api docs
echo "  - todo-api..."
npx @redocly/cli build-docs \
  "$REPO_ROOT/services/todo-api/openapi.json" \
  -o "$SCRIPT_DIR/docs/api/todo-api.html"

# Generate todo-mcp docs
echo "  - todo-mcp..."
npx @redocly/cli build-docs \
  "$REPO_ROOT/services/todo-mcp/openapi.json" \
  -o "$SCRIPT_DIR/docs/api/todo-mcp.html"

echo "✓ API documentation generated successfully"
