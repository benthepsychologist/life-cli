"""
Configuration loader for Life-CLI.

Loads and validates YAML configuration files.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, tries ~/life.yml then ./life.yml

    Returns:
        Dictionary containing configuration

    Raises:
        FileNotFoundError: If config file not found
        yaml.YAMLError: If config file is invalid YAML
    """
    # Determine config file path
    if config_path:
        path = Path(config_path).expanduser()
    else:
        # Try default locations
        home_config = Path.home() / "life.yml"
        local_config = Path.cwd() / "life.yml"

        if home_config.exists():
            path = home_config
        elif local_config.exists():
            path = local_config
        else:
            raise FileNotFoundError(
                "No config file found. Tried:\n"
                f"  - {home_config}\n"
                f"  - {local_config}\n"
                "Use --config to specify a custom location."
            )

    # Load YAML
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing config file {path}: {e}")

    if config is None:
        config = {}

    # Expand workspace path if present
    if "workspace" in config:
        config["workspace"] = str(Path(config["workspace"]).expanduser())

    return config


def get_workspace(config: Dict[str, Any]) -> Path:
    """
    Get workspace path from config, with fallback to current directory.

    Args:
        config: Configuration dictionary

    Returns:
        Path object for workspace directory
    """
    workspace = config.get("workspace", ".")
    return Path(workspace).expanduser().resolve()
