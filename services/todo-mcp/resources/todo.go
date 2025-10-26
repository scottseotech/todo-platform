package resources

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/url"

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

func ErrorReadResourceResult(req *mcp.ReadResourceRequest, message string) (*mcp.ReadResourceResult, error) {
	return &mcp.ReadResourceResult{
		Contents: []*mcp.ResourceContents{
			{URI: req.Params.URI, MIMEType: "application/json", Text: fmt.Sprintf(`{"error": %q}`, message)},
		},
	}, nil
}

func TodosWithDueDate(ctx context.Context, req *mcp.ReadResourceRequest) (*mcp.ReadResourceResult, error) {
	log.Printf("Reading todos with due date resource: %s", req.Params.URI)
	u, err := url.Parse(req.Params.URI)
	if err != nil {
		return nil, err
	}
	if u.Scheme != "todos" {
		return nil, fmt.Errorf("wrong scheme: %q", u.Scheme)
	}
	key := u.Host + u.Path
	log.Printf("Embedded resource key: %s", key)

	resp, err := client.GetTodosWithResponse(ctx)
	if err != nil {
		return nil, fmt.Errorf("error fetching todos: %v", err)
	}

	if resp.StatusCode() != 200 {
		return nil, fmt.Errorf("received status code %d", resp.StatusCode())
	}

	// Parse the response body
	todos := resp.JSON200
	if todos == nil || len(*todos) == 0 {
		return ErrorReadResourceResult(req, "No todos found")
	}

	TodosWithDueDate := []todoclient.Todo{}
	for _, todo := range *todos {
		if todo.DueDate != nil {
			TodosWithDueDate = append(TodosWithDueDate, todo)
		}
	}

	// Format todos as JSON
	todosJSON, err := json.MarshalIndent(TodosWithDueDate, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("error formatting todos: %v", err)
	}

	return &mcp.ReadResourceResult{
		Contents: []*mcp.ResourceContents{
			{URI: req.Params.URI, MIMEType: "application/json", Text: string(todosJSON)},
		},
	}, nil
}
