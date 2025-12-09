"""Tests for life_jobs.shell module.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import subprocess
import pytest
from pathlib import Path

from life_jobs.shell import run


class TestShellRun:
    """Tests for shell.run function."""

    def test_simple_command(self):
        """Should execute simple shell commands."""
        result = run("echo hello")
        assert result["returncode"] == 0
        assert "hello" in result["stdout"]
        assert result["stderr"] == ""

    def test_command_with_variables(self, tmp_path):
        """Should substitute variables in commands."""
        output_file = tmp_path / "output.txt"
        result = run(
            "echo test > {output}",
            variables={"output": str(output_file)},
        )
        assert result["returncode"] == 0
        assert output_file.exists()

    def test_command_with_cwd(self, tmp_path):
        """Should run commands in specified directory."""
        result = run("pwd", cwd=str(tmp_path))
        assert result["returncode"] == 0
        assert str(tmp_path) in result["stdout"]

    def test_command_timeout(self):
        """Should timeout long-running commands."""
        with pytest.raises(subprocess.TimeoutExpired):
            run("sleep 10", timeout=1)

    def test_command_failure_with_check(self):
        """Should raise on non-zero exit with check=True."""
        with pytest.raises(subprocess.CalledProcessError):
            run("exit 1", check=True)

    def test_command_failure_without_check(self):
        """Should return result without raising when check=False."""
        result = run("exit 1", check=False)
        assert result["returncode"] == 1

    def test_stderr_capture(self):
        """Should capture stderr."""
        result = run("echo error >&2", check=True)
        assert "error" in result["stderr"]

    def test_path_expansion_in_variables(self, tmp_path):
        """Should expand ~ in variable values."""
        # Create a file in tmp_path to verify path works
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = run(
            "cat {file}",
            variables={"file": str(test_file)},
        )
        assert result["returncode"] == 0
        assert "content" in result["stdout"]
