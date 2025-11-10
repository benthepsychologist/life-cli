# Copyright 2025 Ben Mensi
# SPDX-License-Identifier: Apache-2.0

"""
Config command for Life-CLI.

Provides configuration validation, tool checking, and task inspection.
"""

import logging

import typer

from life.config_manager import full_validation, get_task_summary, validate_tools
from life.registry import is_tool_installed, list_tools

app = typer.Typer(help="Manage and validate configuration")
logger = logging.getLogger(__name__)


@app.command()
def validate(ctx: typer.Context):
    """
    Validate configuration structure and tool availability.

    Performs full validation:
    - YAML structure and required fields
    - Tool availability (checks if binaries exist on PATH)
    - Configuration consistency
    """
    config = ctx.obj.get("config", {})

    typer.echo("Validating configuration...")
    typer.echo()

    # Perform full validation
    structure_issues, tool_results = full_validation(config)

    # Report structure issues
    if structure_issues:
        typer.echo("Structure Issues:")
        for issue in structure_issues:
            typer.echo(f"  ⚠️  {issue}")
        typer.echo()
    else:
        typer.echo("✓ Configuration structure is valid")
        typer.echo()

    # Report tool availability
    if tool_results:
        typer.echo("Tool Availability:")
        all_installed = True
        for tool_name, installed, message in tool_results:
            typer.echo(f"  {message}")
            if not installed:
                all_installed = False
        typer.echo()

        if not all_installed:
            typer.echo("Some tools are not installed. See install hints above.")
            raise typer.Exit(1)
        else:
            typer.echo("✓ All required tools are installed")
    else:
        typer.echo("No tools found in configuration")

    typer.echo()
    typer.echo("Configuration validation complete!")


@app.command()
def check(ctx: typer.Context):
    """
    Check if all referenced tools are installed.

    Quick check for tool availability without full validation.
    """
    config = ctx.obj.get("config", {})

    typer.echo("Checking tool availability...")
    typer.echo()

    # Validate tools only
    tool_results = validate_tools(config)

    if not tool_results:
        typer.echo("No tools found in configuration")
        return

    all_installed = True
    for tool_name, installed, message in tool_results:
        typer.echo(f"  {message}")
        if not installed:
            all_installed = False

    typer.echo()
    if all_installed:
        typer.echo("✓ All tools are available")
    else:
        typer.echo("✗ Some tools are missing")
        raise typer.Exit(1)


@app.command("list")
def list_tasks(ctx: typer.Context):
    """
    List all configured tasks with tool information.

    Shows tasks organized by command type (sync, merge, process, status)
    with tool dependencies for each task.
    """
    config = ctx.obj.get("config", {})

    typer.echo("Configured Tasks:")
    typer.echo()

    # Get task summary
    summary = get_task_summary(config)

    # Display tasks by type
    for cmd_type in ["sync", "merge", "process", "status"]:
        tasks = summary[cmd_type]
        if not tasks:
            continue

        typer.echo(f"{cmd_type.upper()} Tasks:")
        for task in tasks:
            # Show task name and description
            typer.echo(f"  {task['name']}")
            typer.echo(f"    Description: {task['description']}")

            # Show tools
            if task["tools"]:
                tool_status = []
                for tool in task["tools"]:
                    installed = is_tool_installed(tool)
                    status = "✓" if installed else "✗"
                    tool_status.append(f"{status} {tool}")
                typer.echo(f"    Tools: {', '.join(tool_status)}")
            else:
                typer.echo("    Tools: None")

            # Show incremental status
            if task.get("incremental"):
                typer.echo("    Incremental: Yes")

            typer.echo()

    typer.echo()


@app.command()
def tools():
    """
    List all registered tools in the Life-CLI tool registry.

    Shows built-in tools with installation status and hints.
    """
    typer.echo("Registered Tools:")
    typer.echo()

    all_tools = list_tools()

    for tool in all_tools:
        installed = is_tool_installed(tool.name)
        status = "✓ Installed" if installed else "✗ Not installed"

        typer.echo(f"{tool.name} - {status}")
        typer.echo(f"  Description: {tool.description}")
        if not installed:
            typer.echo(f"  Install: {tool.install_hint}")
        typer.echo()
