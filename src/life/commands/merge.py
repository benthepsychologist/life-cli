"""
Merge command for Life-CLI.

Executes data merge/transformation tasks defined in the config file.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import typer
from typing import Optional

app = typer.Typer(help="Merge and transform data")


@app.callback(invoke_without_command=True)
def merge_callback(
    ctx: typer.Context,
    category: Optional[str] = typer.Argument(None, help="Merge category (e.g., 'clients')"),
    task: Optional[str] = typer.Argument(None, help="Merge task within category"),
):
    """Execute merge tasks defined in config file."""
    if category is None:
        typer.echo("Available merge categories:")
        typer.echo("  (will be loaded from config)")
        return

    # Get config and dry_run from parent context
    config = ctx.obj.get("config", {})
    dry_run = ctx.obj.get("dry_run", False)

    merge_tasks = config.get("merge", {})

    if category not in merge_tasks:
        typer.echo(f"Error: Merge category '{category}' not found in config", err=True)
        raise typer.Exit(1)

    if task is None:
        # Show available tasks in category
        typer.echo(f"Available tasks in '{category}':")
        for task_name in merge_tasks[category].keys():
            typer.echo(f"  - {task_name}")
        return

    if task not in merge_tasks[category]:
        typer.echo(f"Error: Merge task '{task}' not found in category '{category}'", err=True)
        raise typer.Exit(1)

    task_config = merge_tasks[category][task]
    command = task_config.get("command")

    if dry_run:
        typer.echo(f"[DRY RUN] Would execute merge task: {category}.{task}")
        typer.echo(f"[DRY RUN] Command: {command}")
    else:
        typer.echo(f"Executing merge task: {category}.{task}")
        # Actual execution will be implemented in Step 4
        typer.echo("(Command execution not yet implemented)")
