#!/usr/bin/env python3
"""
Loki ignore list management commands for todops

This module provides commands for managing a Loki log signature ignore list
stored in MinIO.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

import click
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class LokiIgnoreManager:
    """Manager for Loki ignore list stored in MinIO."""
    
    BUCKET_NAME = "tools"
    OBJECT_NAME = "loki-ignore.json"
    
    def __init__(self, minio_url: str, access_key: str, secret_key: str, secure: bool = False):
        """Initialize MinIO client for ignore list management."""
        # Parse MinIO URL to extract host and port
        url = minio_url.replace('http://', '').replace('https://', '')
        if ':' in url:
            host, port = url.split(':')
            endpoint = f"{host}:{port}"
        else:
            endpoint = url
            
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # Ensure bucket exists
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure the tools bucket exists."""
        try:
            if not self.client.bucket_exists(self.BUCKET_NAME):
                self.client.make_bucket(self.BUCKET_NAME)
                logger.info(f"Created bucket: {self.BUCKET_NAME}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise
    
    def _parse_duration(self, duration_str: str) -> datetime:
        """
        Parse duration string into future timestamp.
        
        Supports formats like:
        - "7 days"
        - "2 weeks"
        - "1 month"
        - "3 hours"
        - "30 minutes"
        """
        duration_str = duration_str.strip().lower()
        
        # Regular expression patterns for duration parsing
        patterns = [
            (r'(\d+)\s*(?:minute|minutes|min|mins|m)', 'minutes'),
            (r'(\d+)\s*(?:hour|hours|hr|hrs|h)', 'hours'),
            (r'(\d+)\s*(?:day|days|d)', 'days'),
            (r'(\d+)\s*(?:week|weeks|w)', 'weeks'),
            (r'(\d+)\s*(?:month|months|mo)', 'days', 30),  # Approximate months as 30 days
        ]
        
        for pattern_info in patterns:
            if len(pattern_info) == 2:
                pattern, unit = pattern_info
                multiplier = 1
            else:
                pattern, unit, multiplier = pattern_info
                
            match = re.search(pattern, duration_str)
            if match:
                value = int(match.group(1))
                if unit == 'weeks':
                    delta = timedelta(weeks=value)
                elif unit == 'days':
                    delta = timedelta(days=value * multiplier)
                elif unit == 'hours':
                    delta = timedelta(hours=value)
                elif unit == 'minutes':
                    delta = timedelta(minutes=value)
                else:
                    raise ValueError(f"Unknown time unit: {unit}")
                    
                return datetime.utcnow() + delta
        
        raise ValueError(f"Unable to parse duration: {duration_str}")
    
    def _load_ignore_list(self) -> List[Dict]:
        """Load the current ignore list from MinIO."""
        try:
            response = self.client.get_object(self.BUCKET_NAME, self.OBJECT_NAME)
            data = response.read()
            response.close()
            response.release_conn()
            
            return json.loads(data.decode('utf-8'))
        except S3Error as e:
            if e.code == 'NoSuchKey':
                # File doesn't exist yet, return empty list
                return []
            else:
                logger.error(f"Failed to load ignore list: {e}")
                raise
    
    def _save_ignore_list(self, ignore_list: List[Dict]):
        """Save the ignore list to MinIO."""
        try:
            # Convert to JSON
            json_data = json.dumps(ignore_list, indent=2, default=str)
            json_bytes = json_data.encode('utf-8')
            
            # Upload to MinIO
            from io import BytesIO
            self.client.put_object(
                self.BUCKET_NAME,
                self.OBJECT_NAME,
                BytesIO(json_bytes),
                length=len(json_bytes),
                content_type='application/json'
            )
            
            logger.info(f"Saved ignore list with {len(ignore_list)} entries")
        except S3Error as e:
            logger.error(f"Failed to save ignore list: {e}")
            raise
    
    def add_ignore_entry(self, log_signature: str, duration: str) -> str:
        """
        Add a new entry to the ignore list.
        
        Args:
            log_signature: The log signature/pattern to ignore
            duration: Duration string (e.g., "7 days")
            
        Returns:
            The ID of the created entry
        """
        # Load current list
        ignore_list = self._load_ignore_list()
        
        # Parse duration to get expiry date
        expire_date = self._parse_duration(duration)
        
        # Create new entry
        entry_id = str(uuid.uuid4())
        new_entry = {
            'id': entry_id,
            'log_signature': log_signature,
            'expire_date': expire_date.isoformat(),
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Check if signature already exists
        for entry in ignore_list:
            if entry['log_signature'] == log_signature and entry['status'] == 'active':
                # Update existing entry instead
                entry['expire_date'] = expire_date.isoformat()
                entry['updated_at'] = datetime.utcnow().isoformat()
                self._save_ignore_list(ignore_list)
                return entry['id']
        
        # Add new entry
        ignore_list.append(new_entry)
        
        # Save updated list
        self._save_ignore_list(ignore_list)
        
        return entry_id
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete an entry from the ignore list.
        
        Args:
            entry_id: The ID of the entry to delete
            
        Returns:
            True if entry was deleted, False if not found
        """
        ignore_list = self._load_ignore_list()
        
        # Find and remove entry
        original_length = len(ignore_list)
        ignore_list = [e for e in ignore_list if e['id'] != entry_id]
        
        if len(ignore_list) < original_length:
            self._save_ignore_list(ignore_list)
            return True
        
        return False
    
    def update_status(self, entry_id: str, status: str) -> bool:
        """
        Update the status of an entry.
        
        Args:
            entry_id: The ID of the entry to update
            status: New status ('active' or 'inactive')
            
        Returns:
            True if entry was updated, False if not found
        """
        ignore_list = self._load_ignore_list()
        
        for entry in ignore_list:
            if entry['id'] == entry_id:
                entry['status'] = status
                entry['updated_at'] = datetime.utcnow().isoformat()
                self._save_ignore_list(ignore_list)
                return True
        
        return False
    
    def list_entries(self, active_only: bool = False) -> List[Dict]:
        """
        List all entries in the ignore list.
        
        Args:
            active_only: If True, only return active entries
            
        Returns:
            List of ignore entries
        """
        ignore_list = self._load_ignore_list()
        
        # Clean up expired entries
        now = datetime.utcnow()
        cleaned_list = []
        
        for entry in ignore_list:
            expire_date = datetime.fromisoformat(entry['expire_date'])
            if expire_date < now:
                # Mark as expired
                entry['status'] = 'expired'
            cleaned_list.append(entry)
        
        # Save if we marked any as expired
        if any(e['status'] == 'expired' for e in cleaned_list):
            self._save_ignore_list(cleaned_list)
        
        if active_only:
            return [e for e in cleaned_list if e['status'] == 'active']
        
        return cleaned_list


def get_minio_config() -> Dict[str, str]:
    """Get MinIO configuration from environment variables."""
    config = {
        'url': os.getenv('MINIO_URL', 'localhost:9000'),
        'access_key': os.getenv('MINIO_ACCESS_KEY', os.getenv('MINIO_ROOT_USER', '')),
        'secret_key': os.getenv('MINIO_SECRET_KEY', os.getenv('MINIO_ROOT_PASSWORD', '')),
    }
    
    if not config['access_key'] or not config['secret_key']:
        raise click.ClickException(
            "MinIO credentials not found. Please set MINIO_ACCESS_KEY and MINIO_SECRET_KEY "
            "environment variables (or MINIO_ROOT_USER and MINIO_ROOT_PASSWORD)."
        )
    
    return config


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
    
    Examples:
    \b
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