#!/usr/bin/env python3
"""
Loki CLI commands for todops.

This module provides commands for interacting with Loki log aggregation system.
"""

import logging
import os
import sys
from typing import Optional

import click

from todops.loki.client import LokiClient
from todops.loki.helpers import (
    is_quiet_mode,
    load_ignore_list,
    handle_empty_results,
    output_json,
    output_raw,
    output_table,
)

logger = logging.getLogger(__name__)


@click.group()
def loki():
    """Loki log search and analysis commands."""
    pass

@loki.command()
@click.argument('search_term', required=True)
@click.option('--since', '-s', default='1h', help='Time range to search (e.g., "1h", "30m", "2 days ago")')
@click.option('--limit', '-l', default=1000, type=int, help='Maximum number of log entries to return')
@click.option('--namespace', '-n', help='Filter by Kubernetes namespace')
@click.option('--pod', '-p', help='Filter by pod name (supports partial matching)')
@click.option('--app', '-a', help='Filter by app label')
@click.option('--format', '-o', 'output_format', default='raw', type=click.Choice(['table', 'json', 'raw']), help='Output format')
@click.option('--no-ignore', is_flag=True, help='Disable ignore list filtering')
@click.option('--debug', is_flag=True, help='Show the LogQL query being executed')
def search(search_term: str, since: str, limit: int, namespace: Optional[str],
           pod: Optional[str], app: Optional[str],
           output_format: str, no_ignore: bool, debug: bool):
    """Search logs in Loki for a specific term.

    SEARCH_TERM: Text to search for in log messages

    \b
    Examples:
      todops loki search "error"
      todops loki search "failed" --since "2 hours ago"
      todops loki search "timeout" --namespace tools --limit 50
      todops loki search "exception" --pod todopsbot --format json
    """
    url = get_loki_url()

    ignore_list = load_ignore_list(output_format) if not no_ignore else None
    if debug:
        click.echo(f"ignore_list: {ignore_list}\n")

    # Search logs
    try:
        log_entries = _perform_search(
            url, output_format, search_term, since, limit,
            namespace, pod, app, ignore_list, debug
        )
    except Exception as e:
        _handle_search_error(e, output_format)
        return

    if debug:
        click.echo(f"Found {len(log_entries)} log entries\n")
        return

    if not log_entries:
        handle_empty_results(output_format)
        return

    if output_format == 'json':
        output_json(log_entries)
    elif output_format == 'raw':
        output_raw(log_entries)
    else:
        output_table(log_entries, search_term)


def _perform_search(url: str, output_format: str, search_term: str,
                   since: str, limit: int, namespace: Optional[str],
                   pod: Optional[str], app: Optional[str],
                   ignore_list: Optional[list], debug: bool) -> list:
    """Perform the actual log search with appropriate progress indication."""
    client = LokiClient(url)

    client._silent_mode = True
    return client.search_logs(
        search_term=search_term,
        since=since,
        limit=limit,
        namespace=namespace,
        pod=pod,
        app=app,
        ignore_list=ignore_list,
        debug=debug
    )

def _handle_search_error(error: Exception, output_format: str):
    """Handle search errors appropriately based on output format."""
    if is_quiet_mode(output_format):
        sys.stderr.write(f"Error: {error}\n")
        sys.exit(1)
    else:
        logger.error(f"Error searching logs: {error}")
        raise click.ClickException(f"Failed to search logs: {error}")


def get_loki_url() -> str:
    """
    Determine Loki URL with multiple fallback options.
    
    Priority:
    1. LOKI_URL environment variable
    2. Kubernetes internal service (if running in cluster)
    3. Local port-forward assumption
    4. Error if none available
    """
    # Check for explicit URL
    explicit_url = os.getenv("LOKI_URL")
    if explicit_url:
        return explicit_url
    
    # Check if running in Kubernetes
    k8s_service_account = "/var/run/secrets/kubernetes.io/serviceaccount"
    kubernetes_service_host = os.getenv("KUBERNETES_SERVICE_HOST")
    
    if os.path.exists(k8s_service_account) or kubernetes_service_host:
        # Use internal Kubernetes service
        # Loki gateway is on port 80, main Loki service on 3100
        return "http://loki-gateway.logging.svc.cluster.local:80"
    
    # Local development - assume port-forward
    return "http://localhost:3100"


if __name__ == '__main__':
    loki()