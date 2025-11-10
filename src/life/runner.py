"""
Command runner for Life-CLI.

Executes shell commands with variable substitution and error handling.

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional


class CommandRunner:
    """Executes shell commands with variable substitution."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """
        Initialize command runner.

        Args:
            dry_run: If True, only show what would be executed
            verbose: Enable verbose logging
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def substitute_variables(self, command: str, variables: Dict[str, str]) -> str:
        """
        Substitute variables in command string.

        Supports escaping with double braces: {{text}} becomes {text}

        Args:
            command: Command template with {variable} placeholders
            variables: Dict of variable name -> value

        Returns:
            Command with variables substituted

        Example:
            >>> substitute_variables("echo {name}", {"name": "Alice"})
            'echo Alice'
            >>> substitute_variables("echo {{literal}}", {})
            'echo {literal}'
        """
        import re

        # First, temporarily replace escaped braces {{...}} with a placeholder
        escape_open = "\x00ESCAPED_OPEN\x00"
        escape_close = "\x00ESCAPED_CLOSE\x00"
        result = command.replace("{{", escape_open).replace("}}", escape_close)

        # Substitute variables
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
                self.logger.debug(f"Substituted {{{key}}} -> {value}")

        # Check for unsubstituted variables (but ignore our placeholders)
        remaining = re.findall(r'\{(\w+)\}', result)
        if remaining:
            self.logger.warning(f"Unsubstituted variables: {remaining}")

        # Restore escaped braces
        result = result.replace(escape_open, "{").replace(escape_close, "}")

        return result

    def run(
        self,
        command: str,
        variables: Optional[Dict[str, str]] = None,
        shell: bool = True,
        check: bool = True,
    ) -> Optional[subprocess.CompletedProcess]:
        """
        Execute a shell command with variable substitution.

        Args:
            command: Command to execute (may contain {variable} placeholders)
            variables: Dict of variables to substitute
            shell: Run command in shell (default True for multi-line commands)
            check: Raise exception on non-zero exit code

        Returns:
            CompletedProcess if executed, None if dry_run

        Raises:
            subprocess.CalledProcessError: If command fails and check=True
        """
        if variables is None:
            variables = {}

        # Substitute variables
        final_command = self.substitute_variables(command, variables)

        # Dry run mode
        if self.dry_run:
            self.logger.info("[DRY RUN] Would execute:")
            self.logger.info(f"  {final_command}")
            return None

        # Execute command
        if len(final_command) > 100:
            log_msg = f"Executing: {final_command[:100]}..."
        else:
            log_msg = f"Executing: {final_command}"
        self.logger.info(log_msg)

        try:
            result = subprocess.run(
                final_command,
                shell=shell,
                check=check,
                capture_output=True,
                text=True,
            )

            if self.verbose and result.stdout:
                self.logger.debug(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                self.logger.warning(f"STDERR:\n{result.stderr}")

            return result

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with exit code {e.returncode}")
            if e.stdout:
                self.logger.error(f"STDOUT:\n{e.stdout}")
            if e.stderr:
                self.logger.error(f"STDERR:\n{e.stderr}")
            raise

    def run_multiple(
        self,
        commands: list[str],
        variables: Optional[Dict[str, str]] = None,
    ) -> list[Optional[subprocess.CompletedProcess]]:
        """
        Execute multiple commands in sequence.

        Args:
            commands: List of commands to execute
            variables: Dict of variables to substitute in all commands

        Returns:
            List of CompletedProcess results (or None for dry_run)

        Raises:
            subprocess.CalledProcessError: If any command fails
        """
        results = []
        for i, command in enumerate(commands, 1):
            self.logger.info(f"Command {i}/{len(commands)}")
            result = self.run(command, variables)
            results.append(result)

        return results


def expand_path(path: str) -> Path:
    """
    Expand user home directory and environment variables in path.

    Args:
        path: Path string potentially containing ~ or $VAR

    Returns:
        Expanded Path object

    Example:
        >>> expand_path("~/data/file.json")
        Path("/home/user/data/file.json")
    """
    return Path(path).expanduser().resolve()
