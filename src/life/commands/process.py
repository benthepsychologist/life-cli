"""
Process command for Life-CLI.

Executes data processing tasks defined in the config file.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import typer
from typing import Optional

app = typer.Typer(help="Process and transform data")


@app.callback(invoke_without_command=True)
def process_callback(
    ctx: typer.Context,
    task: Optional[str] = typer.Argument(None, help="Process task to run (from config)"),
):
    """Execute process tasks defined in config file."""
    if task is None:
        typer.echo("Available process tasks:")
        typer.echo("  (will be loaded from config)")
        return

    # Get config and dry_run from parent context
    config = ctx.obj.get("config", {})
    dry_run = ctx.obj.get("dry_run", False)

    process_tasks = config.get("process", {})

    if task not in process_tasks:
        typer.echo(f"Error: Process task '{task}' not found in config", err=True)
        raise typer.Exit(1)

    task_config = process_tasks[task]
    command = task_config.get("command")

    if dry_run:
        typer.echo(f"[DRY RUN] Would execute process task: {task}")
        typer.echo(f"[DRY RUN] Command: {command}")
    else:
        typer.echo(f"Executing process task: {task}")
        # Actual execution will be implemented in Step 4
        typer.echo("(Command execution not yet implemented)")
