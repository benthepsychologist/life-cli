# Copyright 2024 Life-CLI Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for validation.py module."""


from life.validation import VALID_TOP_LEVEL_KEYS, suggest_fix, validate_config


class TestValidateConfig:
    """Test configuration validation."""

    def test_valid_config_no_issues(self):
        """Test that valid config returns no issues."""
        config = {
            "workspace": "~/test",
            "sync": {
                "test-task": {
                    "command": "echo test",
                    "description": "Test task",
                }
            },
        }
        issues = validate_config(config)
        assert issues == []

    def test_unknown_top_level_key(self):
        """Test detection of unknown top-level keys."""
        config = {
            "synk": {"task": {"command": "echo test"}},  # Typo: synk instead of sync
            "workspace": "~/test",
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "synk" in issues[0]
        assert "Unknown top-level config keys" in issues[0]

    def test_missing_command_field(self):
        """Test detection of missing command field."""
        config = {
            "sync": {
                "test-task": {
                    "description": "Test task",
                    "output": "~/output.json",
                }
            }
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "Missing required field 'command'" in issues[0]

    def test_both_command_and_commands(self):
        """Test detection of both command and commands fields."""
        config = {
            "sync": {
                "test-task": {
                    "command": "echo test",
                    "commands": ["echo test1", "echo test2"],
                }
            }
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "Cannot have both" in issues[0]

    def test_commands_must_be_list(self):
        """Test that commands field must be a list."""
        config = {
            "sync": {
                "test-task": {
                    "commands": "echo test",  # Should be a list
                }
            }
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "'commands' must be a list" in issues[0]

    def test_incremental_field_without_state_file(self):
        """Test that incremental_field requires state_file."""
        config = {
            "sync": {
                "test-task": {
                    "command": "echo test",
                    "incremental_field": "modified_on",
                    # Missing state_file
                }
            }
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "'incremental_field' requires 'state_file'" in issues[0]

    def test_state_file_without_incremental_field(self):
        """Test that state_file requires incremental_field."""
        config = {
            "sync": {
                "test-task": {
                    "command": "echo test",
                    "state_file": "~/.state.json",
                    # Missing incremental_field
                }
            }
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "'state_file' requires 'incremental_field'" in issues[0]

    def test_valid_incremental_sync(self):
        """Test valid incremental sync configuration."""
        config = {
            "sync": {
                "test-task": {
                    "command": "echo test {extra_args}",
                    "incremental_field": "modified_on",
                    "state_file": "~/.state.json",
                }
            }
        }
        issues = validate_config(config)
        assert issues == []

    def test_nested_merge_tasks(self):
        """Test validation of nested merge tasks."""
        config = {
            "merge": {
                "clients": {
                    "sessions": {
                        "command": "jq merge",
                        "output": "~/output.json",
                    },
                    "calendar": {
                        "command": "jq merge",
                        "output": "~/output2.json",
                    },
                }
            }
        }
        issues = validate_config(config)
        assert issues == []

    def test_category_not_dict(self):
        """Test detection of non-dict category value."""
        config = {
            "sync": "not a dictionary",
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "'sync' must be a dictionary" in issues[0]

    def test_task_not_dict(self):
        """Test detection of non-dict task value."""
        config = {
            "sync": {
                "test-task": "not a dictionary",
            }
        }
        issues = validate_config(config)
        assert len(issues) == 1
        assert "Task config must be a dictionary" in issues[0]

    def test_multiple_issues(self):
        """Test that multiple issues are all reported."""
        config = {
            "synk": {"task": {"command": "echo"}},  # Unknown top-level key
            "sync": {
                "task1": {"description": "missing command"},  # Missing command
                "task2": {
                    "incremental_field": "modified_on"  # Missing state_file and command
                },
            },
        }
        issues = validate_config(config)
        assert len(issues) >= 3  # At least 3 issues

    def test_variables_field_recognized(self):
        """Test that 'variables' field is recognized."""
        config = {
            "sync": {
                "test-task": {
                    "command": "echo {custom_var}",
                    "variables": {
                        "custom_var": "value",
                    },
                }
            }
        }
        issues = validate_config(config)
        assert issues == []


class TestSuggestFix:
    """Test typo suggestion functionality."""

    def test_suggest_close_match(self):
        """Test suggestion for close match."""
        suggestion = suggest_fix("synk", VALID_TOP_LEVEL_KEYS)
        assert suggestion == "sync"

    def test_suggest_no_match(self):
        """Test no suggestion for distant match."""
        suggestion = suggest_fix("completely_different", VALID_TOP_LEVEL_KEYS)
        assert suggestion == ""

    def test_suggest_exact_match(self):
        """Test suggestion for exact match."""
        suggestion = suggest_fix("sync", VALID_TOP_LEVEL_KEYS)
        assert suggestion == "sync"

    def test_suggest_case_insensitive(self):
        """Test case-insensitive suggestions."""
        suggestion = suggest_fix("SYNC", VALID_TOP_LEVEL_KEYS)
        assert suggestion == "sync"
