# Todo MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with the Todo API. Built with Go using the official [MCP Go SDK](https://github.com/modelcontextprotocol/go-sdk) and Gin web framework.

## Overview

This service implements the MCP protocol with Server-Sent Events (SSE) transport, providing a hybrid approach where:
- The `/sse` endpoint uses the MCP SDK for full protocol compliance
- Additional REST endpoints (`/api/v1/*`) provide convenient HTTP access for testing

## Features

- **MCP Protocol Support**: Full MCP server implementation with SSE transport
- **Tools**: Extensible tool system (currently implements "hello" tool)
- **REST API**: Convenient HTTP endpoints for development and testing
- **Health Checks**: `/health` endpoint for monitoring

## Endpoints

### MCP Protocol

- `GET /sse` - Server-Sent Events endpoint for MCP client communication
- `GET /schema` - Returns MCP protocol schema information
- `GET /capabilities` - Returns server capabilities

### REST API (for testing)

- `GET /health` - Health check endpoint
- `GET /api/v1/tools` - List all available tools
- `POST /api/v1/tools/:id/invoke` - Invoke a specific tool by ID

## Available Tools

### hello

A simple greeting tool that demonstrates the MCP tool system.

**Input:**
```json
{
  "name": "string (required)"
}
```

**Output:**
```
Hello, {name}! Welcome to the Todo MCP server. Hello back to you!
```

## Configuration

Environment variables:

- `SERVER_PORT` - Port to run the server on (default: `8081`)
- `TODO_API_URL` - URL of the Todo API service (default: `http://localhost:8080`)

For local development, create a `.env` file:

```env
SERVER_PORT=8081
TODO_API_URL=http://localhost:8080
```

## Running Locally

```bash
# Install dependencies
go mod download

# Run the server
go run main.go

# Or build and run
go build -o todo-mcp .
./todo-mcp
```

## Testing with REST API

```bash
# List available tools
curl http://localhost:8081/api/v1/tools

# Invoke the hello tool
curl -X POST http://localhost:8081/api/v1/tools/hello/invoke \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"name": "World"}}'
```

## Testing with MCP Client

The SSE endpoint follows the MCP protocol specification. You can connect using any MCP-compatible client:

```go
package main

import (
    "context"
    "fmt"
    "log"

    "github.com/modelcontextprotocol/go-sdk/mcp"
)

func main() {
    transport := &mcp.SSEClientTransport{Endpoint: "http://localhost:8081/sse"}
    client := mcp.NewClient(&mcp.Implementation{Name: "test-client", Version: "v1.0.0"}, nil)

    cs, err := client.Connect(context.Background(), transport, nil)
    if err != nil {
        log.Fatal(err)
    }
    defer cs.Close()

    result, err := cs.CallTool(context.Background(), &mcp.CallToolParams{
        Name:      "hello",
        Arguments: map[string]any{"name": "World"},
    })
    if err != nil {
        log.Fatal(err)
    }

    fmt.Println(result.Content[0].(*mcp.TextContent).Text)
}
```

## Architecture

```
┌─────────────┐
│  MCP Client │
└──────┬──────┘
       │ SSE
       ↓
┌─────────────────────────┐
│    Gin Router           │
│  ┌──────────────────┐   │
│  │  /sse            │◄──┼── MCP SDK handles protocol
│  │  (SSE Handler)   │   │
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │  REST Endpoints  │   │
│  │  /api/v1/tools/* │   │
│  └──────────────────┘   │
└─────────┬───────────────┘
          │
          ↓
    ┌──────────┐
    │  Tools   │
    │  • hello │
    └──────────┘
```

## Future Enhancements

- [ ] Add tools for Todo API operations (create, list, update, delete todos)
- [ ] Implement prompts support
- [ ] Add resources support
- [ ] Integration with Todo API REST client
- [ ] Add authentication/authorization
- [ ] Metrics and observability

## Development

### Adding a New Tool

1. Define input struct with JSON schema tags:

```go
type MyToolInput struct {
    Param string `json:"param" jsonschema:"description=Parameter description,required"`
}
```

2. Implement the tool handler:

```go
func myToolHandler(ctx context.Context, req *mcp.CallToolRequest, input MyToolInput) (*mcp.CallToolResult, any, error) {
    return &mcp.CallToolResult{
        Content: []mcp.Content{
            &mcp.TextContent{Text: "result"},
        },
    }, nil, nil
}
```

3. Register the tool:

```go
mcp.AddTool(srv, &mcp.Tool{
    Name:        "mytool",
    Description: "Tool description",
}, myToolHandler)
```

4. Add to REST invoke handler switch statement

## License

Part of the scottseo.tech todo-platform monorepo.
