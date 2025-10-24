package main

import (
	"log"
	"net/http"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/scottseotech/todo-platform/services/todo-mcp/config"
	"github.com/scottseotech/todo-platform/services/todo-mcp/handlers"
)

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

	// Register add_todo tool
	mcp.AddTool(srv, &mcp.Tool{
		Name:        "add_todo",
		Description: "A tool to add a new todo item",
	}, handlers.TodoCreate)

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	// MCP SSE endpoint - SDK handles the session
	// SSE needs both GET (for event stream) and POST (for sending messages)
	sseHandler := mcp.NewSSEHandler(func(*http.Request) *mcp.Server { return srv }, nil)
	router.GET("/sse", gin.WrapH(sseHandler))
	router.POST("/sse", gin.WrapH(sseHandler))

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
