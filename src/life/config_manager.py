# Copyright 2025 Ben Mensi
# SPDX-License-Identifier: Apache-2.0

"""
Config manager for Life-CLI.

Provides semantic validation and analysis of Life-CLI configuration.
"""

from typing import Any, Dict, List, Set, Tuple

from life.registry import get_tool_info, is_tool_installed
from life.validation import validate_config


def extract_tools_from_command(command: str) -> List[str]:
    """
    Extract tool names from a command string.

    Args:
        command: Command string (may contain variables)

    Returns:
        List of tool names found in the command
    """
    # Split command and get the first token (the actual command)
    # Handle shell redirects, pipes, etc.
    parts = command.strip().split()
    if not parts:
        return []

    # Get first command (before any pipes, redirects, etc.)
    first_cmd = parts[0]

    # Remove shell prefixes (sudo, env, etc.)
    shell_prefixes = {"sudo", "env", "time", "nice", "nohup"}
    idx = 0
    while idx < len(parts) and parts[idx] in shell_prefixes:
        idx += 1

    # Skip environment variable assignments (VAR=value)
    while idx < len(parts) and "=" in parts[idx]:
        idx += 1

    # Get the actual command
    if idx < len(parts):
        first_cmd = parts[idx]
    else:
        return []

    # Extract just the binary name (strip path)
    tool_name = first_cmd.split("/")[-1]

    return [tool_name] if tool_name else []


def extract_tools_from_config(config: Dict[str, Any]) -> Set[str]:
    """
    Extract all tools used across all tasks in config.

    Args:
        config: Life-CLI configuration dictionary

    Returns:
        Set of unique tool names referenced in commands
    """
    tools = set()

    # Check sync tasks
    for task_name, task_config in config.get("sync", {}).items():
        # Single command
        if "command" in task_config:
            tools.update(extract_tools_from_command(task_config["command"]))

        # Multiple commands
        if "commands" in task_config:
            for cmd in task_config["commands"]:
                tools.update(extract_tools_from_command(cmd))

    # Check merge tasks (nested structure)
    for category, tasks in config.get("merge", {}).items():
        for task_name, task_config in tasks.items():
            if "command" in task_config:
                tools.update(extract_tools_from_command(task_config["command"]))
            if "commands" in task_config:
                for cmd in task_config["commands"]:
                    tools.update(extract_tools_from_command(cmd))

    # Check process tasks
    for task_name, task_config in config.get("process", {}).items():
        if "command" in task_config:
            tools.update(extract_tools_from_command(task_config["command"]))
        if "commands" in task_config:
            for cmd in task_config["commands"]:
                tools.update(extract_tools_from_command(cmd))

    # Check status tasks
    for task_name, task_config in config.get("status", {}).items():
        if "command" in task_config:
            tools.update(extract_tools_from_command(task_config["command"]))
        if "commands" in task_config:
            for cmd in task_config["commands"]:
                tools.update(extract_tools_from_command(cmd))

    return tools


def validate_tools(config: Dict[str, Any]) -> List[Tuple[str, bool, str]]:
    """
    Validate that all tools referenced in config are installed.

    Args:
        config: Life-CLI configuration dictionary

    Returns:
        List of tuples: (tool_name, is_installed, message)
    """
    tools = extract_tools_from_config(config)
    results = []

    for tool in sorted(tools):
        installed = is_tool_installed(tool)
        tool_info = get_tool_info(tool)

        if installed:
            if tool_info:
                message = f"✓ {tool_info.description}"
            else:
                message = "✓ Tool found on PATH"
        else:
            if tool_info:
                message = f"✗ Not installed. {tool_info.install_hint}"
            else:
                message = "✗ Not found on PATH (unknown tool)"

        results.append((tool, installed, message))

    return results


def get_task_summary(config: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate a summary of all tasks in the config.

    Args:
        config: Life-CLI configuration dictionary

    Returns:
        Dictionary mapping command types to lists of task info
    """
    summary = {
        "sync": [],
        "merge": [],
        "process": [],
        "status": [],
    }

    # Sync tasks
    for task_name, task_config in config.get("sync", {}).items():
        tools = set()
        if "command" in task_config:
            tools.update(extract_tools_from_command(task_config["command"]))
        if "commands" in task_config:
            for cmd in task_config["commands"]:
                tools.update(extract_tools_from_command(cmd))

        summary["sync"].append(
            {
                "name": task_name,
                "description": task_config.get("description", "No description"),
                "tools": sorted(tools),
                "incremental": "incremental_field" in task_config,
            }
        )

    # Merge tasks (nested structure)
    for category, tasks in config.get("merge", {}).items():
        for task_name, task_config in tasks.items():
            tools = set()
            if "command" in task_config:
                tools.update(extract_tools_from_command(task_config["command"]))
            if "commands" in task_config:
                for cmd in task_config["commands"]:
                    tools.update(extract_tools_from_command(cmd))

            summary["merge"].append(
                {
                    "name": f"{category}.{task_name}",
                    "description": task_config.get("description", "No description"),
                    "tools": sorted(tools),
                    "incremental": False,
                }
            )

    # Process tasks
    for task_name, task_config in config.get("process", {}).items():
        tools = set()
        if "command" in task_config:
            tools.update(extract_tools_from_command(task_config["command"]))
        if "commands" in task_config:
            for cmd in task_config["commands"]:
                tools.update(extract_tools_from_command(cmd))

        summary["process"].append(
            {
                "name": task_name,
                "description": task_config.get("description", "No description"),
                "tools": sorted(tools),
                "incremental": False,
            }
        )

    # Status tasks
    for task_name, task_config in config.get("status", {}).items():
        tools = set()
        if "command" in task_config:
            tools.update(extract_tools_from_command(task_config["command"]))
        if "commands" in task_config:
            for cmd in task_config["commands"]:
                tools.update(extract_tools_from_command(cmd))

        summary["status"].append(
            {
                "name": task_name,
                "description": task_config.get("description", "No description"),
                "tools": sorted(tools),
                "incremental": False,
            }
        )

    return summary


def full_validation(config: Dict[str, Any]) -> Tuple[List[str], List[Tuple[str, bool, str]]]:
    """
    Perform full validation: structure + tool availability.

    Args:
        config: Life-CLI configuration dictionary

    Returns:
        Tuple of (structure_issues, tool_results)
    """
    # Validate structure
    structure_issues = validate_config(config)

    # Validate tools
    tool_results = validate_tools(config)

    return structure_issues, tool_results
