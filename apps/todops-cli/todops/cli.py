"""Main CLI module for todops."""

import os
from pathlib import Path
import click
from dotenv import load_dotenv
from todops import __version__
from todops.loki_commands import loki
from todops.loki_ignore_commands import ignore
from todops.slack_commands import slack

# Load .env file if it exists
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

@click.group()
def main():
    """todops - A minimal CLI for todo platform operations."""
    pass


main.add_command(loki)
loki.add_command(ignore)
main.add_command(slack)

@main.command()
def version():
    """Display the version of todops."""
    click.echo(f"todops version {__version__}")


if __name__ == "__main__":
    main()
