# Todo API Go Client

Generated Go client for the Todo API using oapi-codegen.

## Installation

```bash
go get github.com/scottseotech/todo-platform/clients/todo-client-go
```

## Usage

```go
import (
    "context"
    "fmt"
    todoclient "github.com/scottseotech/todo-platform/clients/todo-client-go"
)

func main() {
    client, err := todoclient.NewClient("http://localhost:8080")
    if err != nil {
        panic(err)
    }

    // Get all todos
    todos, err := client.GetTodos(context.Background())
    if err != nil {
        panic(err)
    }

    fmt.Printf("Todos: %+v\n", todos)
}
```

## Regenerating the Client

To regenerate the client after OpenAPI spec changes:

```bash
# Install oapi-codegen
go install github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@latest

# Generate client
oapi-codegen -generate "types,client" -package todoclient -o client.gen.go ../../services/todo-api/openapi.json

# Update dependencies
go mod tidy
```