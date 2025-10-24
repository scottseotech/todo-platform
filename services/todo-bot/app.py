#!/usr/bin/env python3
"""
Todo Slack Bot

A Slack bot for managing todos using slash commands.
Built with Slack Bolt SDK using Socket Mode.
"""

import os
import logging
import threading
from datetime import datetime
from flask import Flask, jsonify
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask web server for health checks
web_app = Flask(__name__)

# Disable Flask's default logger to reduce noise
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# Initialize Slack app with Socket Mode
# Note: signing_secret is not required for Socket Mode but kept for compatibility
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN")
)

# Configuration
TODO_API_URL = os.environ.get("TODO_API_URL", "http://localhost:8080")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8082"))


@web_app.route("/health")
def health():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        "status": "healthy"
    }), 200


@app.command("/todo")
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

        # TODO: Call Todo API to create the todo
        # For now, just acknowledge receipt
        user_name = command.get("user_name", "unknown")
        user_id = command.get("user_id", "unknown")
        logger.info(f"[/todo] User: {user_name}, Todo: '{cleaned_text}'")

        # Placeholder response - will be replaced with actual API call
        respond(
            text=f"✅ Todo added: \"{cleaned_text}\"",
            blocks=[
                {
                  "type": "header",
                  "text": {
                    "type": "plain_text",
                    "text": "Todo"
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
                      "text": "*Status:*"
                    },
                    {
                      "type": "plain_text",
                      "text": "Added"
                    }
                  ]
                },
                {
                  "type": "section",
                  "fields": [
                    {
                      "type": "mrkdwn",
                      "text": "*Added by:*"
                    },
                    {
                      "type": "mrkdwn",
                      "text": f"<@{user_id}> | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                  ]
                },
            ],
            response_type="in_channel"
        )

    except Exception as e:
        logger.error(f"[/todo] Error: {e}", exc_info=True)
        respond(
            text="❌ Sorry, something went wrong while adding your todo. Please try again.",
            response_type="ephemeral"
        )


@app.event("app_home_opened")
def handle_app_home_opened(client, event):
    """
    Handle app home opened event
    Shows a welcome message when users open the app's home tab
    """
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome to Todo Bot! 👋*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Use the `/todo` command to manage your todos.\n\n*Available Commands:*\n• `/todo <text>` - Add a new todo"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Examples:*\n```/todo Buy groceries\n/todo \"Call dentist tomorrow\"\n/todo Finish project report```"
                        }
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"[app_home_opened] Error: {e}", exc_info=True)


@app.event("app_mention")
def handle_app_mention(event, say):
    """
    Handle app mentions
    Responds when the bot is mentioned in a channel
    """
    try:
        user = event["user"]
        say(
            text=f"Hi <@{user}>! Use `/todo` to add a todo item.",
            thread_ts=event["ts"]
        )
    except Exception as e:
        logger.error(f"[app_mention] Error: {e}", exc_info=True)


def start_health_server():
    """Start the Flask health check server in a separate thread"""
    logger.info(f"🏥 Starting health check server on port {SERVER_PORT}")
    web_app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)


def main():
    """Start the Slack bot"""
    try:
        # Verify required environment variables (signing_secret not needed for Socket Mode)
        required_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]

        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please check your .env file")
            return

        logger.info("⚡️ Todo Bot is starting...")
        logger.info(f"📍 Todo API URL: {TODO_API_URL}")

        # Start health check server in background thread
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()

        # Start the app using Socket Mode
        handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])

        logger.info("⚡️ Todo Bot is running in Socket Mode!")
        logger.info("👂 Listening for Slack events...")

        handler.start()

    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down Todo Bot...")
    except Exception as e:
        logger.error(f"Failed to start app: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
