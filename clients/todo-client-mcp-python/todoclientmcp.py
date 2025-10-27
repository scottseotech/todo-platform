"""
Todo MCP Client - Python client for interacting with todo-mcp server via SSE transport.

This client uses the Model Context Protocol (MCP) to communicate with the todo-mcp server.
"""

import json
import logging
import uuid
import threading
import queue
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import requests
from sseclient import SSEClient

logger = logging.getLogger(__name__)


@dataclass
class Todo:
    """Represents a todo item"""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Todo':
        """Create Todo from dictionary"""
        return cls(
            id=data['id'],
            title=data['title'],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
            due_date=datetime.fromisoformat(data['due_date'].replace('Z', '+00:00')) if data.get('due_date') else None
        )


class MCPError(Exception):
    """Base exception for MCP client errors"""
    pass


class TodoMCPClient:
    """
    MCP client for todo-mcp server using SSE transport.

    Example usage:
        client = TodoMCPClient("http://localhost:8081")
        client.connect()

        # Add a todo
        result = client.add_todo("Buy groceries")
        print(result)

        # List todos
        todos = client.get_todos()
        for todo in todos:
            print(f"{todo.id}: {todo.title}")

        # Update a todo
        client.update_todo(1, title="Buy groceries and cook dinner")

        # Delete a todo
        client.delete_todo(1)

        client.disconnect()
    """

    def __init__(self, base_url: str = "http://localhost:8081"):
        """
        Initialize MCP client.

        Args:
            base_url: Base URL of the todo-mcp server (e.g., "http://localhost:8081")
        """
        self.base_url = base_url.rstrip('/')
        self.sse_url = f"{self.base_url}/sse"
        self.session_id: Optional[str] = None
        self.sse_client: Optional[SSEClient] = None
        self.initialized = False
        self.http_session = requests.Session()  # Reuse same session for all requests
        self.sse_thread: Optional[threading.Thread] = None
        self.response_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()

    def connect(self) -> None:
        """
        Connect to the MCP server and initialize the session.
        This establishes the SSE connection and sends the initialize request.
        """
        # Establish SSE connection (GET /sse)
        logger.info(f"Connecting to MCP server at {self.sse_url}")
        headers = {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
        }

        response = self.http_session.get(self.sse_url, headers=headers, stream=True)
        if response.status_code != 200:
            raise MCPError(f"Failed to connect to SSE endpoint: {response.status_code}")

        self.sse_client = SSEClient(response)

        # Start background thread to read SSE events and extract session ID
        self.sse_thread = threading.Thread(target=self._sse_reader, daemon=True)
        self.sse_thread.start()

        # Wait for the endpoint event to be processed by background thread
        logger.info("Waiting for endpoint event from server...")
        timeout = 10.0
        start_time = time.time()
        while not self.session_id:
            if time.time() - start_time > timeout:
                raise MCPError("Timeout waiting for endpoint event")
            time.sleep(0.01)

        logger.info(f"SSE connection established with session {self.session_id}")

        # Send initialize request
        self._initialize()

    def _sse_reader(self):
        """Background thread that reads SSE events and queues responses"""
        try:
            for event in self.sse_client.events():
                if self.stop_event.is_set():
                    break

                # Handle endpoint event (contains session ID)
                if event.event == 'endpoint' and event.data:
                    endpoint_url = event.data.strip()
                    logger.debug(f"Received endpoint: {endpoint_url}")
                    if '?sessionid=' in endpoint_url:
                        self.session_id = endpoint_url.split('?sessionid=')[1]
                        logger.debug(f"Extracted session ID: {self.session_id}")
                    continue

                # Handle message events (JSON-RPC responses)
                if event.event == 'message' and event.data:
                    try:
                        data = json.loads(event.data)
                        logger.debug(f"SSE message received: {data}")
                        self.response_queue.put(data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE message: {event.data}")
        except Exception as e:
            logger.error(f"SSE reader thread error: {e}", exc_info=True)

    def _initialize(self) -> None:
        """Send initialize request to the MCP server"""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "todo-client-mcp-python",
                    "version": "1.0.0"
                }
            }
        }

        response = self._send_request(init_request)
        if 'error' in response:
            raise MCPError(f"Initialize failed: {response['error']}")

        self.initialized = True
        logger.info("MCP session initialized successfully")

    def _send_request(self, request: dict) -> dict:
        """
        Send a JSON-RPC request via POST to the SSE endpoint.

        Args:
            request: JSON-RPC request object

        Returns:
            JSON-RPC response object
        """
        if not self.session_id:
            raise MCPError("Not connected. Call connect() first.")

        # POST to /sse?sessionid=<session_id>
        url = f"{self.sse_url}?sessionid={self.session_id}"
        headers = {
            'Content-Type': 'application/json',
        }

        logger.info(f"Posting to URL: {url}")
        logger.debug(f"Sending request: {json.dumps(request, indent=2)}")
        response = self.http_session.post(url, json=request, headers=headers)
        logger.info(f"POST response status: {response.status_code}")

        if response.status_code not in [200, 202]:
            raise MCPError(f"Request failed with status {response.status_code}: {response.text}")

        # For SSE transport, response comes through the SSE stream, not the POST response
        # The POST just accepts the request (202 Accepted)
        logger.debug("Request sent, reading response from SSE stream")
        return self._read_sse_response()

    def _read_sse_response(self, timeout: float = 30.0) -> dict:
        """Read the next JSON-RPC response from the SSE stream (via background thread queue)"""
        try:
            response = self.response_queue.get(timeout=timeout)
            return response
        except queue.Empty:
            raise MCPError(f"No response received within {timeout} seconds")

    def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result content
        """
        if not self.initialized:
            raise MCPError("Client not initialized. Call connect() first.")

        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = self._send_request(request)

        if 'error' in response:
            raise MCPError(f"Tool call failed: {response['error']}")

        # Extract content from result
        result = response.get('result', {})
        content = result.get('content', [])

        if not content:
            raise MCPError("No content in tool response")

        # Return the first content item's text
        return content[0].get('text', '')

    def add_todo(self, title: str, due_date: Optional[str] = None) -> str:
        """
        Add a new todo item.

        Args:
            title: Title of the todo item
            due_date: Optional due date in ISO 8601 format (e.g., "2025-10-26T12:00:00Z")

        Returns:
            Success message
        """
        arguments = {"title": title}
        if due_date:
            arguments["due_date"] = due_date

        return self.call_tool("add_todo", arguments)

    def get_todos(self) -> List[Todo]:
        """
        Get all todo items.

        Returns:
            List of Todo objects
        """
        result = self.call_tool("get_todos", {})

        # Parse the response - it might be JSON or formatted text
        try:
            # Try to parse as JSON array
            todos_data = json.loads(result)
            return [Todo.from_dict(todo) for todo in todos_data]
        except json.JSONDecodeError:
            # Response might be formatted text like "Found 2 todos:\n[...]"
            # Try to extract JSON from the text
            if '\n' in result:
                # Split and try to parse the JSON part
                parts = result.split('\n', 1)
                if len(parts) > 1:
                    todos_data = json.loads(parts[1])
                    return [Todo.from_dict(todo) for todo in todos_data]
            raise MCPError(f"Failed to parse todos response: {result}")

    def update_todo(self, todo_id: int, title: Optional[str] = None, due_date: Optional[str] = None) -> str:
        """
        Update an existing todo item.

        Args:
            todo_id: ID of the todo item to update
            title: New title (optional)
            due_date: New due date in ISO 8601 format (optional)

        Returns:
            Success message
        """
        arguments = {"id": todo_id}
        if title:
            arguments["title"] = title
        if due_date:
            arguments["due_date"] = due_date

        return self.call_tool("update_todo", arguments)

    def delete_todo(self, todo_id: int) -> str:
        """
        Delete a todo item.

        Args:
            todo_id: ID of the todo item to delete

        Returns:
            Success message
        """
        return self.call_tool("delete_todo", {"id": todo_id})

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.

        Returns:
            List of tool definitions
        """
        if not self.initialized:
            raise MCPError("Client not initialized. Call connect() first.")

        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }

        response = self._send_request(request)

        if 'error' in response:
            raise MCPError(f"tools/list failed: {response['error']}")

        return response.get('result', {}).get('tools', [])

    def disconnect(self) -> None:
        """Disconnect from the MCP server"""
        logger.info("Disconnecting from MCP server")

        # Stop SSE reader thread
        self.stop_event.set()
        if self.sse_thread and self.sse_thread.is_alive():
            self.sse_thread.join(timeout=2.0)

        if self.sse_client:
            self.sse_client = None

        self.session_id = None
        self.initialized = False

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Convenience function
def create_client(base_url: str = "http://localhost:8081") -> TodoMCPClient:
    """
    Create and return a connected TodoMCPClient.

    Args:
        base_url: Base URL of the todo-mcp server

    Returns:
        Connected TodoMCPClient instance
    """
    client = TodoMCPClient(base_url)
    client.connect()
    return client
