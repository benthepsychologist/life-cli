# Copyright 2025 Ben Mensi
# SPDX-License-Identifier: Apache-2.0

"""Tests for config_manager.py module."""


from life.config_manager import (
    extract_tools_from_command,
    extract_tools_from_config,
    full_validation,
    get_task_summary,
    validate_tools,
)


class TestExtractToolsFromCommand:
    """Test tool extraction from command strings."""

    def test_simple_command(self):
        """Test extracting tool from simple command."""
        tools = extract_tools_from_command("msg sync")
        assert tools == ["msg"]

    def test_command_with_path(self):
        """Test extracting tool from command with path."""
        tools = extract_tools_from_command("/usr/bin/msg sync")
        assert tools == ["msg"]

    def test_command_with_sudo(self):
        """Test extracting tool from command with sudo."""
        tools = extract_tools_from_command("sudo msg sync")
        assert tools == ["msg"]

    def test_command_with_env(self):
        """Test extracting tool from command with env."""
        tools = extract_tools_from_command("env VAR=value msg sync")
        assert tools == ["msg"]

    def test_empty_command(self):
        """Test extracting from empty command."""
        tools = extract_tools_from_command("")
        assert tools == []

    def test_command_with_variables(self):
        """Test extracting tool from command with variables."""
        tools = extract_tools_from_command("gws sheets export {sheet_id} {output}")
        assert tools == ["gws"]


class TestExtractToolsFromConfig:
    """Test tool extraction from full config."""

    def test_extract_from_sync_tasks(self):
        """Test extracting tools from sync tasks."""
        config = {
            "sync": {
                "contacts": {
                    "command": "msg contacts sync",
                },
                "calendar": {
                    "command": "cal sync",
                },
            }
        }

        tools = extract_tools_from_config(config)
        assert "msg" in tools
        assert "cal" in tools

    def test_extract_from_multi_commands(self):
        """Test extracting tools from commands array."""
        config = {
            "sync": {
                "workflow": {
                    "commands": [
                        "msg contacts sync",
                        "gws sheets export",
                        "dataverse query",
                    ]
                }
            }
        }

        tools = extract_tools_from_config(config)
        assert "msg" in tools
        assert "gws" in tools
        assert "dataverse" in tools

    def test_extract_from_merge_tasks(self):
        """Test extracting tools from merge tasks (nested structure)."""
        config = {
            "merge": {
                "clients": {
                    "aggregate": {
                        "command": "gws sheets merge",
                    }
                }
            }
        }

        tools = extract_tools_from_config(config)
        assert "gws" in tools

    def test_extract_from_process_tasks(self):
        """Test extracting tools from process tasks."""
        config = {
            "process": {
                "transform": {
                    "command": "python transform.py",
                }
            }
        }

        tools = extract_tools_from_config(config)
        assert "python" in tools

    def test_extract_from_status_tasks(self):
        """Test extracting tools from status tasks."""
        config = {
            "status": {
                "report": {
                    "command": "msg status check",
                }
            }
        }

        tools = extract_tools_from_config(config)
        assert "msg" in tools

    def test_extract_from_mixed_config(self):
        """Test extracting tools from config with multiple command types."""
        config = {
            "sync": {
                "contacts": {"command": "msg sync"},
            },
            "merge": {
                "clients": {
                    "aggregate": {"command": "gws merge"},
                }
            },
            "process": {
                "transform": {"command": "python process.py"},
            },
            "status": {
                "check": {"command": "cal status"},
            },
        }

        tools = extract_tools_from_config(config)
        assert "msg" in tools
        assert "gws" in tools
        assert "python" in tools
        assert "cal" in tools

    def test_extract_unique_tools(self):
        """Test that duplicate tools are deduplicated."""
        config = {
            "sync": {
                "task1": {"command": "msg sync"},
                "task2": {"command": "msg contacts"},
                "task3": {"command": "msg calendar"},
            }
        }

        tools = extract_tools_from_config(config)
        # Should only have msg once (set deduplication)
        assert len([t for t in tools if t == "msg"]) == 1


