package handlers

import (
	"context"
	"fmt"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	todoclient "github.com/scottseotech/todo-platform/clients/todo-client-go"
	"github.com/scottseotech/todo-platform/services/todo-mcp/config"
)

var client *todoclient.Client

func init() {
	cfg := config.Load()
	var err error
	client, err = todoclient.NewClient(cfg.TodoAPIURL)
	if err != nil {
		panic(err)
	}
}

type TodoCreateInput struct {
	Title   string `json:"title"`
	DueDate string `json:"due_date,omitempty"`
}

func TodoCreate(ctx context.Context, req *mcp.CallToolRequest, input TodoCreateInput) (*mcp.CallToolResult, any, error) {
	if input.Title == "" {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: "Error: title parameter is required and must be a non-empty string"},
			},
			IsError: true,
		}, nil, nil
	}

	createTodoRequest := todoclient.CreateTodoRequest{
		Title:   input.Title,
		DueDate: nil,
	}

	_, err := client.CreateTodo(ctx, createTodoRequest)
	if err != nil {
		panic(err)
	}

	textResponse := fmt.Sprintf("Added todo: %s", input.Title)

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: textResponse},
		},
	}, nil, nil
}
