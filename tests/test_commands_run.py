"""Tests for run and jobs CLI commands.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner

from life.cli import app

runner = CliRunner()


@pytest.fixture
def jobs_dir(tmp_path):
    """Create a temporary jobs directory with test jobs."""
    jobs = tmp_path / "jobs"
    jobs.mkdir()

    # Create a test job file
    (jobs / "test.yaml").write_text(
        """
jobs:
  hello:
    description: "Say hello"
    steps:
      - name: greet
        call: life_jobs.shell.run
        args:
          command: "echo Hello"

  greet_user:
    description: "Greet a specific user"
    steps:
      - name: greet
        call: life_jobs.shell.run
        args:
          command: "echo Hello {name}!"
"""
    )
    return jobs


@pytest.fixture
def config_file(tmp_path, jobs_dir):
    """Create a temporary config file."""
    config = tmp_path / ".life" / "config.yml"
    config.parent.mkdir(parents=True)
    config.write_text(
        f"""
jobs:
  dir: {jobs_dir}
  event_log: {tmp_path}/events.jsonl
"""
    )
    return config


class TestJobsListCommand:
    """Tests for 'life jobs list' command."""

    def test_list_no_jobs_dir(self, tmp_path):
        """Should error when jobs directory doesn't exist."""
        config = tmp_path / "config.yml"
        config.write_text(
            f"""
jobs:
  dir: {tmp_path}/nonexistent
"""
        )
        result = runner.invoke(app, ["--config", str(config), "jobs", "list"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_list_empty_jobs_dir(self, tmp_path):
        """Should show message when no jobs found."""
        jobs_dir = tmp_path / "jobs"
        jobs_dir.mkdir()
        config = tmp_path / "config.yml"
        config.write_text(
            f"""
jobs:
  dir: {jobs_dir}
"""
        )
        result = runner.invoke(app, ["--config", str(config), "jobs", "list"])
        assert result.exit_code == 0
        assert "No jobs found" in result.output

    def test_list_shows_jobs(self, config_file):
        """Should list available jobs with descriptions."""
        result = runner.invoke(app, ["--config", str(config_file), "jobs", "list"])
        assert result.exit_code == 0
        assert "hello" in result.output
        assert "Say hello" in result.output
        assert "greet_user" in result.output
        assert "Greet a specific user" in result.output

    def test_list_yaml_errors(self, tmp_path):
        """Should report YAML parse errors."""
        jobs_dir = tmp_path / "jobs"
        jobs_dir.mkdir()
        (jobs_dir / "bad.yaml").write_text("invalid: yaml: [")

        config = tmp_path / "config.yml"
        config.write_text(
            f"""
jobs:
  dir: {jobs_dir}
"""
        )
        result = runner.invoke(app, ["--config", str(config), "jobs", "list"])
        assert result.exit_code == 1
        assert "failed to parse" in result.output.lower()

    def test_list_yaml_errors_detailed(self, tmp_path):
        """Should show detailed errors with --errors flag."""
        jobs_dir = tmp_path / "jobs"
        jobs_dir.mkdir()
        (jobs_dir / "bad.yaml").write_text("invalid: yaml: [")

        config = tmp_path / "config.yml"
        config.write_text(
            f"""
jobs:
  dir: {jobs_dir}
"""
        )
        result = runner.invoke(app, ["--config", str(config), "jobs", "list", "--errors"])
        assert result.exit_code == 1
        assert "bad.yaml" in result.output


class TestJobsShowCommand:
    """Tests for 'life jobs show' command."""

    def test_show_existing_job(self, config_file):
        """Should display job definition."""
        result = runner.invoke(app, ["--config", str(config_file), "jobs", "show", "hello"])
        assert result.exit_code == 0
        assert "hello" in result.output
        assert "Say hello" in result.output
        assert "life_jobs.shell.run" in result.output

    def test_show_nonexistent_job(self, config_file):
        """Should error for nonexistent job."""
        result = runner.invoke(app, ["--config", str(config_file), "jobs", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestRunCommand:
    """Tests for 'life run' command."""

    def test_run_no_jobs_dir(self, tmp_path):
        """Should error when jobs directory doesn't exist."""
        config = tmp_path / "config.yml"
        config.write_text(
            f"""
jobs:
  dir: {tmp_path}/nonexistent
"""
        )
        result = runner.invoke(app, ["--config", str(config), "run", "hello"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_run_nonexistent_job(self, config_file):
        """Should error for nonexistent job."""
        result = runner.invoke(app, ["--config", str(config_file), "run", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_run_dry_run(self, config_file):
        """Should show what would execute in dry-run mode."""
        result = runner.invoke(app, ["--config", str(config_file), "--dry-run", "run", "hello"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "hello" in result.output
        assert "greet" in result.output

    def test_run_with_variables(self, config_file):
        """Should substitute variables from --var."""
        # Note: --var must come before job_id (typer/click convention: options before arguments)
        # Use --verbose to see the substituted args in output
        result = runner.invoke(
            app,
            ["--config", str(config_file), "--dry-run", "--verbose", "run", "--var", "name=World", "greet_user"],
        )
        assert result.exit_code == 0
        assert "Hello World!" in result.output

    def test_run_missing_variable(self, config_file):
        """Should error when required variable is missing."""
        result = runner.invoke(
            app, ["--config", str(config_file), "--dry-run", "run", "greet_user"]
        )
        assert result.exit_code == 1
        assert "unsubstituted" in result.output.lower()
        assert "name" in result.output

    def test_run_invalid_var_format(self, config_file):
        """Should error for invalid --var format."""
        # Note: --var must come before job_id
        result = runner.invoke(
            app,
            ["--config", str(config_file), "--dry-run", "run", "--var", "invalid", "hello"],
        )
        assert result.exit_code == 1
        assert "KEY=VALUE" in result.output

    def test_run_verbose(self, config_file):
        """Should show details in verbose mode."""
        result = runner.invoke(
            app, ["--config", str(config_file), "--dry-run", "--verbose", "run", "hello"]
        )
        assert result.exit_code == 0
        assert "call:" in result.output
        assert "life_jobs.shell.run" in result.output


class TestRunCommandEventLogging:
    """Tests for event logging in run command."""

    def test_run_creates_event_log(self, tmp_path, jobs_dir):
        """Should create event log file."""
        event_log = tmp_path / "events.jsonl"
        config = tmp_path / "config.yml"
        config.write_text(
            f"""
jobs:
  dir: {jobs_dir}
  event_log: {event_log}
"""
        )

        result = runner.invoke(app, ["--config", str(config), "--dry-run", "run", "hello"])
        assert result.exit_code == 0
        assert event_log.exists()

        events = [json.loads(line) for line in event_log.read_text().strip().split("\n")]
        event_types = [e["event_type"] for e in events]
        assert "job.started" in event_types
        assert "job.completed" in event_types