class TestValidateTools:
    """Test tool validation."""

    def test_validate_installed_tool(self):
        """Test validating a tool that's installed."""
        config = {
            "sync": {
                "test": {"command": "python --version"},
            }
        }

        results = validate_tools(config)
        # Find python in results
        python_result = [r for r in results if r[0] == "python"]
        assert len(python_result) == 1
        tool_name, installed, message = python_result[0]
        # Python should be installed
        assert installed is True
        assert "✓" in message

    def test_validate_missing_tool(self):
        """Test validating a tool that's not installed."""
        config = {
            "sync": {
                "test": {"command": "definitely-not-installed-xyz sync"},
            }
        }

        results = validate_tools(config)
        tool_name, installed, message = results[0]
        assert tool_name == "definitely-not-installed-xyz"
        assert installed is False
        assert "✗" in message

    def test_validate_registered_tool(self):
        """Test validating a registered tool."""
        config = {
            "sync": {
                "test": {"command": "msg sync"},
            }
        }

        results = validate_tools(config)
        msg_result = [r for r in results if r[0] == "msg"]
        assert len(msg_result) == 1

        tool_name, installed, message = msg_result[0]
        assert tool_name == "msg"
        # Message should contain either install hint or description
        assert len(message) > 0


class TestGetTaskSummary:
    """Test task summary generation."""

    def test_summary_sync_tasks(self):
        """Test generating summary for sync tasks."""
        config = {
            "sync": {
                "contacts": {
                    "description": "Sync contacts",
                    "command": "msg contacts sync",
                    "incremental_field": "modifiedDateTime",
                    "state_file": "~/.life/contacts.state.json",
                }
            }
        }

        summary = get_task_summary(config)
        assert len(summary["sync"]) == 1

        task = summary["sync"][0]
        assert task["name"] == "contacts"
        assert task["description"] == "Sync contacts"
        assert "msg" in task["tools"]
        assert task["incremental"] is True

    def test_summary_merge_tasks(self):
        """Test generating summary for merge tasks."""
        config = {
            "merge": {
                "clients": {
                    "aggregate": {
                        "description": "Aggregate client data",
                        "command": "gws sheets merge",
                    }
                }
            }
        }

        summary = get_task_summary(config)
        assert len(summary["merge"]) == 1

        task = summary["merge"][0]
        assert task["name"] == "clients.aggregate"
        assert task["description"] == "Aggregate client data"
        assert "gws" in task["tools"]
        assert task["incremental"] is False

    def test_summary_with_multi_commands(self):
        """Test summary for tasks with multiple commands."""
        config = {
            "sync": {
                "workflow": {
                    "description": "Multi-step workflow",
                    "commands": [
                        "msg sync",
                        "gws export",
                    ],
                }
            }
        }

        summary = get_task_summary(config)
        task = summary["sync"][0]
        assert task["name"] == "workflow"
        assert "msg" in task["tools"]
        assert "gws" in task["tools"]

    def test_summary_all_command_types(self):
        """Test summary with all command types."""
        config = {
            "sync": {
                "contacts": {"command": "msg sync", "description": "Sync contacts"}
            },
            "merge": {
                "clients": {
                    "aggregate": {"command": "gws merge", "description": "Merge data"}
                }
            },
            "process": {
                "transform": {"command": "python process.py", "description": "Transform"}
            },
            "status": {
                "report": {"command": "cal status", "description": "Status check"}
            },
        }

        summary = get_task_summary(config)
        assert len(summary["sync"]) == 1
        assert len(summary["merge"]) == 1
        assert len(summary["process"]) == 1
        assert len(summary["status"]) == 1


class TestFullValidation:
    """Test full validation."""

    def test_full_validation_valid_config(self):
        """Test full validation on a valid config."""
        config = {
            "workspace": "~/test",
            "sync": {
                "test": {
                    "command": "python --version",
                    "output": "~/output.json",
                }
            },
        }

        structure_issues, tool_results = full_validation(config)
        # Should have no structure issues
        assert len(structure_issues) == 0
        # Should have tool results
        assert len(tool_results) > 0

    def test_full_validation_with_issues(self):
        """Test full validation on config with issues."""
        config = {
            "workspace": "~/test",
            "sync": {
                "test": {
                    # Missing command - structure issue
                    "output": "~/output.json",
                }
            },
        }

        structure_issues, tool_results = full_validation(config)
        # Should have structure issues (missing command)
        assert len(structure_issues) > 0

    def test_full_validation_returns_tuples(self):
        """Test that full validation returns correct types."""
        config = {
            "sync": {
                "test": {"command": "python --version"}
            }
        }

        structure_issues, tool_results = full_validation(config)
        assert isinstance(structure_issues, list)
        assert isinstance(tool_results, list)

        # Tool results should be tuples
        if tool_results:
            assert isinstance(tool_results[0], tuple)
            assert len(tool_results[0]) == 3
