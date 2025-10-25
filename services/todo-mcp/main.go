package main

import (
	_ "embed"
	"log"
	"net/http"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/scottseotech/todo-platform/services/todo-mcp/config"
	"github.com/scottseotech/todo-platform/services/todo-mcp/handlers"
	"github.com/scottseotech/todo-platform/services/todo-mcp/middleware"
)

//go:embed openapi.json
var openapiSpec []byte

func main() {
	cfg := config.Load()

	// Create Gin router
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(gin.Logger())
	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{"https://editor.swagger.io"},
		AllowMethods: []string{"GET"},
		AllowHeaders: []string{"Content-Type"},
	}))

	// Create MCP server
	srv := mcp.NewServer(
		&mcp.Implementation{
			Name:    "todo-mcp",
			Version: "1.0.0",
		},
		nil,
	)

	// Register todo tools
	mcp.AddTool(srv, &mcp.Tool{
		Name:         "add_todo",
		Description:  "A tool to add a new todo item",
		InputSchema:  handlers.AddTodoInputSchema,
		OutputSchema: handlers.AddTodoOutputSchema,
	}, handlers.CreateTodo)

	mcp.AddTool(srv, &mcp.Tool{
		Name:         "get_todos",
		Description:  "A tool to retrieve all todo items",
		InputSchema:  handlers.GetTodosInputSchema,
		OutputSchema: handlers.GetTodosOutputSchema,
	}, handlers.GetTodos)

	mcp.AddTool(srv, &mcp.Tool{
		Name:         "update_todo",
		Description:  "A tool to update an existing todo item by ID",
		InputSchema:  handlers.UpdateTodoInputSchema,
		OutputSchema: handlers.UpdateTodoOutputSchema,
	}, handlers.UpdateTodo)

	mcp.AddTool(srv, &mcp.Tool{
		Name:         "delete_todo",
		Description:  "A tool to delete a todo item by ID",
		InputSchema:  handlers.DeleteTodoInputSchema,
		OutputSchema: handlers.DeleteTodoOutputSchema,
	}, handlers.DeleteTodo)

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

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
