# MCP Tool Handler Instrumentation Guide

## Current Instrumentation State

### What IS Instrumented ✅

1. **HTTP Layer** (via `otelgin` middleware in `main.go`):
   - GET /sse (SSE connection)
   - POST /sse (MCP JSON-RPC messages)
   - All other HTTP endpoints

   This creates spans like:
   ```
   POST /sse
   ├─ duration: 45ms
   ├─ http.method: POST
   ├─ http.route: /sse
   └─ http.status_code: 200
   ```

### What is NOT Instrumented ❌

1. **MCP Tool Handlers**:
   - `CreateTodo()`
   - `GetTodos()`
   - `UpdateTodo()`
   - `DeleteTodo()`

2. **MCP Resources**:
   - `TodosWithDueDate()`

3. **MCP Prompts**:
   - `AddTodo()`
   - `UpdateTodo()`

4. **HTTP Client Calls to todo-api**:
   - `client.CreateTodoWithResponse()`
   - `client.GetTodosWithResponse()`
   - etc.

## Why MCP Handlers Aren't Traced

The MCP SDK handles the protocol layer:

```
HTTP Request (traced ✅)
  └─ POST /sse with JSON-RPC payload
      │
      ▼
  MCP SDK parses the request
      │
      ▼
  MCP SDK calls your handler (NOT traced ❌)
      │
      └─ CreateTodo(ctx, req, input)
          │
          └─ client.CreateTodoWithResponse() (NOT traced ❌)
```

**The problem**: The MCP SDK doesn't know about OpenTelemetry, so it doesn't create spans when calling your handlers.

## How to Add Instrumentation

### Option 1: Manual Instrumentation (Simple)

Add tracing at the beginning of each handler:

```go
func CreateTodo(ctx context.Context, req *mcp.CallToolRequest, input CreateTodoInput) (*mcp.CallToolResult, any, error) {
    // Start a new span
    tracer := otel.Tracer("todo-mcp")
    ctx, span := tracer.Start(ctx, "mcp.tool.CreateTodo")
    defer span.End()

    // Add attributes about the tool call
    span.SetAttributes(
        attribute.String("mcp.tool.name", "todos-add"),
        attribute.String("todo.title", input.Title),
    )

    if input.Title == "" {
        span.RecordError(fmt.Errorf("title parameter is required"))
        span.SetStatus(codes.Error, "Missing required parameter")
        return &mcp.CallToolResult{...}, nil, nil
    }

    createTodoRequest := todoclient.CreateTodoRequest{
        Title:   input.Title,
        DueDate: input.DueDate,
    }

    // Make HTTP call with context (this propagates trace!)
    resp, err := client.CreateTodoWithResponse(ctx, createTodoRequest)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "Failed to create todo")
        return &mcp.CallToolResult{...}, nil, nil
    }

    if resp.StatusCode() != 201 {
        err := fmt.Errorf("received status code %d", resp.StatusCode())
        span.RecordError(err)
        span.SetStatus(codes.Error, "Non-201 status code")
        return &mcp.CallToolResult{...}, nil, nil
    }

    // Add result attributes
    if resp.JSON201 != nil {
        span.SetAttributes(
            attribute.Int64("todo.id", int64(resp.JSON201.Id)),
            attribute.String("todo.created_at", resp.JSON201.CreatedAt.String()),
        )
    }

    span.SetStatus(codes.Ok, "Todo created successfully")
    textResponse := fmt.Sprintf("Added todo: %s", input.Title)

    return &mcp.CallToolResult{
        Content: []mcp.Content{
            &mcp.TextContent{Text: textResponse},
        },
    }, nil, nil
}
```

### Option 2: Middleware Wrapper (Advanced)

Create a helper that wraps MCP tool handlers:

