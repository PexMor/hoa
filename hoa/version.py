"""
Version information for HOA.
"""
import subprocess
from datetime import UTC, datetime
from pathlib import Path

__version__ = "1.0.0"

def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

def get_git_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

def get_build_date() -> str:
    """Get build date (current date for development)."""
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

def get_version_info() -> dict:
    """Get complete version information."""
    return {
        "version": __version__,
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
        "build_date": get_build_date(),
    }

