# Troubleshooting tracing

1. Start up the local servers(api & mcp) with OTEL_ENABLE_STDOUT set to true.

2. Hit the mcp test invoke endpoint to initiate manual testing. Use the following.
```bash
curl -X POST http://localhost:8081/tools/todos-add/invoke \
    -H "Content-Type: application/json" \
    -d '{"arguments": {"title": "Test trace propagation", "due_date": "2025-11-01T10:00:00Z"}}
```
3. Verify trace id on both services match

## Testing against k8s env
Enable port forwarding to expose mcp endpoint for testing
```bash
k port-forward -n default svc/todo-mcp 8081:8081
```

Hit the mcp test invoke endpoint to initiate manual testing. Use the following.
```bash
curl -X POST http://localhost:8081/tools/todos-add/invoke \
    -H "Content-Type: application/json" \
    -d '{"arguments": {"title": "Test trace propagation", "due_date": "2025-11-01T10:00:00Z"}}
```