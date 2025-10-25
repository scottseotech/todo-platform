package main

import (
	"context"
	_ "embed"
	"fmt"
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
	// Content: &mcp.TextContent{Text: "" +
	// 	"You can use the following tools:" +
	// 	"- `todos-list` → list current tasks." +
	// 	"- `todos-add(title, due_date?)` → add a new todo item." +
	// 	"- `todos-update(id, title)` → update a todo item." +
	// 	"- `todos-delete(id)` → deletes a todo item." +
	// 	"When users speak naturally, translate their intent into one of these tool invocations.",
	// },

	addPromptHandler := func(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
		return &mcp.GetPromptResult{
			Messages: []*mcp.PromptMessage{
				{
					Role:    "system",
					Content: &mcp.TextContent{Text: fmt.Sprintf("#todos-add(%s, %s)", req.Params.Arguments["title"], req.Params.Arguments["due_date"])},
				},
			},
		}, nil
	}

	updatePromptHandler := func(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
		return &mcp.GetPromptResult{
			Messages: []*mcp.PromptMessage{
				{
					Role:    "system",
					Content: &mcp.TextContent{Text: fmt.Sprintf("#todos-update(%s, %s, %s)", req.Params.Arguments["id"], req.Params.Arguments["title"], req.Params.Arguments["due_date"])},
				},
			},
		}, nil
	}

	srv.AddPrompt(&mcp.Prompt{
		Name:  "todos-add",
		Title: "Add a new todo item",
		Arguments: []*mcp.PromptArgument{
			{
				Name:     "title",
				Title:    "Title of the todo item",
				Required: true,
			},
			{
				Name:     "due_date",
				Title:    "Due date of the todo item (optional)",
				Required: false,
			},
		},
	}, addPromptHandler)

	srv.AddPrompt(&mcp.Prompt{
		Name:  "todos-update",
		Title: "Update an existing todo item",
		Arguments: []*mcp.PromptArgument{
			{
				Name:     "id",
				Title:    "ID of the todo item",
				Required: true,
			},
			{
				Name:     "title",
				Title:    "Title of the todo item",
				Required: true,
			},
			{
				Name:     "due_date",
				Title:    "Due date of the todo item (optional)",
				Required: false,
			},
		},
	}, updatePromptHandler)

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
