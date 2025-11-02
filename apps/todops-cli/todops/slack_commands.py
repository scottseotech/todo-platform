#!/usr/bin/env python3

import sys

import click

from todops.slack.client import SlackClient


@click.group()
def slack():
    """Slack integration commands."""
    pass


@slack.command('post-message')
@click.argument('channel_alias')
@click.argument('message', required=False)
@click.option('--blocks/--no-blocks', default=False, help='Use rich block formatting (default: simple text)')
@click.option('--code/--no-code', default=False, help='Format message as code block')
def slack_post_message(channel_alias, message, blocks, code):
    """Post a message to a Slack channel.
    
    CHANNEL_ALIAS: Channel alias (e.g., 'alerts', 'general') or channel name
    MESSAGE: Message text to send (optional if reading from stdin)
    
    The message can be provided as an argument or read from stdin. If both are available,
    the argument takes precedence. If neither is provided, an error is raised.

    \b
    Examples:
        todops slack post-message alerts "System rebooted successfully"
        todops slack post-message alerts "Daily summary complete" --blocks
        echo "Pipeline completed" | todops slack post-message alerts
        cat report.txt | todops slack post-message alerts --blocks
    """
    try:
        # Determine message source
        final_message = None
        
        # Check if message was provided as argument
        if message:
            final_message = message
        else:
            # Check if there's data available on stdin
            if not sys.stdin.isatty():
                # Read from stdin
                stdin_content = sys.stdin.read().strip()
                if stdin_content:
                    final_message = stdin_content
        
        # Validate that we have a message
        if not final_message:
            click.echo("Error: No message provided. Either pass a message as an argument or pipe content to stdin.", err=True)
            click.echo("Examples:", err=True)
            click.echo("  todops slack post-message alerts \"Your message\"", err=True)
            click.echo("  echo \"Your message\" | todops slack post-message alerts", err=True)
            sys.exit(1)
        
        # Initialize Slack client
        slack_client = SlackClient()
        
        # Send message
        if code:
            final_message = f"```\n{final_message}\n```"
        success = slack_client.post_message(channel_alias, final_message, use_blocks=blocks)
        
        if not success:
            sys.exit(1)
            
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        click.echo("Make sure SLACK_BOT_TOKEN environment variable is set", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error sending Slack message: {e}", err=True)
        sys.exit(1)


@slack.command('list-channels')
def slack_list_channels():
    """List available channel aliases."""
    try:
        slack_client = SlackClient()
        aliases = slack_client.list_available_aliases()
        
        click.echo("Available channel aliases:")
        for alias, channel in aliases.items():
            click.echo(f"  {alias} -> {channel}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)