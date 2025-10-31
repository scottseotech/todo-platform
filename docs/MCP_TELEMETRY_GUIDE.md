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

### Option 2: Middleware Wrapper (Advanced)

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
