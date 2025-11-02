#!/usr/bin/env python3
"""
Loki ignore list management commands for todops

This module provides commands for managing a Loki log signature ignore list
stored in MinIO.
"""

import json
import logging
from datetime import datetime
from typing import Optional

import click

from todops.loki.config import get_minio_config
from todops.loki.ignore_manager import LokiIgnoreManager

logger = logging.getLogger(__name__)


@click.group()
def ignore():
    """Manage Loki log signature ignore list."""
    pass


@ignore.command('set')
@click.argument('log_signature')
@click.option('--for', 'duration', default='7 days',
              help='Duration to ignore (e.g., "7 days", "2 weeks", "3 hours")')
@click.option('--minio-url', help='MinIO URL (overrides MINIO_URL env var)')
def ignore_set(log_signature: str, duration: str, minio_url: Optional[str]):
    """
    Add or update a log signature in the ignore list.
    
    LOG_SIGNATURE: The log pattern/signature to ignore

    \b 
    Examples:
        todops loki ignore set "Connection timeout" --for "7 days"
        todops loki ignore set "Retrying operation" --for "2 weeks"
        todops loki ignore set "DEBUG: Cache miss" --for "3 hours"
    """
    try:
        config = get_minio_config()
        if minio_url:
            config['url'] = minio_url
        
        manager = LokiIgnoreManager(
            config['url'],
            config['access_key'],
            config['secret_key']
        )
        
        entry_id = manager.add_ignore_entry(log_signature, duration)

        expire_date = manager._parse_duration(duration)
        click.echo(f"Added ignore entry:")
        click.echo(f"   ID: {entry_id}")
        click.echo(f"   Signature: {log_signature}")
        click.echo(f"   Expires: {expire_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
    except Exception as e:
        logger.error(f"Failed to add ignore entry: {e}")
        raise click.ClickException(f"Failed to add ignore entry: {e}")


@ignore.command('delete')
@click.argument('entry_id')
@click.option('--minio-url', help='MinIO URL (overrides MINIO_URL env var)')
def ignore_delete(entry_id: str, minio_url: Optional[str]):
    """
    Delete an entry from the ignore list.
    
    ENTRY_ID: The ID of the entry to delete
    """
    try:
        config = get_minio_config()
        if minio_url:
            config['url'] = minio_url
        
        manager = LokiIgnoreManager(
            config['url'],
            config['access_key'],
            config['secret_key']
        )
        
        if manager.delete_entry(entry_id):
            click.echo(f"Deleted entry: {entry_id}")
        else:
            click.echo(f"Entry not found: {entry_id}")
            
    except Exception as e:
        logger.error(f"Failed to delete entry: {e}")
        raise click.ClickException(f"Failed to delete entry: {e}")


@ignore.command('deactivate')
@click.argument('entry_id')
@click.option('--minio-url', help='MinIO URL (overrides MINIO_URL env var)')
def ignore_deactivate(entry_id: str, minio_url: Optional[str]):
    """
    Deactivate an entry in the ignore list.
    
    ENTRY_ID: The ID of the entry to deactivate
    """
    try:
        config = get_minio_config()
        if minio_url:
            config['url'] = minio_url
        
        manager = LokiIgnoreManager(
            config['url'],
            config['access_key'],
            config['secret_key']
        )
        
        if manager.update_status(entry_id, 'inactive'):
            click.echo(f"Deactivated entry: {entry_id}")
        else:
            click.echo(f"Entry not found: {entry_id}")
            
    except Exception as e:
        logger.error(f"Failed to deactivate entry: {e}")
        raise click.ClickException(f"Failed to deactivate entry: {e}")


@ignore.command('activate')
@click.argument('entry_id')
@click.option('--minio-url', help='MinIO URL (overrides MINIO_URL env var)')
def ignore_activate(entry_id: str, minio_url: Optional[str]):
    """
    Activate an entry in the ignore list.
    
    ENTRY_ID: The ID of the entry to activate
    """
    try:
        config = get_minio_config()
        if minio_url:
            config['url'] = minio_url
        
        manager = LokiIgnoreManager(
            config['url'],
            config['access_key'],
            config['secret_key']
        )
        
        if manager.update_status(entry_id, 'active'):
            click.echo(f"Activated entry: {entry_id}")
        else:
            click.echo(f"Entry not found: {entry_id}")
            
    except Exception as e:
        logger.error(f"Failed to activate entry: {e}")
        raise click.ClickException(f"Failed to activate entry: {e}")


@ignore.command('list')
@click.option('--active-only', is_flag=True, help='Show only active entries')
@click.option('--format', 'output_format', default='table',
              type=click.Choice(['table', 'json']),
              help='Output format')
@click.option('--minio-url', help='MinIO URL (overrides MINIO_URL env var)')
def ignore_list(active_only: bool, output_format: str, minio_url: Optional[str]):
    """List all entries in the ignore list."""
    try:
        config = get_minio_config()
        if minio_url:
            config['url'] = minio_url
        
        manager = LokiIgnoreManager(
            config['url'],
            config['access_key'],
            config['secret_key']
        )
        
        entries = manager.list_entries(active_only=active_only)
        
        if not entries:
            click.echo("No entries in ignore list")
            return
        
        if output_format == 'json':
            click.echo(json.dumps(entries, indent=2))
        else:
            # Table format
            click.echo("Loki Ignore List:")
            click.echo()
            click.echo(f"{'ID':<40} {'Signature':<40} {'Status':<10} {'Expires':<20}")
            click.echo("-" * 114)
            
            for entry in entries:
                entry_id = entry['id']  # Show full UUID
                signature = entry['log_signature']
                if len(signature) > 37:
                    signature = signature[:34] + '...'
                
                status = entry['status']
                expire_date = datetime.fromisoformat(entry['expire_date'])
                expire_str = expire_date.strftime('%Y-%m-%d %H:%M')
                
                status_display = status
                
                click.echo(f"{entry_id:<40} {signature:<40} {status_display:<10} {expire_str:<20}")
            
            click.echo()
            click.echo(f"Total entries: {len(entries)}")
            
    except Exception as e:
        logger.error(f"Failed to list entries: {e}")
        raise click.ClickException(f"Failed to list entries: {e}")


if __name__ == '__main__':
    ignore()