"""Todo MCP Client - Python client for interacting with todo-mcp server"""

from .todoclientmcp import TodoMCPClient, Todo, MCPError, create_client

__version__ = "1.0.0"

__all__ = [
    'TodoMCPClient',
    'Todo',
    'MCPError',
    'create_client',
]
