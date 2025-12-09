"""Legacy shell command execution (transitional only).

WARNING: This module exists only for migration from subprocess-based workflows.
New jobs should use Python functions instead of shell commands.

Implementation rules enforced here (Rule 9):
- Minimal and ugly on purpose
- No helpers or abstractions
- Discourage new shell-based jobs
- Keep it uncomfortable

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


def run(
    command: str,
    variables: Optional[Dict[str, str]] = None,
    timeout: int = 300,
    check: bool = True,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a shell command (transitional - prefer Python functions).

    Args:
        command: Shell command to execute
        variables: Variables to substitute in command (e.g., {input} -> value)
        timeout: Command timeout in seconds (default: 300)
        check: Raise exception on non-zero exit code (default: True)
        cwd: Working directory for command

    Returns:
        Dict with returncode, stdout, stderr
    """
    # Substitute variables
    if variables:
        for key, value in variables.items():
            command = command.replace(f"{{{key}}}", str(Path(value).expanduser()))

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
        cwd=Path(cwd).expanduser() if cwd else None,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
