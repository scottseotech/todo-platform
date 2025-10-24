"""
Todo API Client for Python

A simple HTTP client for interacting with the Todo API.
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime


class Todo:
    """Represents a todo item."""

    def __init__(self, id: int, title: str, created_at: str, updated_at: str,
                 due_date: Optional[str] = None):
        self.id = id
        self.title = title
        self.due_date = due_date
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Todo':
        """Create a Todo from a dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            due_date=data.get('due_date'),
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Todo to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'due_date': self.due_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def __repr__(self) -> str:
        return f"Todo(id={self.id}, title='{self.title}', due_date={self.due_date})"


class TodoClient:
    """Client for interacting with the Todo API."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the Todo API client.

        Args:
            base_url: The base URL of the Todo API (default: http://localhost:8080)
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1"
        self.session = requests.Session()

    def health_check(self) -> Dict[str, str]:
        """
        Check the health status of the API.

        Returns:
            Dictionary with 'status' key

        Raises:
            requests.HTTPError: If the request fails
        """
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_todos(self) -> List[Todo]:
        """
        Get all todos.

        Returns:
            List of Todo objects

        Raises:
            requests.HTTPError: If the request fails
        """
        response = self.session.get(f"{self.api_base}/todos")
        response.raise_for_status()
        data = response.json()
        return [Todo.from_dict(item) for item in data]

    def get_todo(self, todo_id: int) -> Todo:
        """
        Get a specific todo by ID.

        Args:
            todo_id: The ID of the todo to retrieve

        Returns:
            Todo object

        Raises:
            requests.HTTPError: If the request fails (e.g., 404 if not found)
        """
        response = self.session.get(f"{self.api_base}/todos/{todo_id}")
        response.raise_for_status()
        return Todo.from_dict(response.json())

    def create_todo(self, title: str, due_date: Optional[str] = None) -> Todo:
        """
        Create a new todo.

        Args:
            title: The title of the todo
            due_date: Optional due date in ISO 8601 format (e.g., "2024-12-31T23:59:59Z")

        Returns:
            Created Todo object

        Raises:
            requests.HTTPError: If the request fails
        """
        payload = {"title": title}
        if due_date:
            payload["due_date"] = due_date

        response = self.session.post(f"{self.api_base}/todos", json=payload)
        response.raise_for_status()
        return Todo.from_dict(response.json())

    def update_todo(self, todo_id: int, title: Optional[str] = None,
                    due_date: Optional[str] = None) -> Todo:
        """
        Update an existing todo.

        Args:
            todo_id: The ID of the todo to update
            title: Optional new title
            due_date: Optional new due date in ISO 8601 format

        Returns:
            Updated Todo object

        Raises:
            requests.HTTPError: If the request fails (e.g., 404 if not found)
        """
        payload = {}
        if title is not None:
            payload["title"] = title
        if due_date is not None:
            payload["due_date"] = due_date

        response = self.session.put(f"{self.api_base}/todos/{todo_id}", json=payload)
        response.raise_for_status()
        return Todo.from_dict(response.json())

    def delete_todo(self, todo_id: int) -> Dict[str, str]:
        """
        Delete a todo by ID.

        Args:
            todo_id: The ID of the todo to delete

        Returns:
            Dictionary with 'message' key confirming deletion

        Raises:
            requests.HTTPError: If the request fails (e.g., 404 if not found)
        """
        response = self.session.delete(f"{self.api_base}/todos/{todo_id}")
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    # Using the client as a context manager
    with TodoClient("http://localhost:8080") as client:
        # Health check
        health = client.health_check()
        print(f"API Health: {health}")

        # Create a todo
        new_todo = client.create_todo("Buy groceries", "2024-12-31T23:59:59Z")
        print(f"Created: {new_todo}")

        # Get all todos
        todos = client.get_todos()
        print(f"All todos: {todos}")

        # Get a specific todo
        if todos:
            todo = client.get_todo(todos[0].id)
            print(f"Got todo: {todo}")

            # Update the todo
            updated = client.update_todo(todo.id, title="Buy groceries and cook dinner")
            print(f"Updated: {updated}")

            # Delete the todo
            result = client.delete_todo(todo.id)
            print(f"Deleted: {result}")