```go
// telemetry/mcp.go
package telemetry

import (
    "context"
    "github.com/modelcontextprotocol/go-sdk/mcp"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
)

// WrapToolHandler wraps an MCP tool handler with tracing
func WrapToolHandler[I any](
    toolName string,
    handler func(context.Context, *mcp.CallToolRequest, I) (*mcp.CallToolResult, any, error),
) func(context.Context, *mcp.CallToolRequest, I) (*mcp.CallToolResult, any, error) {
    return func(ctx context.Context, req *mcp.CallToolRequest, input I) (*mcp.CallToolResult, any, error) {
        tracer := otel.Tracer("todo-mcp")
        ctx, span := tracer.Start(ctx, "mcp.tool."+toolName)
        defer span.End()

        span.SetAttributes(
            attribute.String("mcp.tool.name", toolName),
            attribute.String("mcp.tool.type", "tool"),
        )

        result, data, err := handler(ctx, req, input)

        if err != nil {
            span.RecordError(err)
            span.SetStatus(codes.Error, err.Error())
        } else if result != nil && result.IsError {
            span.SetStatus(codes.Error, "Tool returned error")
        } else {
            span.SetStatus(codes.Ok, "Tool executed successfully")
        }

        return result, data, err
    }
}
```

Then use it in `main.go`:

```go
mcp.AddTool(srv, &mcp.Tool{
    Name:         "todos-add",
    Description:  "A tool to add a new todo item",
    InputSchema:  handlers.AddTodoInputSchema,
    OutputSchema: handlers.AddTodoOutputSchema,
}, telemetry.WrapToolHandler("todos-add", handlers.CreateTodo))
```

## Full Example: Instrumented CreateTodo

Here's what a fully instrumented handler looks like:

```go
package handlers

import (
    "context"
    "encoding/json"
    "fmt"
    "time"

    "github.com/modelcontextprotocol/go-sdk/mcp"
    todoclient "github.com/scottseotech/todo-platform/clients/todo-client-go"
    "github.com/scottseotech/todo-platform/services/todo-mcp/config"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
)

type CreateTodoInput struct {
    Title   string     `json:"title"`
    DueDate *time.Time `json:"due_date,omitempty"`
}

func CreateTodo(ctx context.Context, req *mcp.CallToolRequest, input CreateTodoInput) (*mcp.CallToolResult, any, error) {
    // Create span for MCP tool call
    tracer := otel.Tracer("todo-mcp")
    ctx, span := tracer.Start(ctx, "mcp.tool.CreateTodo")
    defer span.End()

    span.SetAttributes(
        attribute.String("mcp.tool.name", "todos-add"),
        attribute.String("mcp.tool.type", "tool"),
        attribute.String("todo.title", input.Title),
    )

    // Validation
    if input.Title == "" {
        err := fmt.Errorf("title parameter is required")
        span.RecordError(err)
        span.SetStatus(codes.Error, "Validation failed")
        return &mcp.CallToolResult{
            Content: []mcp.Content{
                &mcp.TextContent{Text: "Error: title parameter is required and must be a non-empty string"},
            },
            IsError: true,
        }, nil, nil
    }

    // Add due date attribute if present
    if input.DueDate != nil {
        span.SetAttributes(attribute.String("todo.due_date", input.DueDate.Format(time.RFC3339)))
    }

    createTodoRequest := todoclient.CreateTodoRequest{
        Title:   input.Title,
        DueDate: input.DueDate,
    }

    // HTTP call to todo-api (context propagates trace!)
    resp, err := client.CreateTodoWithResponse(ctx, createTodoRequest)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "HTTP request failed")
        return &mcp.CallToolResult{
            Content: []mcp.Content{
                &mcp.TextContent{Text: fmt.Sprintf("Error creating todo: %v", err)},
            },
            IsError: true,
        }, nil, nil
    }

    // Check status code
    if resp.StatusCode() != 201 {
        err := fmt.Errorf("received status code %d", resp.StatusCode())
        span.RecordError(err)
        span.SetStatus(codes.Error, "Non-201 status code")
        span.SetAttributes(attribute.Int("http.status_code", resp.StatusCode()))
        return &mcp.CallToolResult{
            Content: []mcp.Content{
                &mcp.TextContent{Text: fmt.Sprintf("Error: received status code %d", resp.StatusCode())},
            },
            IsError: true,
        }, nil, nil
    }

    // Add result attributes
    if resp.JSON201 != nil {
        span.SetAttributes(
            attribute.Int64("todo.id", int64(resp.JSON201.Id)),
            attribute.String("todo.created_at", resp.JSON201.CreatedAt.String()),
        )
    }

    span.SetStatus(codes.Ok, "Todo created successfully")
    textResponse := fmt.Sprintf("Added todo: %s", input.Title)

    return &mcp.CallToolResult{
        Content: []mcp.Content{
            &mcp.TextContent{Text: textResponse},
        },
    }, nil, nil
}
```

