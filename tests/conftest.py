# Copyright 2024 Life-CLI Contributors
# SPDX-License-Identifier: Apache-2.0

"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing."""
    return {
        "workspace": "~/test-workspace",
        "sync": {
            "contacts": {
                "command": "echo 'syncing contacts'",
                "description": "Sync contacts from API",
                "output": "~/data/contacts.json",
            },
            "incremental-test": {
                "command": "echo 'syncing incremental' {extra_args}",
                "description": "Test incremental sync",
                "incremental_field": "modified_on",
                "state_file": "~/.test-state.json",
                "output": "~/data/incremental.json",
            },
        },
        "merge": {
            "clients": {
                "sessions": {
                    "command": "echo 'merging sessions'",
                    "description": "Merge client sessions",
                }
            }
        },
        "process": {
            "assessments": {
                "command": "echo 'processing assessments'",
                "description": "Process assessment data",
            }
        },
        "status": {
            "weekly-report": {
                "command": "echo 'generating report'",
                "description": "Weekly status report",
            }
        },
    }


@pytest.fixture
def config_file(temp_dir, sample_config):
    """Create a temporary config file."""
    config_path = temp_dir / "life.yml"
    import yaml
    with open(config_path, "w") as f:
        yaml.dump(sample_config, f)
    return config_path


@pytest.fixture
def state_file(temp_dir):
    """Create a temporary state file path."""
    return temp_dir / "test-state.json"


@pytest.fixture
def sample_state() -> Dict[str, Any]:
    """Sample state data for testing."""
    return {
        "contacts": {
            "modified_on": "2024-11-01T12:00:00Z",
            "last_run": "2024-11-10T10:00:00Z",
        },
        "incremental-test": {
            "modified_on": "2024-11-09T15:30:00Z",
            "last_run": "2024-11-10T09:00:00Z",
        },
    }
