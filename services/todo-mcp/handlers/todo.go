package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	todoclient "github.com/scottseotech/todo-platform/clients/todo-client-go"
	"github.com/scottseotech/todo-platform/services/todo-mcp/config"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
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
	Title   string     `json:"title"`
	DueDate *time.Time `json:"due_date,omitempty"`
}

func CreateTodo(ctx context.Context, req *mcp.CallToolRequest, input CreateTodoInput) (*mcp.CallToolResult, any, error) {
	// Start tracing span for MCP tool call
	tracer := otel.Tracer("todo-mcp")
	ctx, span := tracer.Start(ctx, "mcp.tool.CreateTodo")
	defer span.End()

	// Add attributes about the MCP tool call
	span.SetAttributes(
		attribute.String("mcp.tool.name", "todos-add"),
		attribute.String("mcp.tool.type", "tool"),
		attribute.String("todo.title", input.Title),
	)

	// Validation
	if input.Title == "" {
		err := fmt.Errorf("title parameter is required")
		span.RecordError(err)
		span.SetStatus(codes.Error, "Validation failed: missing title")
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: "Error: title parameter is required and must be a non-empty string"},
			},
			IsError: true,
		}, nil, nil
	}

	// Add due date attribute if present
	if input.DueDate != nil {
		span.SetAttributes(attribute.String("todo.due_date", input.DueDate.Format(time.RFC3339)))
	}

	createTodoRequest := todoclient.CreateTodoRequest{
		Title:   input.Title,
		DueDate: input.DueDate,
	}

	// Make HTTP call to todo-api (context propagates trace!)
	resp, err := client.CreateTodoWithResponse(ctx, createTodoRequest)
	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, "HTTP request to todo-api failed")
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error creating todo: %v", err)},
			},
			IsError: true,
		}, nil, nil
	}

	// Check status code
	span.SetAttributes(attribute.Int("http.status_code", resp.StatusCode()))

	if resp.StatusCode() != 201 {
		err := fmt.Errorf("received status code %d", resp.StatusCode())
		span.RecordError(err)
		span.SetStatus(codes.Error, "Non-201 status code from todo-api")
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: fmt.Sprintf("Error: received status code %d", resp.StatusCode())},
			},
			IsError: true,
		}, nil, nil
	}

	// Add result attributes
	if resp.JSON201 != nil {
		span.SetAttributes(
			attribute.Int64("todo.id", int64(resp.JSON201.Id)),
			attribute.String("todo.created_at", resp.JSON201.CreatedAt.String()),
		)
	}

	span.SetStatus(codes.Ok, "Todo created successfully")
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

func ErrorCallToolResult(message string) *mcp.CallToolResult {
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: message},
		},
		IsError: true,
	}
}

// GetTodos retrieves all todo items
func GetTodos(ctx context.Context, req *mcp.CallToolRequest, input GetTodosInput) (*mcp.CallToolResult, any, error) {
	resp, err := client.GetTodosWithResponse(ctx)
	if err != nil {
		return ErrorCallToolResult(fmt.Sprintf("Error fetching todos: %v", err)), nil, nil
	}

	if resp.StatusCode() != 200 {
		return ErrorCallToolResult(fmt.Sprintf("Error: received status code %d", resp.StatusCode())), nil, nil
	}

	// Parse the response body
	todos := resp.JSON200
	if todos == nil || len(*todos) == 0 {
		return ErrorCallToolResult("No todos found"), nil, nil
	}

	// Format todos as JSON
	todosJSON, err := json.MarshalIndent(todos, "", "  ")
	if err != nil {
		return ErrorCallToolResult(fmt.Sprintf("Error formatting todos: %v", err)), nil, nil
	}

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: string(todosJSON)},
		},
	}, nil, nil
}

// UpdateTodoInput defines the input parameters for the update_todo tool
type UpdateTodoInput struct {
	ID      int32      `json:"id"`
	Title   string     `json:"title,omitempty"`
	DueDate *time.Time `json:"due_date,omitempty"`
}

// UpdateTodo updates an existing todo item
func UpdateTodo(ctx context.Context, req *mcp.CallToolRequest, input UpdateTodoInput) (*mcp.CallToolResult, any, error) {
	if input.ID <= 0 {
		return ErrorCallToolResult("Error: id parameter is required and must be greater than 0"), nil, nil
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
		return ErrorCallToolResult(fmt.Sprintf("Error updating todo: %v", err)), nil, nil
	}

	if resp.StatusCode() == 404 {
		return ErrorCallToolResult(fmt.Sprintf("Todo with id %d not found", input.ID)), nil, nil
	}

	if resp.StatusCode() != 200 {
		return ErrorCallToolResult(fmt.Sprintf("Error: received status code %d", resp.StatusCode())), nil, nil
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
