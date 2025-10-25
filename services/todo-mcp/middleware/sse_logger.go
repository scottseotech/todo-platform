package middleware

import (
	"bytes"
	"io"
	"log"
	"net/http"
)

// SSELogger creates a middleware that logs SSE requests (without breaking streaming)
func SSELogger() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Log incoming request
			log.Printf("[SSE] %s %s", r.Method, r.URL.Path)

			// Log query parameters
			if len(r.URL.Query()) > 0 {
				log.Printf("[SSE] Query params: %v", r.URL.Query())
			}

			// Log request headers
			log.Printf("[SSE] Request headers: Accept=%s, Content-Type=%s",
				r.Header.Get("Accept"),
				r.Header.Get("Content-Type"))

			// Log request body for POST
			if r.Method == "POST" {
				bodyBytes, err := io.ReadAll(r.Body)
				if err == nil {
					log.Printf("[SSE] Request body: %s", string(bodyBytes))
					// Restore body for next handler
					r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))
				}
			}

			// For SSE (GET requests with text/event-stream), don't wrap the response writer
			// because it breaks streaming and flushing
			if r.Method == "GET" && r.Header.Get("Accept") == "text/event-stream" {
				log.Printf("[SSE] Streaming response (GET /sse) - not buffering")
				next.ServeHTTP(w, r)
				return
			}

			// For non-streaming requests (POST), we can safely log the response
			log.Printf("[SSE] Non-streaming request - will log response")
			next.ServeHTTP(w, r)
		})
	}
}
