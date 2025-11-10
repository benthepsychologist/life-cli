# Copyright 2025 Ben Mensi
# SPDX-License-Identifier: Apache-2.0

"""
Tool registry for Life-CLI.

Maintains a registry of known CLI tools with metadata and installation hints.
"""

import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ToolInfo:
    """Metadata for a registered CLI tool."""

    name: str
    binary: str
    description: str
    install_hint: str


# Built-in tool registry
TOOL_REGISTRY: Dict[str, ToolInfo] = {
    "msg": ToolInfo(
        name="msg",
        binary="msg",
        description="Microsoft Graph CLI for email, calendar, and contacts",
        install_hint="Install from: https://github.com/yourusername/msg-cli",
    ),
    "gws": ToolInfo(
        name="gws",
        binary="gws",
        description="Google Workspace CLI for Drive, Sheets, and Docs",
        install_hint="Install from: https://github.com/yourusername/gws-cli",
    ),
    "cal": ToolInfo(
        name="cal",
        binary="cal",
        description="Calendar sync and management tool",
        install_hint="Install from: https://github.com/yourusername/cal-cli",
    ),
    "dataverse": ToolInfo(
        name="dataverse",
        binary="dataverse",
        description="Microsoft Dataverse CLI for CRM data access",
        install_hint="Install from: https://github.com/yourusername/dataverse-cli",
    ),
}


def is_tool_installed(tool_name: str) -> bool:
    """
    Check if a tool is installed and available on PATH.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool binary is found on PATH, False otherwise
    """
    tool_info = TOOL_REGISTRY.get(tool_name)
    if not tool_info:
        # For unknown tools, try to find the tool name itself on PATH
        return shutil.which(tool_name) is not None

    # For registered tools, check if binary exists
    return shutil.which(tool_info.binary) is not None


def get_tool_info(tool_name: str) -> Optional[ToolInfo]:
    """
    Get metadata for a registered tool.

    Args:
        tool_name: Name of the tool

    Returns:
        ToolInfo if tool is registered, None otherwise
    """
    return TOOL_REGISTRY.get(tool_name)


def list_tools() -> List[ToolInfo]:
    """
    List all registered tools.

    Returns:
        List of ToolInfo objects for all registered tools
    """
    return list(TOOL_REGISTRY.values())


def register_tool(tool_info: ToolInfo) -> None:
    """
    Register a new tool (for extensibility).

    Args:
        tool_info: ToolInfo object to register
    """
    TOOL_REGISTRY[tool_info.name] = tool_info
