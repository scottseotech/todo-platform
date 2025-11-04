import logging
import json
from time import sleep

from utils.subprocess import run_command

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

        servicesObj = {"service": services}
        servicesJson = json.dumps(servicesObj)
        cmds = [
            "gh",
            "workflow",
            "run", 
            "-R",
            "scottseotech/todo-platform",
            "Services Deployment",
            "-f",
            f"version={version}",
            "-f", 
            f"services={servicesJson}"
        ]
        run_command(cmds)

        search_cmd = f'gh run list --workflow=deployment.yaml --limit=10 --json databaseId,displayTitle --jq ".[] | select(.displayTitle | ascii_downcase | contains(\\"{version}\\" | ascii_downcase)) | .databaseId" | head -1'
        
        run_id = ""
        for i in range(10):
            sleep(1)
            result = run_command(search_cmd, shell=True, debug=False)
            output = result.stdout.strip()
            if output:
                run_id=output
                break

        # Format services list for display
        services_list = ",".join([f"{svc}" for svc in services])

        # Send a message to the user
        client.chat_postMessage(
            channel=user_id,
            text=f"Service Deployment initiated",
            unfurl_links=False,
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":information_source: Service Deployment Initiated"
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
                      "text": "*Github Workflow Run:*"
                    },
                    {
                      "type": "mrkdwn",
                      "text": f"<https://github.com/scottseotech/todo-platform/actions/runs/{run_id}|{run_id}>"
                    }
                  ]
                },                
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Services:* "
                        },
                        {
                            "type": "plain_text",
                            "text": f"{services_list}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Version:* "
                        },
                        {
                            "type": "plain_text",
                            "text": f"{version}"
                        }
                    ]
                }
            ]
        )

    except Exception as e:
        logger.error(f"[deploy] Error handling submission: {e}", exc_info=True)