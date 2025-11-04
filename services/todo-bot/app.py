#!/usr/bin/env python3
"""
Todo Slack Bot

A Slack bot for managing todos using slash commands.
Built with Slack Bolt SDK using Socket Mode.
"""

import os
import logging
import threading
from flask import Flask, jsonify
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

from handlers import set_chat_backend
from backends import OpenAIBackend
from handlers.todos import todo_slash_command
from handlers.events import app_mention
from handlers.deploy import deploy_slash_command, handle_deploy_submission

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
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN")
)

# Register all handlers explicitly

app.command("/deploy")(deploy_slash_command)
app.command("/todo")(todo_slash_command)
app.event("app_mention")(app_mention)

# Register modal submission handler
app.view("deploy_modal")(handle_deploy_submission)

# Configuration
TODO_API_URL = os.environ.get("TODO_API_URL", "http://localhost:8080")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8082"))

# Configure your backend
backend = OpenAIBackend()

# Set the backend for event handlers
set_chat_backend(backend)

@web_app.route("/health")
def health():
    """Health check endpoint for Kubernetes"""
    return jsonify({
        "status": "healthy"
    }), 200


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
