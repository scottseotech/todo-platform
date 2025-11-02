"""Loki ignore list manager for MinIO storage."""

import json
import logging
import re
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, List

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
