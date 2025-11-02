import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import click
import requests
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

class LokiClient:
    """Client for interacting with Loki API."""
    
    def __init__(self, base_url: str):
        """Initialize Loki client with base URL."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set timeout for requests
        self.session.timeout = 30
    
    def _parse_time_expression(self, time_expr: str) -> datetime:
        """
        Parse human-readable time expressions into datetime objects.
        
        Supports formats like:
        - "1 hour ago"
        - "30 minutes ago"
        - "2 days ago"
        - "1h ago", "30m ago", "2d ago"
        - Absolute timestamps: "2024-01-01T00:00:00Z"
        """
        time_expr = time_expr.strip().lower()
        
        # Handle absolute timestamps first
        if not time_expr.endswith('ago'):
            try:
                return date_parser.parse(time_expr)
            except Exception as e:
                raise ValueError(f"Invalid timestamp format: {time_expr}") from e
        
        # Parse relative time expressions
        time_expr = time_expr.replace('ago', '').strip()
        
        # Extract number and unit
        patterns = [
            (r'(\d+)\s*h(?:our)?s?', 'hours'),
            (r'(\d+)\s*m(?:in(?:ute)?)?s?', 'minutes'),
            (r'(\d+)\s*s(?:ec(?:ond)?)?s?', 'seconds'),
            (r'(\d+)\s*d(?:ay)?s?', 'days'),
            (r'(\d+)\s*w(?:eek)?s?', 'weeks'),
        ]
        
        for pattern, unit in patterns:
            match = re.search(pattern, time_expr)
            if match:
                value = int(match.group(1))
                delta_kwargs = {unit: value}
                return datetime.utcnow() - timedelta(**delta_kwargs)
        
        raise ValueError(f"Unable to parse time expression: {time_expr}")
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime as nanosecond timestamp for Loki."""
        return str(int(dt.timestamp() * 1_000_000_000))
    
    def query_range(self, query: str, start_time: datetime, end_time: Optional[datetime] = None, 
                   limit: int = 100) -> Dict:
        """
        Query logs from Loki using LogQL.
        
        Args:
            query: LogQL query string
            start_time: Start time for query
            end_time: End time for query (defaults to now)
            limit: Maximum number of log entries to return
            
        Returns:
            Dict containing Loki API response
        """
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Build query parameters
        params = {
            'query': query,
            'start': self._format_timestamp(start_time),
            'end': self._format_timestamp(end_time),
            'limit': limit,
            'direction': 'backward',  # Most recent first
        }
        
        url = f"{self.base_url}/loki/api/v1/query_range"
        
        try:
            if not getattr(self, '_silent_mode', False):
                logger.debug(f"Querying Loki: {url} with params: {params}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if not getattr(self, '_silent_mode', False):
                logger.error(f"Failed to query Loki: {e}")
            raise click.ClickException(f"Failed to connect to Loki at {self.base_url}: {e}")
        except json.JSONDecodeError as e:
            if not getattr(self, '_silent_mode', False):
                logger.error(f"Invalid JSON response from Loki: {e}")
            raise click.ClickException(f"Invalid response from Loki: {e}")
    
    def search_logs(self, search_term: str, since: str = "1h", limit: int = 100,
                   namespace: Optional[str] = None, pod: Optional[str] = None,
                   app: Optional[str] = None,
                   ignore_list: Optional[List[Dict]] = None, debug: bool = False) -> List[Dict]:
        """
        Search logs for a specific term with optional filters.

        Args:
            search_term: Text to search for in logs
            since: Time range to search (e.g., "1h", "30m", "1 day ago")
            limit: Maximum number of results
            namespace: Kubernetes namespace filter
            pod: Pod name filter
            app: App label filter
            ignore_list: List of active ignore entries to exclude from search

        Returns:
            List of log entries
        """
        # Build LogQL query
        query_parts = []
        
        # Build selector with multiple filters
        selector_filters = []
        
        # Always include job filter as base
        selector_filters.append('job=~".+"')
        
        # Add namespace filter
        if namespace:
            selector_filters.append(f'namespace="{namespace}"')
            
        # Add pod filter - try instance first (more common in fluent-bit logs)
        if pod:
            selector_filters.append(f'instance=~".*{pod}.*"')
            
        # Add app filter
        if app:
            selector_filters.append(f'app="{app}"')

        selector = '{' + ', '.join(selector_filters) + '}'

        query_parts.append(selector)

        # Add search filter if provided
        if search_term:
            # Special case: if search term is just ".", don't add a filter (match all)
            if search_term != ".":
                # Use regex filter for case-insensitive search
                escaped_term = re.escape(search_term)
                query_parts.append(f' |~ "(?i){escaped_term}"')
        
        if ignore_list:
            for entry in ignore_list:
                query_parts.append(f' !~ "{entry["log_signature"]}"')

        query = ''.join(query_parts)

        # Parse time range
        start_time = self._parse_time_expression(since)

        # Show debug info if requested
        if debug:
            click.echo(f"\nLogQL Query: {query}")
            click.echo(f"Time range: {start_time} to now")
            click.echo(f"Limit: {limit}\n")

        # Execute query
        result = self.query_range(query, start_time, limit=limit)
        
        # Extract and format log entries
        log_entries = []
        
        if result.get('status') == 'success':
            data = result.get('data', {})
            streams = data.get('result', [])
            
            for stream in streams:
                labels = stream.get('stream', {})
                values = stream.get('values', [])
                
                for timestamp_ns, log_line in values:
                    # Convert nanosecond timestamp to datetime
                    timestamp = datetime.fromtimestamp(int(timestamp_ns) / 1_000_000_000)
                    
                    # Extract pod name from labels - fluent-bit maps pod_name to 'instance'
                    pod_name = labels.get('pod') or labels.get('instance', 'unknown')
                    
                    log_entries.append({
                        'timestamp': timestamp,
                        'labels': labels,
                        'message': log_line,
                        'namespace': labels.get('namespace', 'unknown'),
                        'pod': pod_name,
                        'container': labels.get('container', 'unknown'),
                        'app': labels.get('app', 'unknown'),
                        'level': labels.get('detected_level', labels.get('level', 'unknown')),
                    })
        
        # Sort by timestamp (most recent first)
        log_entries.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return log_entries
