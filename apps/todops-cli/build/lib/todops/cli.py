"""Main CLI module for todops."""

import click
from todops import __version__


@click.group()
def main():
    """todops - A minimal CLI for todo platform operations."""
    pass


@main.command()
def version():
    """Display the version of todops."""
    click.echo(f"todops version {__version__}")


if __name__ == "__main__":
    main()
