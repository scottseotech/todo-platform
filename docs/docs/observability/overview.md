# Observability Stack

## OpenTelemetry
Instrumentation for distributed tracing.

- **Exporters**: OTLP/gRPC to Tempo
- **Propagation**: W3C Trace Context
- **SDK**: Go OpenTelemetry

## Tempo
Distributed tracing backend.

- **Storage**: Local filesystem
- **Query**: Grafana integration
- **Retention**: Configurable

## Loki

## Grafana
Unified observability dashboard.

- **Data Sources**: Tempo, Loki, Prometheus
- **Dashboards**: Pre-configured
- **Alerts**: Prometheus AlertManager
