## Trace Attributes

### Automatic Attributes

All traces include:

- `service.name`: Service identifier (todo-api, todo-mcp)
- `service.version`: Application version
- `environment`: Deployment environment
- `http.method`: HTTP method (GET, POST, etc.)
- `http.route`: Route pattern (/api/v1/todos/:id)
- `http.status_code`: Response status code
- `http.client_ip`: Client IP address


## Visualizing Traces

### Grafana with Tempo

1. Access Grafana: `kubectl port-forward -n observability svc/grafana 3000:3000`
2. Navigate to Explore
3. Select Tempo data source
4. Query traces:
   - By Trace ID
   - By service name
   - By tag (e.g., `http.status_code=500`)

## Trace Context Propagation

Traces are propagated across services using:

- **W3C Trace Context**: Standard HTTP headers (`traceparent`, `tracestate`)
- **Baggage**: Key-value pairs propagated with trace context

## Performance Considerations

### Sampling

Current configuration uses **always-on sampling** (all traces recorded).

For high-traffic production environments, consider:

```go
// In telemetry.go
sdktrace.WithSampler(sdktrace.ParentBased(
    sdktrace.TraceIDRatioBased(0.1), // Sample 10% of traces
))
```

### Batch Processing

Spans are batched and exported every 5 seconds or when batch reaches 512 spans:

```go
sdktrace.WithBatcher(exporter,
    sdktrace.WithBatchTimeout(5*time.Second),
    sdktrace.WithMaxExportBatchSize(512),
)
```

## Troubleshooting

### No Traces Appearing

1. **Check exporter configuration**:
   ```bash
   # Verify OTLP endpoint is reachable
   curl http://tempo:4318/v1/traces
   ```

2. **Enable stdout exporter**:
   ```bash
   export OTEL_ENABLE_STDOUT=true
   ```
   Check if traces are printed to stdout.

3. **Verify service startup logs**:
   ```
   Telemetry initialized: service=todo-api, version=1.0.0, env=production
   OTLP trace exporter configured: tempo:4318
   ```

### Incomplete Traces

- **Database spans missing**: Ensure database queries use `WithContext(ctx)`
- **HTTP client spans missing**: Use instrumented HTTP client

### High Overhead

- Reduce sampling rate
- Increase batch timeout
- Disable stdout exporter in production

## Adding Custom Spans

### Example: Instrumenting a Function

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
)

func ProcessTodo(ctx context.Context, todoID int) error {
    tracer := otel.Tracer("todo-api")
    ctx, span := tracer.Start(ctx, "ProcessTodo")
    defer span.End()

    // Add attributes
    span.SetAttributes(
        attribute.Int("todo.id", todoID),
        attribute.String("operation", "process"),
    )

    // Do work...
    err := doSomething(ctx)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "Processing failed")
        return err
    }

    span.SetStatus(codes.Ok, "Processing completed")
    return nil
}
```

### Example: Adding Events

```go
span.AddEvent("validation_started")
// ... validation logic ...
span.AddEvent("validation_completed", trace.WithAttributes(
    attribute.Int("rules_checked", 10),
))
```

## Metrics (Future Enhancement)

While not yet implemented, the telemetry package is ready for metrics:

```go
import "go.opentelemetry.io/otel/metric"

// Create meter
meter := otel.Meter("todo-api")

// Create counter
todoCreated, _ := meter.Int64Counter(
    "todos.created",
    metric.WithDescription("Number of todos created"),
)

// Increment counter
todoCreated.Add(ctx, 1,
    metric.WithAttributes(attribute.String("user", userID)),
)
```

## Best Practices

1. **Always propagate context**: Pass `context.Context` through function calls
2. **Use descriptive span names**: `CreateTodo` not `Handler`
3. **Add meaningful attributes**: Include IDs, user info, business logic data
4. **Record errors**: Always call `span.RecordError(err)` on errors
5. **Set span status**: Use `codes.Ok` or `codes.Error`
6. **Keep spans focused**: One logical operation per span
7. **Avoid sensitive data**: Don't include passwords, tokens in attributes

## References

- [OpenTelemetry Go Documentation](https://opentelemetry.io/docs/languages/go/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
