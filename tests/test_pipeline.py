"""Tests for pipeline processor and commands.

Tests the pipeline verb and its underlying processor functions.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from life.cli import app
from life_jobs.pipeline import (
    _to_bool,
    clear_views_directory,
    get_vault_statistics,
    run_lorchestra,
)

runner = CliRunner()


# =============================================================================
# Processor Tests: _to_bool helper
# =============================================================================


class TestToBool:
    """Tests for _to_bool helper function."""

    def test_bool_true(self):
        """Boolean True should return True."""
        assert _to_bool(True) is True

    def test_bool_false(self):
        """Boolean False should return False."""
        assert _to_bool(False) is False

    def test_string_true(self):
        """String 'true' should return True."""
        assert _to_bool("true") is True
        assert _to_bool("True") is True
        assert _to_bool("TRUE") is True

    def test_string_false(self):
        """String 'false' should return False."""
        assert _to_bool("false") is False
        assert _to_bool("False") is False

    def test_string_yes_one(self):
        """String '1' and 'yes' should return True."""
        assert _to_bool("1") is True
        assert _to_bool("yes") is True

    def test_string_no_zero(self):
        """String '0' and 'no' should return False."""
        assert _to_bool("0") is False
        assert _to_bool("no") is False


# =============================================================================
# Processor Tests: run_lorchestra
# =============================================================================


class TestRunLorchestra:
    """Tests for run_lorchestra processor function."""

    def test_run_lorchestra_not_installed(self):
        """Should return helpful error when lorchestra is not in PATH."""
        with patch("shutil.which", return_value=None):
            result = run_lorchestra("pipeline.ingest")

        assert result["job_id"] == "pipeline.ingest"
        assert result["success"] is False
        assert result["exit_code"] == -1
        assert "not installed" in result["error_message"]

    def test_run_lorchestra_success(self):
        """Should return success result when lorchestra exits 0."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Job completed successfully"
        mock_result.stderr = ""

        with patch("shutil.which", return_value="/usr/bin/lorchestra"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_lorchestra("pipeline.ingest")

        assert result["job_id"] == "pipeline.ingest"
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert result["stdout"] == "Job completed successfully"
        assert result["error_message"] is None

        # Verify correct command was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["lorchestra", "run", "pipeline.ingest"]

    def test_run_lorchestra_failure(self):
        """Should capture exit code and error message on failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: job failed\nDetails here"

        with patch("shutil.which", return_value="/usr/bin/lorchestra"):
            with patch("subprocess.run", return_value=mock_result):
                result = run_lorchestra("pipeline.ingest")

        assert result["job_id"] == "pipeline.ingest"
        assert result["success"] is False
        assert result["exit_code"] == 1
        assert "exited with code 1" in result["error_message"]
        assert "Error: job failed" in result["error_message"]

    def test_run_lorchestra_dry_run(self):
        """Should pass --dry-run flag to lorchestra."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "DRY RUN: would execute..."
        mock_result.stderr = ""

        with patch("shutil.which", return_value="/usr/bin/lorchestra"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_lorchestra("pipeline.ingest", dry_run=True)

        assert result["success"] is True

        # Verify --dry-run was passed
        call_args = mock_run.call_args
        assert call_args[0][0] == ["lorchestra", "run", "pipeline.ingest", "--dry-run"]

    def test_run_lorchestra_verbose_streams_output(self):
        """Verbose mode should not capture output (streams to terminal)."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("shutil.which", return_value="/usr/bin/lorchestra"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = run_lorchestra("pipeline.ingest", verbose=True)

        assert result["success"] is True
        # In verbose mode, stdout/stderr are empty (streamed, not captured)
        assert result["stdout"] == ""
        assert result["stderr"] == ""

        # Verify capture_output was NOT passed (defaults to False)
        call_args = mock_run.call_args
        assert "capture_output" not in call_args.kwargs or not call_args.kwargs.get(
            "capture_output"
        )

    def test_run_lorchestra_duration_tracked(self):
        """Should track execution duration in milliseconds."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("shutil.which", return_value="/usr/bin/lorchestra"):
            with patch("subprocess.run", return_value=mock_result):
                result = run_lorchestra("pipeline.ingest")

        assert "duration_ms" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0

    def test_run_lorchestra_string_true_converts_to_bool(self):
        """String 'true' from job runner should be converted to boolean."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("shutil.which", return_value="/usr/bin/lorchestra"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                # Pass string "true" as job runner does
                result = run_lorchestra("pipeline.ingest", dry_run="true")

        # Verify --dry-run was passed (conversion worked)
        call_args = mock_run.call_args
        assert "--dry-run" in call_args[0][0]


# =============================================================================
# Processor Tests: clear_views_directory
# =============================================================================


class TestClearViewsDirectory:
    """Tests for clear_views_directory processor function."""

    def test_clear_views_directory(self, tmp_path):
        """Should delete all files in views directory."""
        # Setup: create vault/views with some files
        views_dir = tmp_path / "views"
        views_dir.mkdir()
        (views_dir / "file1.json").write_text("{}")
        (views_dir / "file2.json").write_text("{}")
        subdir = views_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.json").write_text("{}")

        # Execute
        deleted = clear_views_directory(str(tmp_path), dry_run=False)

        # Verify files were deleted
        assert len(deleted) == 3  # file1, file2, subdir
        assert not (views_dir / "file1.json").exists()
        assert not (views_dir / "file2.json").exists()
        assert not subdir.exists()
        # views directory itself should still exist
        assert views_dir.exists()

    def test_clear_views_directory_dry_run(self, tmp_path):
        """Dry run should report files without deleting."""
        # Setup
        views_dir = tmp_path / "views"
        views_dir.mkdir()
        (views_dir / "file1.json").write_text("{}")
        (views_dir / "file2.json").write_text("{}")

        # Execute with dry_run=True
        deleted = clear_views_directory(str(tmp_path), dry_run=True)

        # Verify files were NOT deleted
        assert len(deleted) == 2
        assert (views_dir / "file1.json").exists()
        assert (views_dir / "file2.json").exists()

    def test_clear_views_directory_missing(self, tmp_path):
        """Should return empty list if views directory doesn't exist."""
        deleted = clear_views_directory(str(tmp_path), dry_run=False)
        assert deleted == []

    def test_clear_views_directory_expands_tilde(self):
        """Should expand ~ in vault path."""
        with patch("pathlib.Path.expanduser") as mock_expand:
            mock_expand.return_value = Path("/home/user/vault")
            with patch("pathlib.Path.exists", return_value=False):
                clear_views_directory("~/vault", dry_run=False)
            mock_expand.assert_called()


# =============================================================================
# Processor Tests: get_vault_statistics
# =============================================================================


class TestGetVaultStatistics:
    """Tests for get_vault_statistics processor function."""

    def test_get_vault_statistics(self, tmp_path):
        """Should count files in each category subdirectory."""
        # Setup vault structure
        views_dir = tmp_path / "views"
        views_dir.mkdir()

        # Create category directories with files
        (views_dir / "clients").mkdir()
        (views_dir / "clients" / "client1.json").write_text("{}")
        (views_dir / "clients" / "client2.json").write_text("{}")

        (views_dir / "sessions").mkdir()
        (views_dir / "sessions" / "session1.json").write_text("{}")

        (views_dir / "transcripts").mkdir()
        # Empty - should be 0

        # Execute
        stats = get_vault_statistics(str(tmp_path))

        assert stats["clients"] == 2
        assert stats["sessions"] == 1
        assert stats["transcripts"] == 0
        assert stats["notes"] == 0
        assert stats["summaries"] == 0
        assert stats["reports"] == 0

    def test_get_vault_statistics_missing_views(self, tmp_path):
        """Should return zeros if views directory doesn't exist."""
        stats = get_vault_statistics(str(tmp_path))

        assert all(v == 0 for v in stats.values())

    def test_get_vault_statistics_ignores_subdirs(self, tmp_path):
        """Should only count files, not subdirectories."""
        views_dir = tmp_path / "views"
        (views_dir / "clients").mkdir(parents=True)
        (views_dir / "clients" / "file.json").write_text("{}")
        (views_dir / "clients" / "subdir").mkdir()  # Should not be counted

        stats = get_vault_statistics(str(tmp_path))

        assert stats["clients"] == 1  # Only the file, not the subdir


# =============================================================================
# Verb -> job_id Mapping Tests (CRITICAL)
# =============================================================================


class TestVerbJobIdMapping:
    """Tests ensuring each CLI verb calls the correct lorchestra job_id.

    These tests are CRITICAL for ensuring the mapping between CLI commands
    and lorchestra jobs is correct.
    """

    @pytest.fixture
    def mock_run_lorchestra(self):
        """Mock run_lorchestra to capture the job_id."""
        with patch("life_jobs.pipeline.run_lorchestra") as mock:
            mock.return_value = {
                "job_id": "mocked",
                "success": True,
                "exit_code": 0,
                "duration_ms": 100,
                "stdout": "",
                "stderr": "",
                "error_message": None,
            }
            yield mock

    def test_ingest_verb_calls_correct_job_id(self, mock_run_lorchestra):
        """life pipeline ingest -> pipeline.ingest"""
        result = runner.invoke(app, ["pipeline", "ingest"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        assert call_kwargs["job_id"] == "pipeline.ingest"

    def test_canonize_verb_calls_correct_job_id(self, mock_run_lorchestra):
        """life pipeline canonize -> pipeline.canonize"""
        result = runner.invoke(app, ["pipeline", "canonize"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        assert call_kwargs["job_id"] == "pipeline.canonize"

    def test_formation_verb_calls_correct_job_id(self, mock_run_lorchestra):
        """life pipeline formation -> pipeline.formation"""
        result = runner.invoke(app, ["pipeline", "formation"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        assert call_kwargs["job_id"] == "pipeline.formation"

    def test_project_verb_calls_correct_job_id(self, mock_run_lorchestra):
        """life pipeline project -> pipeline.project"""
        result = runner.invoke(app, ["pipeline", "project"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        assert call_kwargs["job_id"] == "pipeline.project"

    def test_views_verb_calls_correct_job_id(self, mock_run_lorchestra):
        """life pipeline views -> pipeline.views"""
        result = runner.invoke(app, ["pipeline", "views"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        assert call_kwargs["job_id"] == "pipeline.views"

    def test_run_all_verb_calls_correct_job_id(self, mock_run_lorchestra):
        """life pipeline run-all -> pipeline.daily_all (DIVERGENT NAMING)"""
        result = runner.invoke(app, ["pipeline", "run-all"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        # NOTE: run-all maps to pipeline.daily_all, not pipeline.run_all
        assert call_kwargs["job_id"] == "pipeline.daily_all"


# =============================================================================
# Integration Tests
# =============================================================================


class TestPipelineIntegration:
    """Integration tests for pipeline commands."""

    @pytest.fixture
    def mock_run_lorchestra(self):
        """Mock run_lorchestra for integration tests."""
        with patch("life_jobs.pipeline.run_lorchestra") as mock:
            mock.return_value = {
                "job_id": "pipeline.project",
                "success": True,
                "exit_code": 0,
                "duration_ms": 5000,
                "stdout": "Projection complete",
                "stderr": "",
                "error_message": None,
            }
            yield mock

    def test_project_full_refresh(self, tmp_path, mock_run_lorchestra):
        """--full-refresh should clear views before running."""
        # Setup vault with views
        views_dir = tmp_path / "views"
        views_dir.mkdir()
        (views_dir / "old_file.json").write_text("{}")

        # Mock config to use tmp_path as vault
        with patch("life.commands.pipeline._get_vault_path", return_value=tmp_path):
            result = runner.invoke(app, ["pipeline", "project", "--full-refresh"])

        # File should be deleted
        assert not (views_dir / "old_file.json").exists()
        assert "Cleared 1 items" in result.output

    def test_project_shows_statistics(self, tmp_path, mock_run_lorchestra):
        """project command should display vault statistics after completion."""
        # Setup vault with views
        views_dir = tmp_path / "views"
        (views_dir / "clients").mkdir(parents=True)
        (views_dir / "clients" / "c1.json").write_text("{}")
        (views_dir / "clients" / "c2.json").write_text("{}")
        (views_dir / "sessions").mkdir()
        (views_dir / "sessions" / "s1.json").write_text("{}")

        with patch("life.commands.pipeline._get_vault_path", return_value=tmp_path):
            result = runner.invoke(app, ["pipeline", "project"])

        # Should show statistics
        assert "Vault Statistics" in result.output
        assert "clients: 2" in result.output
        assert "sessions: 1" in result.output

    def test_dry_run_propagates_to_lorchestra(self, mock_run_lorchestra):
        """--dry-run flag should be passed through to lorchestra."""
        result = runner.invoke(app, ["--dry-run", "pipeline", "ingest"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        # Job runner passes strings, processor converts to bool
        assert call_kwargs["dry_run"] == "true"

    def test_verbose_propagates_to_lorchestra(self, mock_run_lorchestra):
        """--verbose flag should be passed through to lorchestra."""
        result = runner.invoke(app, ["--verbose", "pipeline", "ingest"])

        mock_run_lorchestra.assert_called_once()
        call_kwargs = mock_run_lorchestra.call_args.kwargs
        # Job runner passes strings, processor converts to bool
        assert call_kwargs["verbose"] == "true"

    def test_failed_job_returns_nonzero_exit(self):
        """Failed lorchestra job should result in non-zero exit code."""
        with patch("life_jobs.pipeline.run_lorchestra") as mock:
            mock.return_value = {
                "job_id": "pipeline.ingest",
                "success": False,
                "exit_code": 1,
                "duration_ms": 100,
                "stdout": "",
                "stderr": "Error occurred",
                "error_message": "lorchestra exited with code 1",
            }
            result = runner.invoke(app, ["pipeline", "ingest"])

        assert result.exit_code == 1
        assert "failed" in result.output
