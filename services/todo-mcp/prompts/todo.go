package prompts

import (
	"context"
	"fmt"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func AddTodo(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	return &mcp.GetPromptResult{
		Messages: []*mcp.PromptMessage{
			{
				Role:    "system",
				Content: &mcp.TextContent{Text: fmt.Sprintf("#todos-add(%s, %s)", req.Params.Arguments["title"], req.Params.Arguments["due_date"])},
			},
		},
	}, nil
}

func AddTodoArguments() []*mcp.PromptArgument {
	return []*mcp.PromptArgument{
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
	}
}

func UpdateTodo(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	return &mcp.GetPromptResult{
		Messages: []*mcp.PromptMessage{
			{
				Role:    "system",
				Content: &mcp.TextContent{Text: fmt.Sprintf("#todos-update(%s, %s, %s)", req.Params.Arguments["id"], req.Params.Arguments["title"], req.Params.Arguments["due_date"])},
			},
		},
	}, nil
}

func UpdateTodoArguments() []*mcp.PromptArgument {
	return []*mcp.PromptArgument{
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
	}
}
