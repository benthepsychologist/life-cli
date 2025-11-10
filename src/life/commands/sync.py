"""
Sync command for Life-CLI.

Executes data synchronization tasks defined in the config file.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import typer
from typing import Optional

app = typer.Typer(help="Sync data from external sources")


@app.callback(invoke_without_command=True)
def sync_callback(
    ctx: typer.Context,
    task: Optional[str] = typer.Argument(None, help="Sync task to run (from config)"),
):
    """Execute sync tasks defined in config file."""
    if task is None:
        # No task specified, show available tasks
        typer.echo("Available sync tasks:")
        typer.echo("  (will be loaded from config)")
        return

    # Get config and dry_run from parent context
    config = ctx.obj.get("config", {})
    dry_run = ctx.obj.get("dry_run", False)

    sync_tasks = config.get("sync", {})

    if task not in sync_tasks:
        typer.echo(f"Error: Sync task '{task}' not found in config", err=True)
        raise typer.Exit(1)

    task_config = sync_tasks[task]
    command = task_config.get("command")

    if dry_run:
        typer.echo(f"[DRY RUN] Would execute sync task: {task}")
        typer.echo(f"[DRY RUN] Command: {command}")
    else:
        typer.echo(f"Executing sync task: {task}")
        # Actual execution will be implemented in Step 3
        typer.echo("(Command execution not yet implemented)")
