# Todo API Python Client

## Usage

### Basic Example

```python
from todoclient import TodoClient

# Create a client
client = TodoClient("http://localhost:8080")

# Health check
health = client.health_check()
print(health)  # {'status': 'healthy'}

# Create a todo
todo = client.create_todo("Buy groceries", due_date="2024-12-31T23:59:59Z")
print(todo)  # Todo(id=1, title='Buy groceries', due_date='2024-12-31T23:59:59Z')

# Get all todos
todos = client.get_todos()
for todo in todos:
    print(todo)

# Get a specific todo
todo = client.get_todo(1)
print(todo)

# Update a todo
updated_todo = client.update_todo(1, title="Buy groceries and cook dinner")
print(updated_todo)

# Delete a todo
result = client.delete_todo(1)
print(result)  # {'message': 'Todo deleted successfully!'}

# Close the client
client.close()
```

### Using Context Manager

```python
from todoclient import TodoClient

with TodoClient("http://localhost:8080") as client:
    # Health check
    health = client.health_check()
    print(f"API Health: {health}")

    # Create a todo
    new_todo = client.create_todo("Buy groceries")
    print(f"Created: {new_todo}")

    # Get all todos
    todos = client.get_todos()
    print(f"Total todos: {len(todos)}")
```

## Error Handling

The client raises `requests.HTTPError` for failed requests:

```python
from todoclient import TodoClient
import requests

client = TodoClient()

try:
    todo = client.get_todo(999)  # Non-existent ID
except requests.HTTPError as e:
    print(f"Error: {e}")
    print(f"Status code: {e.response.status_code}")
```