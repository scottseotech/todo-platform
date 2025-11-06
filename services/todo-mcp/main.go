package main

import (
	"context"
	_ "embed"
	"log"
	"net/http"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/scottseotech/todo-platform/services/todo-mcp/config"
	"github.com/scottseotech/todo-platform/services/todo-mcp/handlers"
	"github.com/scottseotech/todo-platform/services/todo-mcp/middleware"
	"github.com/scottseotech/todo-platform/services/todo-mcp/prompts"
	"github.com/scottseotech/todo-platform/services/todo-mcp/resources"
	"github.com/scottseotech/todo-platform/services/todo-mcp/telemetry"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
)

//go:embed openapi.json
var openapiSpec []byte

func main() {
	cfg := config.Load()

	// Initialize OpenTelemetry
	telemetryConfig := telemetry.LoadConfig("todo-mcp", "1.0.0")
	shutdown, err := telemetry.InitTracer(telemetryConfig)
	if err != nil {
		log.Fatalf("Failed to initialize telemetry: %v", err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := shutdown(ctx); err != nil {
			log.Printf("Error shutting down telemetry: %v", err)
		}
	}()

	// Create Gin router
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(gin.Logger())

	// Add OpenTelemetry middleware with filter to exclude health/metrics
	router.Use(otelgin.Middleware("todo-mcp",
		otelgin.WithFilter(func(r *http.Request) bool {
			// Exclude health and metrics endpoints from tracing
			return r.URL.Path != "/health" && r.URL.Path != "/metrics"
		}),
	))

	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{
			"https://editor.swagger.io",
			"http://localhost:8000",
			"https://docs.scottseo.tech",
		},
		AllowMethods: []string{"GET", "OPTIONS"},
		AllowHeaders: []string{"Content-Type", "Accept"},
	}))

	// Create MCP server
	srv := mcp.NewServer(
		&mcp.Implementation{
			Name:    "todo-mcp",
			Version: "1.0.0",
		},
		nil,
	)

	srv.AddResource(&mcp.Resource{
		Name:     "todos-with-due-date",
		MIMEType: "application/json",
		URI:      "todos://with-due-date",
	}, resources.TodosWithDueDate)

	srv.AddPrompt(&mcp.Prompt{
		Name:      "todos-add",
		Title:     "Add a new todo item",
		Arguments: prompts.AddTodoArguments(),
	}, prompts.AddTodo)

	srv.AddPrompt(&mcp.Prompt{
		Name:      "todos-update",
		Title:     "Update an existing todo item",
		Arguments: prompts.UpdateTodoArguments(),
	}, prompts.UpdateTodo)

	// Register todo tools
	mcp.AddTool(srv, &mcp.Tool{
		Name:         "todos-add",
		Description:  "A tool to add a new todo item",
		InputSchema:  handlers.AddTodoInputSchema,
		OutputSchema: handlers.AddTodoOutputSchema,
	}, handlers.CreateTodo)

	mcp.AddTool(srv, &mcp.Tool{
		Name:         "todos-list",
		Description:  "A tool to retrieve all todo items",
		InputSchema:  handlers.GetTodosInputSchema,
		OutputSchema: handlers.GetTodosOutputSchema,
	}, handlers.GetTodos)

	mcp.AddTool(srv, &mcp.Tool{
		Name:         "todos-update",
		Description:  "A tool to update an existing todo item by ID",
		InputSchema:  handlers.UpdateTodoInputSchema,
		OutputSchema: handlers.UpdateTodoOutputSchema,
	}, handlers.UpdateTodo)

	mcp.AddTool(srv, &mcp.Tool{
		Name:         "todos-delete",
		Description:  "A tool to delete a todo item by ID",
		InputSchema:  handlers.DeleteTodoInputSchema,
		OutputSchema: handlers.DeleteTodoOutputSchema,
	}, handlers.DeleteTodo)

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	// Prometheus metrics endpoint
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// MCP SSE endpoint - SDK handles the session
	// SSE needs both GET (for event stream) and POST (for sending messages)
	sseHandler := mcp.NewSSEHandler(func(*http.Request) *mcp.Server { return srv }, nil)

	// Wrap SSE handler with logging middleware
	loggedSSEHandler := middleware.SSELogger()(sseHandler)

	router.GET("/sse", gin.WrapH(loggedSSEHandler))
	router.POST("/sse", gin.WrapH(loggedSSEHandler))

	// OpenAPI specification endpoint
	router.GET("/openapi.json", func(c *gin.Context) {
		c.Data(http.StatusOK, "application/json", openapiSpec)
	})

	// Regular HTTP endpoints for MCP protocol
	router.GET("/schema", handlers.Schema())
	router.GET("/capabilities", handlers.Capabilities())

	router.GET("/tools", handlers.Tools())
	router.POST("/tools/:id/invoke", handlers.InvokeTool())

	// Start server
	addr := ":" + cfg.ServerPort
	log.Printf("Starting todo-mcp server on %s", addr)
	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
