package middleware

import (
	"fmt"
	"time"

	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/otel/trace"
)

// LoggerWithTraceID is a custom logger middleware that includes trace_id and span_id in logs
func LoggerWithTraceID() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Start timer
		start := time.Now()
		path := c.Request.URL.Path
		query := c.Request.URL.RawQuery

		// Process request
		c.Next()

		// Calculate latency
		latency := time.Since(start)

		// Get trace context from span
		span := trace.SpanFromContext(c.Request.Context())
		spanContext := span.SpanContext()

		traceID := ""
		spanID := ""
		if spanContext.IsValid() {
			traceID = spanContext.TraceID().String()
			spanID = spanContext.SpanID().String()
		}

		// Get status code
		statusCode := c.Writer.Status()

		// Log format: [GIN] timestamp | status | latency | method | path | trace_id | span_id
		if query != "" {
			path = path + "?" + query
		}

		// Color codes for status
		statusColor := getStatusColor(statusCode)
		methodColor := getMethodColor(c.Request.Method)
		resetColor := "\033[0m"

		if traceID != "" {
			fmt.Printf("[GIN] %s |%s %3d %s| %13v | %15s |%s %-7s %s %s | trace_id=%s span_id=%s\n",
				start.Format("2006/01/02 - 15:04:05"),
				statusColor, statusCode, resetColor,
				latency,
				c.ClientIP(),
				methodColor, c.Request.Method, resetColor,
				path,
				traceID,
				spanID,
			)
		} else {
			// Fallback to regular format without trace info
			fmt.Printf("[GIN] %s |%s %3d %s| %13v | %15s |%s %-7s %s %s\n",
				start.Format("2006/01/02 - 15:04:05"),
				statusColor, statusCode, resetColor,
				latency,
				c.ClientIP(),
				methodColor, c.Request.Method, resetColor,
				path,
			)
		}
	}
}

func getStatusColor(code int) string {
	switch {
	case code >= 200 && code < 300:
		return "\033[97;42m" // green
	case code >= 300 && code < 400:
		return "\033[90;47m" // white
	case code >= 400 && code < 500:
		return "\033[90;43m" // yellow
	default:
		return "\033[97;41m" // red
	}
}

func getMethodColor(method string) string {
	switch method {
	case "GET":
		return "\033[97;44m" // blue
	case "POST":
		return "\033[97;42m" // green
	case "PUT":
		return "\033[97;43m" // yellow
	case "DELETE":
		return "\033[97;41m" // red
	case "PATCH":
		return "\033[97;45m" // magenta
	case "HEAD":
		return "\033[97;46m" // cyan
	case "OPTIONS":
		return "\033[90;47m" // white
	default:
		return "\033[0m" // reset
	}
}
