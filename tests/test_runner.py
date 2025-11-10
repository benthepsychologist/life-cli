# Copyright 2024 Life-CLI Contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for runner.py module."""

import logging
import subprocess
from pathlib import Path

import pytest

from life.runner import CommandRunner, expand_path


class TestCommandRunner:
    """Test command execution functionality."""

    def test_init_creates_runner(self):
        """Test CommandRunner initialization."""
        runner = CommandRunner(dry_run=False)
        assert runner.dry_run is False
        assert runner.logger is not None

    def test_substitute_variables_simple(self):
        """Test basic variable substitution."""
        runner = CommandRunner()

        command = "echo {name} {value}"
        variables = {"name": "test", "value": "123"}
        result = runner.substitute_variables(command, variables)

        assert result == "echo test 123"

    def test_substitute_variables_multiple_occurrences(self):
        """Test variable used multiple times."""
        runner = CommandRunner()

        command = "echo {var} and {var} again"
        variables = {"var": "hello"}
        result = runner.substitute_variables(command, variables)

        assert result == "echo hello and hello again"

    def test_substitute_variables_converts_to_string(self):
        """Test non-string values are converted."""
        runner = CommandRunner()

        command = "echo {number} {boolean}"
        variables = {"number": 42, "boolean": True}
        result = runner.substitute_variables(command, variables)

        assert result == "echo 42 True"

    def test_substitute_variables_missing_variable(self, caplog):
        """Test warning for unsubstituted variables."""
        runner = CommandRunner()

        command = "echo {name} {missing}"
        variables = {"name": "test"}

        with caplog.at_level(logging.WARNING):
            result = runner.substitute_variables(command, variables)

        assert result == "echo test {missing}"
        assert "Unsubstituted variables" in caplog.text
        assert "missing" in caplog.text

    def test_substitute_variables_empty(self):
        """Test substitution with no variables."""
        runner = CommandRunner()

        command = "echo hello world"
        variables = {}
        result = runner.substitute_variables(command, variables)

        assert result == "echo hello world"

    def test_substitute_variables_empty_value(self):
        """Test substitution with empty string value."""
        runner = CommandRunner()

        command = "echo '{value}' end"
        variables = {"value": ""}
        result = runner.substitute_variables(command, variables)

        assert result == "echo '' end"

    def test_substitute_variables_with_escaping(self):
        """Test variable escaping with double braces."""
        runner = CommandRunner()

        command = "echo {{literal}} and {var}"
        variables = {"var": "substituted"}
        result = runner.substitute_variables(command, variables)

        assert result == "echo {literal} and substituted"

    def test_substitute_variables_escape_only(self):
        """Test escaping without any real variables."""
        runner = CommandRunner()

        command = "echo {{name}} {{value}}"
        variables = {}
        result = runner.substitute_variables(command, variables)

        assert result == "echo {name} {value}"

    def test_substitute_variables_mixed_escape_and_vars(self):
        """Test mixed escaped and real variables."""
        runner = CommandRunner()

        # Mix of escaped literals and real substitutions
        command = "echo {{literal}} and {var} in {{json}}"
        variables = {"var": "value"}
        result = runner.substitute_variables(command, variables)

        # Escaped braces become single braces, variables get substituted
        assert result == "echo {literal} and value in {json}"

    def test_run_command_dry_run(self, caplog):
        """Test command execution in dry-run mode."""
        runner = CommandRunner(dry_run=True)

        with caplog.at_level(logging.INFO):
            runner.run("echo hello")

        assert "[DRY RUN]" in caplog.text
        assert "echo hello" in caplog.text

    def test_run_command_success(self, caplog):
        """Test successful command execution."""
        runner = CommandRunner(dry_run=False)

        with caplog.at_level(logging.INFO):
            runner.run("echo 'test output'")

        assert "Executing:" in caplog.text
        assert "echo 'test output'" in caplog.text

    def test_run_command_failure(self):
        """Test failed command raises CalledProcessError."""
        runner = CommandRunner(dry_run=False)

        with pytest.raises(subprocess.CalledProcessError):
            runner.run("exit 1")

    def test_run_command_with_substitution(self):
        """Test command execution with variable substitution."""
        runner = CommandRunner(dry_run=False)

        variables = {"message": "hello world"}
        # Use command that will succeed
        runner.run("echo {message}", variables)

    def test_run_multiple_commands_dry_run(self, caplog):
        """Test multiple command execution in dry-run mode."""
        runner = CommandRunner(dry_run=True)

        commands = [
            "echo first",
            "echo second",
            "echo third",
        ]

        with caplog.at_level(logging.INFO):
            runner.run_multiple(commands)

        assert caplog.text.count("[DRY RUN]") == 3
        assert "echo first" in caplog.text
        assert "echo second" in caplog.text
        assert "echo third" in caplog.text

    def test_run_multiple_commands_success(self, caplog):
        """Test successful execution of multiple commands."""
        runner = CommandRunner(dry_run=False)

        commands = [
            "echo 'first'",
            "echo 'second'",
        ]

        with caplog.at_level(logging.INFO):
            runner.run_multiple(commands)

        assert "Executing:" in caplog.text
        assert "echo 'first'" in caplog.text
        assert "echo 'second'" in caplog.text

    def test_run_multiple_commands_stops_on_error(self):
        """Test multiple commands stop on first error."""
        runner = CommandRunner(dry_run=False)

        commands = [
            "echo 'first'",
            "exit 1",  # This will fail
            "echo 'third'",  # This should not run
        ]

        with pytest.raises(subprocess.CalledProcessError):
            runner.run_multiple(commands)

    def test_run_multiple_with_variables(self, caplog):
        """Test multiple commands with variable substitution."""
        runner = CommandRunner(dry_run=False)

        commands = [
            "echo {name}",
            "echo {value}",
        ]
        variables = {"name": "test", "value": "123"}

        with caplog.at_level(logging.INFO):
            runner.run_multiple(commands, variables)

        # Commands should be substituted before execution
        assert "test" in caplog.text or "123" in caplog.text

    def test_run_multiple_empty_list(self, caplog):
        """Test running empty command list."""
        runner = CommandRunner(dry_run=False)

        with caplog.at_level(logging.INFO):
            runner.run_multiple([])

        # Should not crash, no commands executed


class TestExpandPath:
    """Test path expansion separately from config tests."""

    def test_expand_path_none(self):
        """Test expanding None returns empty string."""
        # Current implementation doesn't handle None, but documenting expected behavior
        # This would need to be added if paths can be None
        pass

    def test_expand_path_complex(self):
        """Test expanding complex path with tilde."""
        path = expand_path("~/workspace/test/file.txt")

        assert path.is_absolute()
        assert str(path).startswith(str(Path.home()))
        assert "workspace" in str(path)
        assert "file.txt" in str(path)
