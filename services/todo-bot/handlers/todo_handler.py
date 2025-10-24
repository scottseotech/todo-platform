"""
Todo command handler
"""

import logging
import os
from datetime import datetime
from todoclient import TodoClient

logger = logging.getLogger(__name__)

# Configuration
TODO_API_URL = os.environ.get("TODO_API_URL", "http://localhost:8080")

# Initialize the client
client = TodoClient(base_url=TODO_API_URL)


def handle_todo_command(ack, command, respond):
    """
    Handle /todo slash command

    Usage examples:
        /todo "Buy groceries"
        /todo Buy groceries
    """
    # Acknowledge the command request immediately
    ack()

    try:
        # Extract todo text from command
        todo_text = command["text"].strip()

        # Validate input
        if not todo_text:
            respond(
                text="❌ Please provide a todo item.\n\nUsage: `/todo <your todo text>`\n\nExample: `/todo Buy groceries`",
                response_type="ephemeral"
            )
            return

        # Remove surrounding quotes if present
        cleaned_text = todo_text.strip('"\'')

        if not cleaned_text:
            respond(
                text="❌ Please provide a todo item.",
                response_type="ephemeral"
            )
            return

        # Get user info
        user_name = command.get("user_name", "unknown")
        user_id = command.get("user_id", "unknown")
        logger.info(f"[/todo] User: {user_name}, Todo: '{cleaned_text}'")

        # Call Todo API to create the todo
        todo = client.create_todo(title=cleaned_text)
        logger.info(f"[/todo] Created todo ID: {todo.id}")

        # Respond with success
        respond(
            text=f"✅ Todo added: \"{todo.title}\"",
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
                      "text": f"*ID:*"
                    },
                    {
                      "type": "plain_text",
                      "text": str(todo.id)
                    }
                  ]
                },
                {
                  "type": "section",
                  "fields": [
                    {
                      "type": "mrkdwn",
                      "text": f"*Title:*"
                    },
                    {
                      "type": "plain_text",
                      "text": todo.title
                    }
                  ]
                },
                {
                  "type": "section",
                  "fields": [
                    {
                      "type": "mrkdwn",
                      "text": f"*Added by:*"
                    },
                    {
                      "type": "plain_text",
                      "text": f"<@{user_id}> | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" 
                    }
                  ]
                }
            ],
            response_type="in_channel"
        )

    except Exception as e:
        logger.error(f"[/todo] Error: {e}", exc_info=True)
        respond(
            text="❌ Sorry, something went wrong while adding your todo. Please try again.",
            response_type="ephemeral"
        )
