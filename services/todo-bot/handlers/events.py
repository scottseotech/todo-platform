"""
Event handlers for Slack events
"""

import logging
import asyncio
import re
from backends import ChatBackend

logger = logging.getLogger(__name__)

# Global backend reference - should be set by main app
_chat_backend: ChatBackend = None


def set_chat_backend(backend: ChatBackend):
    """Set the chat backend for handling app mentions"""
    global _chat_backend
    _chat_backend = backend

def app_mention(event, say):
    """
    Handle app mentions
    Responds when the bot is mentioned in a channel by relaying to LLM
    """
    try:
        user = event["user"]
        text = event.get("text", "")

        # Remove bot mention from the text
        # Slack mentions look like <@U12345678>
        clean_text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()

        if not clean_text:
            say(
                text=f"Hi <@{user}>! How can I help you?",
                thread_ts=event["ts"]
            )
            return

        # Check if backend is configured
        if _chat_backend is None:
            logger.warning("[app_mention] Chat backend not configured")
            say(
                text="Sorry, I'm not configured to respond right now.",
                thread_ts=event["ts"]
            )
            return

        # Send to LLM
        logger.info(f"[app_mention] Relaying to LLM: {clean_text}")

        # Run async function in sync context
        response = asyncio.run(_chat_backend.chat(clean_text, user))

        # Format response in alert style
        formatted_response = f"*AI Agent Response* for <@{user}>\n\n{response}"
        say(formatted_response)

        # Reply in thread
        # say(
        #     text=formatted_response,
        #     thread_ts=event["ts"]
        # )

    except Exception as e:
        logger.error(f"[app_mention] Error: {e}", exc_info=True)
        try:
            say(
                text="Sorry, I encountered an error processing your message.",
                thread_ts=event.get("ts")
            )
        except:
            pass
