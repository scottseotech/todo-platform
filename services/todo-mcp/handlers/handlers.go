package handlers

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

var AddTodoInputSchema map[string]any = gin.H{
	"type": "object",
	"properties": gin.H{
		"title": gin.H{
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
}
var GetTodosInputSchema map[string]any = gin.H{
	"type":       "object",
	"properties": gin.H{},
}
var UpdateTodoInputSchema map[string]any = gin.H{
	"type": "object",
	"properties": gin.H{
		"id": gin.H{
			"type":        "integer",
			"description": "The ID of the todo item to update",
		},
		"title": gin.H{
			"type":        "string",
			"description": "The new title for the todo item (optional)",
		},
		"due_date": gin.H{
			"type":        "string",
			"format":      "date-time",
			"description": "The new due date for the todo item (optional)",
		},
	},
	"required": []string{"id"},
}
var DeleteTodoInputSchema map[string]any = gin.H{
	"type": "object",
	"properties": gin.H{
		"id": gin.H{
			"type":        "integer",
			"description": "The ID of the todo item to delete",
		},
	},
	"required": []string{"id"},
}

// Output Schemas
var AddTodoOutputSchema map[string]any = gin.H{
	"type": "object",
	"properties": gin.H{
		"id": gin.H{
			"type":        "integer",
			"description": "The ID of the created todo item",
		},
		"title": gin.H{
			"type":        "string",
			"description": "The title of the created todo item",
		},
		"created_at": gin.H{
			"type":        "string",
			"format":      "date-time",
			"description": "When the todo was created",
		},
		"updated_at": gin.H{
			"type":        "string",
			"format":      "date-time",
			"description": "When the todo was last updated",
		},
	},
}

var GetTodosOutputSchema map[string]any = gin.H{
	"type": "object",
	"items": gin.H{
		"type": "array",
		"properties": gin.H{
			"id": gin.H{
				"type":        "integer",
				"description": "The ID of the todo item",
			},
			"title": gin.H{
				"type":        "string",
				"description": "The title of the todo item",
			},
			"created_at": gin.H{
				"type":        "string",
				"format":      "date-time",
				"description": "When the todo was created",
			},
			"updated_at": gin.H{
				"type":        "string",
				"format":      "date-time",
				"description": "When the todo was last updated",
			},
		},
	},
}

var UpdateTodoOutputSchema map[string]any = gin.H{
	"type": "object",
	"properties": gin.H{
		"id": gin.H{
			"type":        "integer",
			"description": "The ID of the updated todo item",
		},
		"title": gin.H{
			"type":        "string",
			"description": "The updated title",
		},
		"updated_at": gin.H{
			"type":        "string",
			"format":      "date-time",
			"description": "When the todo was last updated",
		},
	},
}

var DeleteTodoOutputSchema map[string]any = gin.H{
	"type": "object",
	"properties": gin.H{
		"success": gin.H{
			"type":        "boolean",
			"description": "Whether the deletion was successful",
		},
		"id": gin.H{
			"type":        "integer",
			"description": "The ID of the deleted todo item",
		},
	},
}

// Tools returns the list of available tools
func Tools() gin.HandlerFunc {
	return func(c *gin.Context) {
		log.Printf("Received tools request")
		tools := []gin.H{
			{
				"id":          "todos-add",
				"name":        "todos-add",
				"description": "A tool to add a new todo item",
				"inputSchema": AddTodoInputSchema,
			},
			{
				"id":          "todos-list",
				"name":        "todos-list",
				"description": "A tool to retrieve all todo items",
				"inputSchema": GetTodosInputSchema,
			},
			{
				"id":          "todos-update",
				"name":        "todos-update",
				"description": "A tool to update an existing todo item by ID",
				"inputSchema": UpdateTodoInputSchema,
			},
			{
				"id":          "todos-delete",
				"name":        "todos-delete",
				"description": "A tool to delete a todo item by ID",
				"inputSchema": DeleteTodoInputSchema,
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
		case "todos-add":
			title, _ := requestBody.Arguments["title"].(string)
			dueDate, _ := requestBody.Arguments["due_date"].(string)
			var duePtr *time.Time
			if dueDate != "" {
				t, err := time.Parse(time.RFC3339, dueDate)
				if err != nil {
					c.JSON(http.StatusBadRequest, gin.H{"error": "invalid due_date format; expected RFC3339 date-time"})
					return
				}
				duePtr = &t
			}

			input := CreateTodoInput{
				Title:   title,
				DueDate: duePtr,
			}
			result, _, err = CreateTodo(c.Request.Context(), nil, input)

		case "todos-list":
			input := GetTodosInput{}
			result, _, err = GetTodos(c.Request.Context(), nil, input)

		case "todos-update":
			// JSON unmarshals numbers as float64
			idFloat, _ := requestBody.Arguments["id"].(float64)
			title, _ := requestBody.Arguments["title"].(string)
			dueDate, _ := requestBody.Arguments["due_date"].(string)
			var duePtr *time.Time
			if dueDate != "" {
				t, err := time.Parse(time.RFC3339, dueDate)
				if err != nil {
					c.JSON(http.StatusBadRequest, gin.H{"error": "invalid due_date format; expected RFC3339 date-time"})
					return
				}
				duePtr = &t
			}
			input := UpdateTodoInput{
				ID:      int32(idFloat),
				Title:   title,
				DueDate: duePtr,
			}
			result, _, err = UpdateTodo(c.Request.Context(), nil, input)

		case "todos-delete":
			// JSON unmarshals numbers as float64
			idFloat, _ := requestBody.Arguments["id"].(float64)
			input := DeleteTodoInput{ID: int32(idFloat)}
			result, _, err = DeleteTodo(c.Request.Context(), nil, input)

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
		log.Println("Received schema request")
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
		log.Println("Received capabilities request")
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
