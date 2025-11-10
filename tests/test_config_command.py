# Copyright 2025 Ben Mensi
# SPDX-License-Identifier: Apache-2.0

"""Tests for config command."""

from typer.testing import CliRunner

from life.cli import app

runner = CliRunner()


class TestConfigValidate:
    """Test config validate command."""

    def test_validate_with_valid_config(self, tmp_path):
        """Test validate command with valid config."""
        config_file = tmp_path / "life.yml"
        config_file.write_text(
            """
workspace: ~/test
sync:
  test:
    command: python --version
    output: ~/output.json
"""
        )

        result = runner.invoke(app, ["--config", str(config_file), "config", "validate"])
        assert result.exit_code == 0
        assert "Configuration structure is valid" in result.stdout
        assert "Tool Availability:" in result.stdout

    def test_validate_with_invalid_config(self, tmp_path):
        """Test validate command with invalid config."""
        config_file = tmp_path / "life.yml"
        config_file.write_text(
            """
workspace: ~/test
sync:
  test:
    # Missing command - should trigger validation error
    output: ~/output.json
"""
        )

        result = runner.invoke(app, ["--config", str(config_file), "config", "validate"])
        # Should fail due to missing command
        assert "Structure Issues:" in result.stdout

    def test_validate_with_missing_tool(self, tmp_path):
        """Test validate command with missing tool."""
        config_file = tmp_path / "life.yml"
        config_file.write_text(
            """
workspace: ~/test
sync:
  test:
    command: definitely-not-a-real-tool sync
    output: ~/output.json
"""
        )

        result = runner.invoke(app, ["--config", str(config_file), "config", "validate"])
        # Should exit with error due to missing tool
        assert result.exit_code == 1
        assert "not installed" in result.stdout.lower() or "not found" in result.stdout.lower()


class TestConfigCheck:
    """Test config check command."""

    def test_check_with_installed_tools(self, tmp_path):
        """Test check command with installed tools."""
        config_file = tmp_path / "life.yml"
        config_file.write_text(
            """
workspace: ~/test
sync:
  test:
    command: python --version
"""
        )

        result = runner.invoke(app, ["--config", str(config_file), "config", "check"])
        assert result.exit_code == 0
        assert "All tools are available" in result.stdout

    def test_check_with_missing_tools(self, tmp_path):
        """Test check command with missing tools."""
        config_file = tmp_path / "life.yml"
        config_file.write_text(
            """
workspace: ~/test
sync:
  test:
    command: definitely-not-installed-xyz sync
"""
        )

        result = runner.invoke(app, ["--config", str(config_file), "config", "check"])
        assert result.exit_code == 1
        assert "Some tools are missing" in result.stdout


class TestConfigList:
    """Test config list command."""

    def test_list_tasks(self, tmp_path):
        """Test list command showing all tasks."""
        config_file = tmp_path / "life.yml"
        config_file.write_text(
            """
workspace: ~/test
sync:
  contacts:
    description: Sync contacts
    command: python sync_contacts.py
    incremental_field: modifiedDateTime
    state_file: ~/.life/contacts.state.json
merge:
  clients:
    aggregate:
      description: Aggregate client data
      command: python merge_clients.py
process:
  transform:
    description: Transform data
    command: python transform.py
status:
  report:
    description: Generate report
    command: python report.py
"""
        )

        result = runner.invoke(app, ["--config", str(config_file), "config", "list"])
        assert result.exit_code == 0

        # Check that all command types are listed
        assert "SYNC Tasks:" in result.stdout
        assert "MERGE Tasks:" in result.stdout
        assert "PROCESS Tasks:" in result.stdout
        assert "STATUS Tasks:" in result.stdout

        # Check specific task names
        assert "contacts" in result.stdout
        assert "clients.aggregate" in result.stdout
        assert "transform" in result.stdout
        assert "report" in result.stdout

        # Check descriptions
        assert "Sync contacts" in result.stdout
        assert "Aggregate client data" in result.stdout

        # Check incremental marker
        assert "Incremental: Yes" in result.stdout

    def test_list_empty_config(self, tmp_path):
        """Test list command with empty config."""
        config_file = tmp_path / "life.yml"
        config_file.write_text("workspace: ~/test\n")

        result = runner.invoke(app, ["--config", str(config_file), "config", "list"])
        assert result.exit_code == 0


class TestConfigTools:
    """Test config tools command."""

    def test_tools_command(self, tmp_path):
        """Test tools command listing registered tools."""
        config_file = tmp_path / "life.yml"
        config_file.write_text("workspace: ~/test\n")

        result = runner.invoke(app, ["--config", str(config_file), "config", "tools"])
        assert result.exit_code == 0
        assert "Registered Tools:" in result.stdout

        # Check that built-in tools are listed
        assert "msg" in result.stdout
        assert "gws" in result.stdout
        assert "cal" in result.stdout
        assert "dataverse" in result.stdout

        # Check for install hints
        assert "Install:" in result.stdout or "Installed" in result.stdout
