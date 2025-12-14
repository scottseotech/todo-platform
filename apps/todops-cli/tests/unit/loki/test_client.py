from todops.loki.client import LokiClient
from datetime import datetime, timedelta

def test_parse_time_expression():
    client = LokiClient(base_url="http://localhost:3100")

    # Test relative time expressions
    now = datetime.now()

    one_hour_ago = client._parse_time_expression("1 hour ago")

    assert (now - one_hour_ago).total_seconds() >= 3600 - 5  # Allow small delta for execution time

    thirty_minutes_ago = client._parse_time_expression("30 minutes ago")
    assert (now - thirty_minutes_ago).total_seconds() >= 1800 - 5

    two_days_ago = client._parse_time_expression("2 days ago")
    assert (now - two_days_ago).total_seconds() >= 172800 - 5

    # Test absolute timestamp
    absolute_time = "2024-01-01T00:00:00Z"
    parsed_time = client._parse_time_expression(absolute_time)

    assert parsed_time == datetime(2024, 1, 1, 0, 0, 0, tzinfo=parsed_time.tzinfo)

def test_format_timestamp():
    client = LokiClient(base_url="http://localhost:3100")
    now = datetime.now()
    one_hour_ago = client._format_timestamp(now)
