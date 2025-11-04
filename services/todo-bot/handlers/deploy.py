import logging

logger = logging.getLogger(__name__)


def deploy_slash_command(ack, command, client):
    """
    Handle /deploy slash command by opening a modal
    """
    # Acknowledge the command immediately
    ack()

    try:
        # Open the modal
        client.views_open(
            trigger_id=command["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "deploy_modal",
                "title": {
                    "type": "plain_text",
                    "text": "Deploy Service"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Deploy"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "service_block",
                        "element": {
                            "type": "multi_static_select",
                            "action_id": "service_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select one or more services"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "todo-api"
                                    },
                                    "value": "todo-api"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "todo-mcp"
                                    },
                                    "value": "todo-mcp"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "todo-bot"
                                    },
                                    "value": "todo-bot"
                                }
                            ]
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Services"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "version_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "version_input",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "e.g., v1.0.0 or abc1234"
                            }
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Version"
                        }
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"[/deploy] Error opening modal: {e}", exc_info=True)


def handle_deploy_submission(ack, body, client, logger):
    """
    Handle the deploy modal submission
    """
    # Acknowledge the submission
    ack()

    try:
        # Extract the values from the modal
        values = body["view"]["state"]["values"]

        # Get selected services (multi-select returns an array)
        selected_options = values["service_block"]["service_select"]["selected_options"]
        services = [option["value"] for option in selected_options]

        version = values["version_block"]["version_input"]["value"]

        user_id = body["user"]["id"]

        logger.info(f"[deploy] User: {user_id}, Services: {services}, Version: {version}")

        # TODO: Trigger the actual deployment workflow here
        # For now, just send a confirmation message

        # Format services list for display
        services_list = "\n".join([f"• {svc}" for svc in services])

        # Send a message to the user
        client.chat_postMessage(
            channel=user_id,
            text=f"Deployment initiated for {len(services)} service(s) version {version}",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Deployment Initiated"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Services:*\n{services_list}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Version:* {version}"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Requested by <@{user_id}>"
                        }
                    ]
                }
            ]
        )

    except Exception as e:
        logger.error(f"[deploy] Error handling submission: {e}", exc_info=True)