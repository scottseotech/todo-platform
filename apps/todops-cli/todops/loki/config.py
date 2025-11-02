"""Configuration helpers for Loki tools."""

import os
from typing import Dict

import click


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
