package handlers

import (
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func Tools() gin.HandlerFunc {
	return func(c *gin.Context) {
		tools := []gin.H{
			{
				"id":          "add_todo",
				"name":        "add_todo",
				"description": "A tool to add a new todo item",
				"inputSchema": gin.H{
					"type": "object",
					"properties": gin.H{
						"name": gin.H{
							"type":        "string",
							"description": "The title of the todo item",
						},
						"due_date": gin.H{
							"type":        "string",
							"format":      "date-time",
							"description": "The due date of the todo item (optional)",
						},
					},
					"required": []string{"title"},
				},
			},
		}

		c.JSON(http.StatusOK, gin.H{
			"tools": tools,
		})
	}
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
		case "add_todo":
			title, _ := requestBody.Arguments["title"].(string)
			input := TodoCreateInput{Title: title}
			result, _, err = TodoCreate(c.Request.Context(), nil, input)
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
