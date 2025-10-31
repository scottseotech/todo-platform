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

### High Overhead

- Reduce sampling rate
- Increase batch timeout
- Disable stdout exporter in production

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
