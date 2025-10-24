package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/scottseo.tech/todo-platform/services/todo-mcp/handlers"
)

type Config struct {
	ServerPort string
	TodoAPIURL string
}

func loadConfig() Config {
	// Load .env file for local development
	err := godotenv.Load()
	if err != nil {
		log.Printf("Continuing without .env file")
	}

	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "8081"
	}

	todoAPIURL := os.Getenv("TODO_API_URL")
	if todoAPIURL == "" {
		todoAPIURL = "http://localhost:8080"
	}

	return Config{
		ServerPort: port,
		TodoAPIURL: todoAPIURL,
	}
}

func main() {
	cfg := loadConfig()

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
	}, helloHandler)

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
	r.GET("/schema", schemaHandler)
	r.GET("/capabilities", capabilitiesHandler)

	r.GET("/tools", listToolsHandler(srv))
	r.POST("/tools/:id/invoke", invokeToolHandler(srv))

	// Start server
	addr := ":" + cfg.ServerPort
	log.Printf("Starting todo-mcp server on %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

// HelloInput defines the input parameters for the hello tool
type HelloInput struct {
	Name string `json:"name"`
}

// helloHandler implements the hello tool
func helloHandler(ctx context.Context, req *mcp.CallToolRequest, input HelloInput) (*mcp.CallToolResult, any, error) {
	if input.Name == "" {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: "Error: name parameter is required and must be a non-empty string"},
			},
			IsError: true,
		}, nil, nil
	}

	// Generate greeting
	greeting := fmt.Sprintf("Hello, %s! Welcome to the Todo MCP server. Hello back to you!", input.Name)

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: greeting},
		},
	}, nil, nil
}

// schemaHandler returns the MCP protocol schema
func schemaHandler(c *gin.Context) {
	schema := gin.H{
		"version": "1.0.0",
		"protocol": gin.H{
			"name":    "Model Context Protocol",
			"version": "2024-11-05",
		},
		"server": gin.H{
			"name":    "todo-mcp",
			"version": "1.0.0",
		},
	}

	c.JSON(http.StatusOK, schema)
}

// capabilitiesHandler returns the server capabilities
func capabilitiesHandler(c *gin.Context) {
	capabilities := gin.H{
		"tools": gin.H{
			"supported": true,
		},
		"prompts": gin.H{
			"supported": false,
		},
		"resources": gin.H{
			"supported": false,
		},
	}

	c.JSON(http.StatusOK, capabilities)
}

// listToolsHandler returns a handler that lists all available tools
func listToolsHandler(srv *mcp.Server) gin.HandlerFunc {
	return handlers.Tools
}

// invokeToolHandler returns a handler that invokes a specific tool
// Note: This is a REST-like endpoint for testing. For production MCP usage, use the /sse endpoint
func invokeToolHandler(srv *mcp.Server) gin.HandlerFunc {
	return func(c *gin.Context) {
		toolID := c.Param("id")

		// Parse request body
		var requestBody struct {
			Arguments map[string]interface{} `json:"arguments"`
		}

		if err := c.ShouldBindJSON(&requestBody); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
			return
		}

		// Execute the tool directly (bypassing MCP protocol for HTTP convenience)
		var result *mcp.CallToolResult
		var err error

		switch toolID {
		case "hello":
			name, _ := requestBody.Arguments["name"].(string)
			input := HelloInput{Name: name}
			result, _, err = helloHandler(c.Request.Context(), nil, input)
		default:
			c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("Tool '%s' not found", toolID)})
			return
		}

		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		// Build response
		response := gin.H{
			"content": result.Content,
		}

		if result.IsError {
			response["isError"] = true
		}

		c.JSON(http.StatusOK, response)
	}
}
