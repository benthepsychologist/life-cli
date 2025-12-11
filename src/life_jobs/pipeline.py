"""Pipeline operations via lorchestra subprocess.

Implementation rules enforced here (Rule 8):
- Never print
- Never read global config or environment (except Path.expanduser)
- Always return simple dicts
- Side effects: file IO, lorchestra subprocess calls only

Transport: lorchestra CLI via subprocess
Auth: None (lorchestra handles its own auth)

Copyright 2025 Ben Mensi
Licensed under the Apache License, Version 2.0
"""

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

# I/O declaration for static analysis and auditing
__io__ = {
    "reads": ["filesystem.vault"],
    "writes": ["filesystem.vault"],
    "external": ["lorchestra.subprocess"],
}


def _to_bool(value) -> bool:
    """Convert value to boolean, handling string 'true'/'false' from job runner."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)


def run_lorchestra(
    job_id: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Execute a lorchestra composite job.

    External: lorchestra.subprocess

    Args:
        job_id: Lorchestra job ID (e.g., "pipeline.ingest")
        dry_run: If True, passes --dry-run to lorchestra (accepts string "true"/"false")
        verbose: If True, streams output in real-time (accepts string "true"/"false")

    Returns:
        {job_id, success, exit_code, duration_ms, stdout, stderr, error_message}
    """
    # Convert string values from job runner to booleans
    dry_run = _to_bool(dry_run)
    verbose = _to_bool(verbose)

    # Check if lorchestra is available
    if shutil.which("lorchestra") is None:
        return {
            "job_id": job_id,
            "success": False,
            "exit_code": -1,
            "duration_ms": 0,
            "stdout": "",
            "stderr": "",
            "error_message": "lorchestra is not installed or not in PATH",
        }

    # Build command
    cmd = ["lorchestra", "run", job_id]
    if dry_run:
        cmd.append("--dry-run")

    start_time = time.time()

    try:
        if verbose:
            # Stream output in real-time, don't capture
            result = subprocess.run(cmd, check=False)
            stdout = ""
            stderr = ""
        else:
            # Capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""

        duration_ms = int((time.time() - start_time) * 1000)
        exit_code = result.returncode
        success = exit_code == 0

        error_message = None
        if not success:
            error_message = f"lorchestra exited with code {exit_code}"
            if stderr:
                # Include first line of stderr in error message
                first_line = stderr.strip().split("\n")[0]
                error_message = f"{error_message}: {first_line}"

        return {
            "job_id": job_id,
            "success": success,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "stdout": stdout,
            "stderr": stderr,
            "error_message": error_message,
        }

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "job_id": job_id,
            "success": False,
            "exit_code": -1,
            "duration_ms": duration_ms,
            "stdout": "",
            "stderr": "",
            "error_message": f"Failed to execute lorchestra: {e}",
        }


def clear_views_directory(
    vault_path: str,
    dry_run: bool = False,
) -> List[str]:
    """Delete all files in {vault_path}/views/ only.

    Writes: filesystem.vault (deletes files)

    Args:
        vault_path: Path to the vault directory (~ will be expanded)
        dry_run: If True, logs what would be deleted without deleting

    Returns:
        List of deleted (or would-be-deleted) file paths
    """
    vault = Path(vault_path).expanduser()
    views_dir = vault / "views"

    if not views_dir.exists():
        return []

    deleted: List[str] = []

    # Delete all files and subdirectories in views/
    for item in views_dir.iterdir():
        item_path = str(item)
        deleted.append(item_path)

        if not dry_run:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    return deleted


def get_vault_statistics(vault_path: str) -> Dict[str, int]:
    """Count files in vault views directory by type.

    Reads: filesystem.vault

    Counts are based on files under {vault_path}/views/, not the entire vault.
    File types are determined by directory name (e.g., views/clients/, views/sessions/).

    Args:
        vault_path: Path to the vault directory (~ will be expanded)

    Returns:
        {clients, sessions, transcripts, notes, summaries, reports}
    """
    vault = Path(vault_path).expanduser()
    views_dir = vault / "views"

    stats = {
        "clients": 0,
        "sessions": 0,
        "transcripts": 0,
        "notes": 0,
        "summaries": 0,
        "reports": 0,
    }

    if not views_dir.exists():
        return stats

    # Count files in each known subdirectory
    for category in stats.keys():
        category_dir = views_dir / category
        if category_dir.exists() and category_dir.is_dir():
            # Count only files, not subdirectories
            stats[category] = sum(1 for f in category_dir.iterdir() if f.is_file())

    return stats
