package main

import (
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/scottseotech/todo-platform/services/todo-mcp/config"
	"github.com/scottseotech/todo-platform/services/todo-mcp/handlers"
)

func main() {
	cfg := config.Load()

	// Create Gin router
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(gin.Logger())

	// Create MCP server
	srv := mcp.NewServer(
		&mcp.Implementation{
			Name:    "todo-mcp",
			Version: "1.0.0",
		},
		nil,
	)

	// Register hello tool
	mcp.AddTool(srv, &mcp.Tool{
		Name:        "hello",
		Description: "A simple hello world tool that greets you and says hello back",
	}, handlers.HelloHandler)

	// Health check endpoint
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	// MCP SSE endpoint - SDK handles the session
	// SSE needs both GET (for event stream) and POST (for sending messages)
	sseHandler := mcp.NewSSEHandler(func(*http.Request) *mcp.Server { return srv }, nil)
	r.GET("/sse", gin.WrapH(sseHandler))
	r.POST("/sse", gin.WrapH(sseHandler))

	// Regular HTTP endpoints for MCP protocol
	r.GET("/schema", handlers.Schema())
	r.GET("/capabilities", handlers.Capabilities())

	r.GET("/tools", handlers.Tools())
	r.POST("/tools/:id/invoke", handlers.InvokeTool())

	// Start server
	addr := ":" + cfg.ServerPort
	log.Printf("Starting todo-mcp server on %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
