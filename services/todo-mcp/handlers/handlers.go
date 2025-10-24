package handlers

import (
	"context"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func Tools() gin.HandlerFunc {
	return func(c *gin.Context) {
		tools := []gin.H{
			{
				"id":          "hello",
				"name":        "hello",
				"description": "A simple hello world tool that greets you and says hello back",
				"inputSchema": gin.H{
					"type": "object",
					"properties": gin.H{
						"name": gin.H{
							"type":        "string",
							"description": "The name to greet",
						},
					},
					"required": []string{"name"},
				},
			},
		}

		c.JSON(http.StatusOK, gin.H{
			"tools": tools,
		})
	}
}

// HelloInput defines the input parameters for the hello tool
type HelloInput struct {
	Name string `json:"name"`
}

// InvokeTool returns a handler that invokes a specific tool
// Note: This is a REST-like endpoint for testing. For production MCP usage, use the /sse endpoint
func InvokeTool() gin.HandlerFunc {
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
			result, _, err = HelloHandler(c.Request.Context(), nil, input)
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

// HelloHandler implements the hello tool
func HelloHandler(ctx context.Context, req *mcp.CallToolRequest, input HelloInput) (*mcp.CallToolResult, any, error) {
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
func Schema() gin.HandlerFunc {
	return func(c *gin.Context) {
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
}

// CapabilitiesHandler returns the server capabilities
func Capabilities() gin.HandlerFunc {
	return func(c *gin.Context) {
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
}
