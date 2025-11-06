"""
OpenTelemetry configuration for todo-bot.

This module initializes OpenTelemetry tracing with OTLP exporter to send traces
to Tempo via gRPC. It also instruments the Flask app and requests library for
automatic span creation.
"""

import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor

logger = logging.getLogger(__name__)


def init_telemetry(app=None):
    """
    Initialize OpenTelemetry with OTLP exporter.

    Args:
        app: Optional Flask app to instrument

    Returns:
        Tracer instance for manual span creation
    """
    # Check if OTEL is enabled
    otel_enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
    if not otel_enabled:
        logger.info("OpenTelemetry is disabled via OTEL_ENABLED env var")
        return None

    # Create resource with service information
    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "todo-bot"),
        "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter (sends to Tempo)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "tempo:4317")
    insecure = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true"

    logger.info(f"Configuring OTLP exporter: endpoint={otlp_endpoint}, insecure={insecure}")

    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=insecure
    )

    # Add batch span processor for efficient export
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Optionally add console exporter for debugging
    stdout_enabled = os.getenv("OTEL_ENABLE_STDOUT", "false").lower() == "true"
    if stdout_enabled:
        logger.info("Console span exporter enabled for debugging")
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument requests library (for MCP client calls)
    RequestsInstrumentor().instrument()
    logger.info("Requests library instrumented for automatic tracing")

    # Auto-instrument Flask app if provided
    if app:
        # Exclude health endpoint from tracing
        def flask_request_hook(span, environ):
            # Suppress tracing for health checks
            if environ.get("PATH_INFO") == "/health":
                span.set_attribute("http.route", "/health")
                span.set_attribute("otel.suppress_instrumentation", True)

        FlaskInstrumentor().instrument_app(
            app,
            excluded_urls="/health",  # Exclude health endpoint from tracing
        )
        logger.info("Flask app instrumented for automatic tracing (excluding /health)")

    logger.info("OpenTelemetry initialized successfully")

    # Return tracer for manual span creation
    return trace.get_tracer(__name__)


def get_tracer():
    """Get the tracer instance for manual span creation."""
    return trace.get_tracer(__name__)
