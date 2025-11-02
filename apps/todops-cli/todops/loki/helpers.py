"""Helper functions for Loki CLI commands."""

import json
import re
from typing import Optional

import click

from todops.loki_ignore_commands import LokiIgnoreManager, get_minio_config


def is_quiet_mode(output_format: str) -> bool:
    """Check if output format requires quiet mode (no UI elements)."""
    return output_format in ['json', 'raw']


def load_ignore_list(output_format: str) -> Optional[list]:
    """Load active ignore list from MinIO, returns None on failure."""
    try:
        config = get_minio_config()
        manager = LokiIgnoreManager(
            config['url'],
            config['access_key'],
            config['secret_key']
        )
        return manager.list_entries(active_only=True)
    except Exception as e:
        if not is_quiet_mode(output_format):
            click.echo(f"Warning: Could not load ignore list: {e}", err=True)
        return None


def print_search_info(url: str, search_term: str, since: str,
                     namespace: Optional[str], pod: Optional[str],
                     app: Optional[str]):
    """Print search parameters (for interactive mode)."""
    click.echo(f"Searching Loki at: {url}")
    click.echo(f"Search term: '{search_term}'")
    click.echo(f"Time range: {since}")

    if namespace:
        click.echo(f"Namespace: {namespace}")
    if pod:
        click.echo(f"Pod filter: {pod}")
    if app:
        click.echo(f"App filter: {app}")

    click.echo()


def handle_empty_results(output_format: str):
    """Handle case when no log entries are found."""
    if output_format == 'json':
        click.echo("[]")
    elif output_format == 'raw':
        pass  # Silent exit
    else:
        click.echo("No matching log entries found.")


def output_json(log_entries: list):
    """Output log entries in JSON format."""
    json_entries = [
        {**entry, 'timestamp': entry['timestamp'].isoformat()}
        for entry in log_entries
    ]
    click.echo(json.dumps(json_entries, indent=2))


def output_raw(log_entries: list):
    """Output log entries in raw format."""
    for entry in log_entries:
        namespace_prefix = f"[{entry['namespace']}] "
        click.echo(f"{namespace_prefix}{entry['message']}")


def highlight_search_term(message: str, search_term: str) -> str:
    """Highlight search term in message with brackets."""
    if search_term.lower() in message.lower():
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        return pattern.sub(f'[{search_term.upper()}]', message)
    return message


def output_table(log_entries: list, search_term: str):
    """Output log entries in table format."""
    click.echo("Recent log entries:")
    click.echo()

    for i, entry in enumerate(log_entries, 1):
        timestamp_str = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        pod_name = entry['pod'][:20] if entry['pod'] != 'unknown' else 'unknown'

        message = highlight_search_term(entry['message'], search_term)

        # Truncate long messages
        if len(message) > 100:
            message = message[:97] + '...'

        click.echo(f"{i:3d}. {timestamp_str} [{pod_name:20s}] {message}")

        if i >= 50:  # Limit display to 50 entries in table mode
            remaining = len(log_entries) - 50
            if remaining > 0:
                click.echo(f"\n... and {remaining} more entries (use --format json to see all)")
            break
