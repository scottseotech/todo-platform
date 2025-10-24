"""
Event handlers for Slack events
"""

import logging

logger = logging.getLogger(__name__)


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
