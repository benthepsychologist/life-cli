"""
Main CLI entry point for Life-CLI.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import sys
import logging
from typing import Optional
from pathlib import Path

import typer
import yaml

from life import __version__
from life.config import load_config
from life.commands import sync, merge, process, status

# Initialize main app
app = typer.Typer(
    name="life",
    help="Lightweight, stateful, CLI-first orchestrator for personal data pipelines",
    no_args_is_help=True,
)

# Add subcommands
app.add_typer(sync.app, name="sync")
app.add_typer(merge.app, name="merge")
app.add_typer(process.app, name="process")
app.add_typer(status.app, name="status")

# Global state for context
state = {"config": {}, "dry_run": False, "verbose": False}


def setup_logging(verbose: bool = False):
    """Configure logging for the CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@app.callback()
def main_callback(
    ctx: typer.Context,
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (default: ~/life.yml or ./life.yml)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be executed without running commands",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """
    Life-CLI: Lightweight orchestrator for personal data pipelines.

    Manages sync, merge, process, and status tasks defined in a YAML config file.
    """
    # Setup logging
    setup_logging(verbose)

    # Load config if a subcommand is being invoked
    if ctx.invoked_subcommand and ctx.invoked_subcommand != "version":
        try:
            config = load_config(config_path)
            state["config"] = config
            state["dry_run"] = dry_run
            state["verbose"] = verbose

            if verbose:
                logging.debug(f"Loaded config from: {config_path or 'default location'}")
                logging.debug(f"Dry run: {dry_run}")

        except FileNotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except yaml.YAMLError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    # Store state in context for subcommands
    ctx.obj = state


@app.command()
def version():
    """Show version information."""
    typer.echo(f"life-cli version {__version__}")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
