package handlers

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	todoclient "github.com/scottseotech/todo-platform/clients/todo-client-go"
	"github.com/scottseotech/todo-platform/services/todo-mcp/config"
)

var client *todoclient.ClientWithResponses

func init() {
	cfg := config.Load()
	var err error
	client, err = todoclient.NewClientWithResponses(cfg.TodoAPIURL)
	if err != nil {
		panic(err)
	}
}

type CreateTodoInput struct {
	Title   string `json:"title"`
	DueDate string `json:"due_date,omitempty"`
}

func CreateTodo(ctx context.Context, req *mcp.CallToolRequest, input CreateTodoInput) (*mcp.CallToolResult, any, error) {
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

	resp, err := client.CreateTodoWithResponse(ctx, createTodoRequest)
	if err != nil {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error creating todo: %v", err)},
			},
			IsError: true,
		}, nil, nil
	}

	if resp.StatusCode() != 201 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error: received status code %d", resp.StatusCode())},
			},
			IsError: true,
		}, nil, nil
	}

	textResponse := fmt.Sprintf("Added todo: %s", input.Title)

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: textResponse},
		},
	}, nil, nil
}

// GetTodosInput defines the input parameters for the get_todos tool
type GetTodosInput struct {
	// No input parameters needed
}

// GetTodos retrieves all todo items
func GetTodos(ctx context.Context, req *mcp.CallToolRequest, input GetTodosInput) (*mcp.CallToolResult, any, error) {
	resp, err := client.GetTodosWithResponse(ctx)
	if err != nil {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error fetching todos: %v", err)},
			},
			IsError: true,
		}, nil, nil
	}

	if resp.StatusCode() != 200 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error: received status code %d", resp.StatusCode())},
			},
			IsError: true,
		}, nil, nil
	}

	// Parse the response body
	todos := resp.JSON200
	if todos == nil || len(*todos) == 0 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: "No todos found"},
			},
		}, nil, nil
	}

	// Format todos as JSON
	todosJSON, err := json.MarshalIndent(todos, "", "  ")
	if err != nil {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error formatting todos: %v", err)},
			},
			IsError: true,
		}, nil, nil
	}

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: fmt.Sprintf("Found %d todos:\n%s", len(*todos), string(todosJSON))},
		},
	}, nil, nil
}

// UpdateTodoInput defines the input parameters for the update_todo tool
type UpdateTodoInput struct {
	ID      int32  `json:"id"`
	Title   string `json:"title,omitempty"`
	DueDate string `json:"due_date,omitempty"`
}

// UpdateTodo updates an existing todo item
func UpdateTodo(ctx context.Context, req *mcp.CallToolRequest, input UpdateTodoInput) (*mcp.CallToolResult, any, error) {
	if input.ID <= 0 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: "Error: id parameter is required and must be greater than 0"},
			},
			IsError: true,
		}, nil, nil
	}

	// Build update request
	updateRequest := todoclient.UpdateTodoRequest{}

	if input.Title != "" {
		updateRequest.Title = &input.Title
	}

	// Note: DueDate handling would require parsing the string to time.Time
	// For now, we'll leave it as nil unless explicitly needed

	resp, err := client.UpdateTodoWithResponse(ctx, input.ID, updateRequest)
	if err != nil {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error updating todo: %v", err)},
			},
			IsError: true,
		}, nil, nil
	}

	if resp.StatusCode() == 404 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Todo with id %d not found", input.ID)},
			},
			IsError: true,
		}, nil, nil
	}

	if resp.StatusCode() != 200 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error: received status code %d", resp.StatusCode())},
			},
			IsError: true,
		}, nil, nil
	}

	textResponse := fmt.Sprintf("Updated todo #%d", input.ID)
	if input.Title != "" {
		textResponse += fmt.Sprintf(" with title: %s", input.Title)
	}

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: textResponse},
		},
	}, nil, nil
}

// DeleteTodoInput defines the input parameters for the delete_todo tool
type DeleteTodoInput struct {
	ID int32 `json:"id"`
}

// DeleteTodo deletes a todo item by ID
func DeleteTodo(ctx context.Context, req *mcp.CallToolRequest, input DeleteTodoInput) (*mcp.CallToolResult, any, error) {
	if input.ID <= 0 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: "Error: id parameter is required and must be greater than 0"},
			},
			IsError: true,
		}, nil, nil
	}

	resp, err := client.DeleteTodoWithResponse(ctx, input.ID)
	if err != nil {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error deleting todo: %v", err)},
			},
			IsError: true,
		}, nil, nil
	}

	if resp.StatusCode() == 404 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Todo with id %d not found", input.ID)},
			},
			IsError: true,
		}, nil, nil
	}

	if resp.StatusCode() != 200 {
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error: received status code %d", resp.StatusCode())},
			},
			IsError: true,
		}, nil, nil
	}

	textResponse := fmt.Sprintf("Successfully deleted todo #%d", input.ID)

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: textResponse},
		},
	}, nil, nil
}
