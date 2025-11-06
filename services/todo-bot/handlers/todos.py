"""
Todo command handler
"""

import logging
import os
from datetime import datetime
from todoclient import TodoClient
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Configuration
TODO_API_URL = os.environ.get("TODO_API_URL", "http://localhost:8080")

# Initialize the client
client = TodoClient(base_url=TODO_API_URL)


def todo_slash_command(ack, command, respond):
    """
    Handle /todo slash command with subcommands

    Usage examples:
        /todo add Buy groceries
        /todo list
        /todo update 1 Buy milk instead
        /todo delete 1
    """
    # Acknowledge the command request immediately
    ack()

    with tracer.start_as_current_span(
        "todo_slash_command",
        attributes={
            "slack.command": "/todo",
            "slack.user_id": command.get("user_id"),
            "slack.user_name": command.get("user_name"),
        }
    ) as span:
        try:
            # Extract command text
            text = command["text"].strip()
            user_id = command.get("user_id", "unknown")
            user_name = command.get("user_name", "unknown")

            # Parse subcommand
            parts = text.split(maxsplit=1) if text else []

            if not parts:
                # No subcommand - show help
                span.set_attribute("todo.subcommand", "help")
                _show_help(respond)
                return

            subcommand = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            span.set_attribute("todo.subcommand", subcommand)
            span.set_attribute("todo.args", args)

            # Route to appropriate handler
            if subcommand == "add":
                _handle_add(args, user_id, user_name, respond)
            elif subcommand == "list":
                _handle_list(user_id, respond)
            elif subcommand == "update":
                _handle_update(args, user_id, user_name, respond)
            elif subcommand == "delete":
                _handle_delete(args, user_id, user_name, respond)
            else:
                # Backward compatibility: if no subcommand, treat as "add"
                _handle_add(text, user_id, user_name, respond)

            span.set_status(trace.Status(trace.StatusCode.OK))

        except Exception as e:
            logger.error(f"[/todo] Error: {e}", exc_info=True)
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            respond(
                text="❌ Sorry, something went wrong. Please try again.",
                response_type="in_channel"
            )


def _show_help(respond):
    """Show help message"""
    respond(
        text="Todo Bot - Help",
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Todo Bot Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Available commands:*\n\n"
                            "• `/todo add <text>` - Create a new todo\n"
                            "• `/todo list` - List all todos\n"
                            "• `/todo update <id> <text>` - Update a todo\n"
                            "• `/todo delete <id>` - Delete a todo\n\n"
                            "*Examples:*\n"
                            "```/todo add Buy groceries\n"
                            "/todo list\n"
                            "/todo update 1 Buy milk\n"
                            "/todo delete 1```"
                }
            }
        ],
        response_type="in_channel"
    )


def _handle_add(text, user_id, user_name, respond):
    """Handle add subcommand"""
    cleaned_text = text.strip('"\'')

    if not cleaned_text:
        respond(
            text="❌ Please provide a todo item.\n\nUsage: `/todo add <text>`",
            response_type="ephemeral"
        )
        return

    logger.info(f"[/todo add] User: {user_name}, Todo: '{cleaned_text}'")

    # Call Todo API to create the todo
    todo = client.create_todo(title=cleaned_text)
    logger.info(f"[/todo add] Created todo ID: {todo.id}")

    # Respond with success
    respond(
        text=f"Todo added: \"{todo.title}\"",
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Todo Created"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*ID:* {todo.id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Title:* {todo.title}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Added by <@{user_id}> | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ],
        response_type="in_channel"
    )


def _handle_list(user_id, respond):
    """Handle list subcommand"""
    logger.info(f"[/todo list] Fetching todos")

    # Get all todos from API
    todos = client.get_todos()

    if not todos:
        respond(
            text="📭 No todos found. Create one with `/todo add <text>`",
            response_type="ephemeral"
        )
        return

    # Build blocks for each todo
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Your Todos ({len(todos)} items)"
            }
        },
        {
            "type": "divider"
        }
    ]

    for todo in todos:
        blocks.append({
            "type": "section",
            "fields": [
                {
                  "type": "mrkdwn",
                  "text": f"*#{todo.id}* - {todo.title}"
                },                
                {
                    "type": "mrkdwn",
                    "text": f"*Created:* {todo.created_at[:10]}"
                }
            ]
        })

    respond(
        text=f"📋 {len(todos)} todos",
        blocks=blocks,
        response_type="in_channel"
    )


def _handle_update(args, user_id, user_name, respond):
    """Handle update subcommand"""
    parts = args.split(maxsplit=1)

    if len(parts) < 2:
        respond(
            text="❌ Usage: `/todo update <id> <new text>`\n\nExample: `/todo update 1 Buy milk`",
            response_type="ephemeral"
        )
        return

    try:
        todo_id = int(parts[0])
        new_title = parts[1].strip('"\'')

        if not new_title:
            respond(text="❌ Please provide new text for the todo.", response_type="ephemeral")
            return

        logger.info(f"[/todo update] User: {user_name}, ID: {todo_id}, New title: '{new_title}'")

        # Update via API
        updated_todo = client.update_todo(todo_id, title=new_title)

        respond(
            text=f"Todo #{todo_id} updated",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Todo Updated"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*ID:* {updated_todo.id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Title:* {updated_todo.title}"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Updated by <@{user_id}> | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    ]
                }
            ],
            response_type="in_channel"
        )

    except ValueError:
        respond(text="❌ Invalid todo ID. Must be a number.", response_type="ephemeral")
    except Exception as e:
        logger.error(f"[/todo update] Error: {e}", exc_info=True)
        respond(text=f"❌ Failed to update todo: {str(e)}", response_type="ephemeral")


def _handle_delete(args, user_id, user_name, respond):
    """Handle delete subcommand"""
    if not args:
        respond(
            text="❌ Usage: `/todo delete <id>`\n\nExample: `/todo delete 1`",
            response_type="ephemeral"
        )
        return

    try:
        todo_id = int(args.strip())

        logger.info(f"[/todo delete] User: {user_name}, ID: {todo_id}")

        # Delete via API
        client.delete_todo(todo_id)

        respond(
            text=f"Todo #{todo_id} deleted",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Todo Deleted"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Todo *#{todo_id}* has been deleted."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Deleted by <@{user_id}> | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    ]
                }
            ],
            response_type="in_channel"
        )

    except ValueError:
        respond(text="❌ Invalid todo ID. Must be a number.", response_type="ephemeral")
    except Exception as e:
        logger.error(f"[/todo delete] Error: {e}", exc_info=True)
        respond(text=f"❌ Failed to delete todo: {str(e)}", response_type="ephemeral")