## Expected Trace Visualization

After instrumentation, you'll see traces like this in Grafana Tempo:

```
POST /sse (42ms) ✅ Already traced
│
└─ mcp.tool.CreateTodo (38ms) ✅ NEW!
    │ mcp.tool.name: "todos-add"
    │ todo.title: "Buy groceries"
    │
    └─ POST /api/v1/todos (35ms) ✅ HTTP client propagates trace
        │ http.method: POST
        │ http.url: http://todo-api:8080/api/v1/todos
        │
        └─ CreateTodo (33ms) ✅ todo-api handler
            │ todo.id: 123
            │ todo.created_at: "2025-10-28T10:30:00Z"
            │
            └─ INSERT INTO todos (30ms) ✅ Database query (if instrumented)
```

## Why This Matters

### Without Instrumentation
You only see:
```
POST /sse - 42ms
```

You can't tell:
- Which MCP tool was called
- What parameters were passed
- How long the tool execution took
- What the result was
- Where errors occurred

### With Instrumentation
You see the full picture:
```
POST /sse - 42ms
└─ mcp.tool.CreateTodo - 38ms
   └─ POST /api/v1/todos - 35ms
      └─ CreateTodo handler - 33ms
         └─ INSERT INTO todos - 30ms
```

You can see:
- Exact tool called: `CreateTodo`
- Parameters: `title="Buy groceries"`
- Time breakdown: 42ms total, 38ms in tool, 35ms in HTTP, 30ms in DB
- Success/failure status
- Error messages and stack traces

## Instrumenting HTTP Client Calls

The `todoclient.ClientWithResponses` HTTP client needs to be instrumented to propagate traces to todo-api.

### Option 1: Wrap the HTTP Client

```go
import (
    "net/http"
    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

func init() {
    cfg := config.Load()

    // Create HTTP client with OTel instrumentation
    httpClient := &http.Client{
        Transport: otelhttp.NewTransport(http.DefaultTransport),
    }

    var err error
    client, err = todoclient.NewClientWithResponses(
        cfg.TodoAPIURL,
        todoclient.WithHTTPClient(httpClient), // Use instrumented client
    )
    if err != nil {
        panic(err)
    }
}
```

### Option 2: Manual HTTP Request Instrumentation

If the client doesn't support custom HTTP clients:

```go
import (
    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

// Manually create HTTP request with tracing
req, _ := http.NewRequestWithContext(ctx, "POST", cfg.TodoAPIURL+"/api/v1/todos", body)

// Wrap the request with OTel
client := &http.Client{
    Transport: otelhttp.NewTransport(http.DefaultTransport),
}

resp, err := client.Do(req)
```

## Summary

**Current state:**
- ✅ HTTP layer is traced (SSE connections, JSON-RPC messages)
- ❌ MCP tool handlers are NOT traced
- ❌ HTTP client calls to todo-api are NOT traced
- ❌ MCP resources and prompts are NOT traced

**To fix:**
1. Add `tracer.Start()` at the beginning of each MCP tool handler
2. Add attributes for tool name, parameters, and results
3. Record errors and set span status
4. Instrument the HTTP client to propagate traces to todo-api

**Result:**
- Full end-to-end tracing from Slack bot → todo-mcp → todo-api → database
- Clear visibility into MCP tool execution
- Performance bottleneck identification
- Error tracking with full context
