#!/usr/bin/env python3
"""
Example usage of the Todo MCP Client.

Make sure the todo-mcp server is running on port 8081 before running this script.
"""

import logging
from todoclientmcp import TodoMCPClient, MCPError

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main example function demonstrating the MCP client"""

    print("=" * 60)
    print("Todo MCP Client Example")
    print("=" * 60)
    print()

    # Create client and connect
    client = TodoMCPClient("http://localhost:8081")

    try:
        print("Connecting to MCP server...")
        client.connect()
        print("✓ Connected successfully\n")

        # List available tools
        print("Available tools:")
        tools = client.list_tools()
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
        print()

        # Add some todos
        print("Adding todos...")
        result1 = client.add_todo("Write MCP client documentation")
        print(f"  ✓ {result1}")

        result2 = client.add_todo("Test MCP SSE transport")
        print(f"  ✓ {result2}")

        result3 = client.add_todo("Deploy todo-mcp to production")
        print(f"  ✓ {result3}")
        print()

        # List all todos
        print("Current todos:")
        todos = client.get_todos()
        for todo in todos:
            print(f"  [{todo.id}] {todo.title}")
            print(f"      Created: {todo.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Update a todo
        if todos:
            first_todo = todos[0]
            print(f"Updating todo #{first_todo.id}...")
            result = client.update_todo(
                first_todo.id,
                title=f"{first_todo.title} (UPDATED)"
            )
            print(f"  ✓ {result}")
            print()

        # List todos again to see the update
        print("After update:")
        todos = client.get_todos()
        for todo in todos:
            print(f"  [{todo.id}] {todo.title}")
        print()

        # Delete a todo
        if todos and len(todos) > 1:
            second_todo = todos[1]
            print(f"Deleting todo #{second_todo.id}...")
            result = client.delete_todo(second_todo.id)
            print(f"  ✓ {result}")
            print()

        # Final list
        print("Final todo list:")
        todos = client.get_todos()
        if todos:
            for todo in todos:
                print(f"  [{todo.id}] {todo.title}")
        else:
            print("  (no todos)")
        print()

        print("✓ Example completed successfully!")

    except MCPError as e:
        logger.error(f"MCP Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        print("\nDisconnecting...")
        client.disconnect()
        print("✓ Disconnected")

    return 0


def context_manager_example():
    """Example using context manager for automatic connection/disconnection"""

    print("\n" + "=" * 60)
    print("Context Manager Example")
    print("=" * 60)
    print()

    try:
        with TodoMCPClient("http://localhost:8081") as client:
            # Add a todo
            client.add_todo("Test context manager")

            # List todos
            todos = client.get_todos()
            print("Todos from context manager:")
            for todo in todos:
                print(f"  [{todo.id}] {todo.title}")
            print()

        print("✓ Context manager automatically disconnected")

    except MCPError as e:
        logger.error(f"MCP Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()

    if exit_code == 0:
        exit_code = context_manager_example()

    exit(exit_code)
