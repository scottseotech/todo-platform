package telemetry

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
	"go.opentelemetry.io/otel/trace"
)

// Config holds telemetry configuration
type Config struct {
	ServiceName    string
	ServiceVersion string
	Environment    string
	OTLPEndpoint   string
	EnableStdout   bool
}

// InitTracer initializes the OpenTelemetry tracer
func InitTracer(cfg Config) (func(context.Context) error, error) {
	ctx := context.Background()

	// Create resource with service information
	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceNameKey.String(cfg.ServiceName),
			semconv.ServiceVersionKey.String(cfg.ServiceVersion),
			attribute.String("environment", cfg.Environment),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	var exporters []sdktrace.SpanExporter

	// OTLP exporter (for Tempo, Jaeger, etc.)
	if cfg.OTLPEndpoint != "" {
		otlpExporter, err := otlptracegrpc.New(ctx,
			otlptracegrpc.WithEndpoint(cfg.OTLPEndpoint),
			otlptracegrpc.WithInsecure(), // Use TLS in production
		)
		if err != nil {
			return nil, fmt.Errorf("failed to create OTLP exporter: %w", err)
		}
		exporters = append(exporters, otlpExporter)
		log.Printf("OTLP trace exporter configured: %s", cfg.OTLPEndpoint)
	}

	// Stdout exporter (for local development)
	if cfg.EnableStdout {
		stdoutExporter, err := stdouttrace.New(
			stdouttrace.WithPrettyPrint(),
		)
		if err != nil {
			return nil, fmt.Errorf("failed to create stdout exporter: %w", err)
		}
		exporters = append(exporters, stdoutExporter)
		log.Println("Stdout trace exporter enabled")
	}

	// If no exporters configured, log warning but don't fail
	if len(exporters) == 0 {
		log.Println("Warning: No trace exporters configured. Telemetry will be no-op.")
		return func(context.Context) error { return nil }, nil
	}

	// Create batch span processors for each exporter
	var options []sdktrace.TracerProviderOption
	options = append(options, sdktrace.WithResource(res))

	for _, exporter := range exporters {
		options = append(options, sdktrace.WithBatcher(exporter,
			sdktrace.WithBatchTimeout(5*time.Second),
			sdktrace.WithMaxExportBatchSize(512),
		))
	}

	// Create tracer provider
	tp := sdktrace.NewTracerProvider(options...)

	// Set global tracer provider
	otel.SetTracerProvider(tp)

	// Set global propagator (for distributed tracing)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	log.Printf("Telemetry initialized: service=%s, version=%s, env=%s",
		cfg.ServiceName, cfg.ServiceVersion, cfg.Environment)

	// Return shutdown function
	return tp.Shutdown, nil
}

// LoadConfig loads telemetry configuration from environment
func LoadConfig(serviceName, serviceVersion string) Config {
	return Config{
		ServiceName:    serviceName,
		ServiceVersion: getEnv("SERVICE_VERSION", serviceVersion),
		Environment:    getEnv("ENVIRONMENT", "development"),
		OTLPEndpoint:   getEnv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
		EnableStdout:   getEnv("OTEL_ENABLE_STDOUT", "false") == "true",
	}
}

// Tracer returns a tracer for the given name
func Tracer(name string) trace.Tracer {
	return otel.Tracer(name)
}

// Helper function to get environment variable with default
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
