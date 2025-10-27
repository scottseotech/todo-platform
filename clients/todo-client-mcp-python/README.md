# Todo MCP Client (Python)

Python client library for interacting with the todo-mcp server using the Model Context Protocol (MCP) over SSE transport.

## Installation

From the repository root:

```bash
pip install -e clients/todo-client-mcp-python
```

Or install dependencies directly:

```bash
cd clients/todo-client-mcp-python
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from todoclientmcp import TodoMCPClient

# Create and connect to the server
client = TodoMCPClient("http://localhost:8081")
client.connect()

# Add a todo
result = client.add_todo("Buy groceries")
print(result)

# List all todos
todos = client.get_todos()
for todo in todos:
    print(f"{todo.id}: {todo.title} (created: {todo.created_at})")

# Update a todo
client.update_todo(1, title="Buy groceries and cook dinner")

# Delete a todo
client.delete_todo(1)

# Disconnect when done
client.disconnect()
```

### Context Manager

```python
from todoclientmcp import TodoMCPClient

# Automatically connects and disconnects
with TodoMCPClient("http://localhost:8081") as client:
    todos = client.get_todos()
    for todo in todos:
        print(f"{todo.id}: {todo.title}")
```

### Convenience Function

```python
from todoclientmcp import create_client

# Creates and connects in one call
client = create_client("http://localhost:8081")
todos = client.get_todos()
client.disconnect()
```

## API Reference

### TodoMCPClient

Main client class for interacting with the todo-mcp server.

#### Methods

- `connect()`: Establish connection to the MCP server and initialize the session
- `disconnect()`: Disconnect from the server
- `add_todo(title: str, due_date: Optional[str] = None) -> str`: Add a new todo item
- `get_todos() -> List[Todo]`: Get all todo items
- `update_todo(todo_id: int, title: Optional[str] = None, due_date: Optional[str] = None) -> str`: Update a todo
- `delete_todo(todo_id: int) -> str`: Delete a todo by ID
- `list_tools() -> List[Dict[str, Any]]`: List available MCP tools

### Todo

Data class representing a todo item.

#### Attributes

- `id: int`: Todo ID
- `title: str`: Todo title
- `created_at: datetime`: Creation timestamp
- `updated_at: datetime`: Last update timestamp
- `due_date: Optional[datetime]`: Optional due date

### MCPError

Exception raised for MCP client errors.

## Requirements

- Python 3.8+
- requests >= 2.31.0
- sseclient-py >= 1.8.0

## How It Works

This client uses the Model Context Protocol (MCP) to communicate with the todo-mcp server:

1. **Connection**: Establishes an SSE (Server-Sent Events) connection via GET /sse
2. **Initialization**: Sends an `initialize` JSON-RPC request to start the session
3. **Tool Calls**: Sends `tools/call` JSON-RPC requests via POST /sse?sessionid=<id>
4. **Responses**: Receives responses either as immediate JSON or via SSE event stream

The protocol follows the MCP specification version 2024-11-05.

## Example Script

See `example.py` for a complete working example.

## Development

To run the example:

```bash
# Make sure todo-mcp server is running on port 8081
cd clients/todo-client-mcp-python
python example.py
```

## License

MIT
