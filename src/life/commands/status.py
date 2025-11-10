"""
Status command for Life-CLI.

Executes status check tasks defined in the config file.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import typer
from typing import Optional

app = typer.Typer(help="Check status and generate reports")


@app.callback(invoke_without_command=True)
def status_callback(
    ctx: typer.Context,
    task: Optional[str] = typer.Argument(None, help="Status task to run (from config)"),
):
    """Execute status tasks defined in config file."""
    if task is None:
        typer.echo("Available status tasks:")
        typer.echo("  (will be loaded from config)")
        return

    # Get config and dry_run from parent context
    config = ctx.obj.get("config", {})
    dry_run = ctx.obj.get("dry_run", False)

    status_tasks = config.get("status", {})

    if task not in status_tasks:
        typer.echo(f"Error: Status task '{task}' not found in config", err=True)
        raise typer.Exit(1)

    task_config = status_tasks[task]
    command = task_config.get("command")

    if dry_run:
        typer.echo(f"[DRY RUN] Would execute status task: {task}")
        typer.echo(f"[DRY RUN] Command: {command}")
    else:
        typer.echo(f"Executing status task: {task}")
        # Actual execution will be implemented later
        typer.echo("(Command execution not yet implemented)")
