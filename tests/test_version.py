"""
Tests for version module.
"""

import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from hoa.version import (
    __version__,
    get_git_commit,
    get_git_branch,
    get_build_date,
    get_version_info,
)


class TestVersionConstant:
    """Tests for __version__ constant."""
    
    def test_version_constant_exists(self):
        """Test that __version__ constant exists."""
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    
    def test_version_format(self):
        """Test that version follows semver format."""
        # Should be like "1.0.0"
        parts = __version__.split(".")
        assert len(parts) >= 2  # At least major.minor
        assert all(part.isdigit() for part in parts if part.isdigit())  # Numeric parts


class TestGetGitCommit:
    """Tests for get_git_commit function."""
    
    def test_get_git_commit(self):
        """Test getting git commit hash."""
        commit = get_git_commit()
        
        # Should return a string (commit hash or "unknown")
        assert isinstance(commit, str)
        assert len(commit) > 0
        
        # If in a git repo, should be a short hash
        if commit != "unknown":
            assert len(commit) >= 7  # Short hash
            assert all(c in "0123456789abcdef" for c in commit)
    
    @patch("subprocess.run")
    def test_get_git_commit_not_a_repo(self, mock_run):
        """Test getting git commit when not in a git repo."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        commit = get_git_commit()
        
        assert commit == "unknown"
    
    @patch("subprocess.run")
    def test_get_git_commit_git_not_found(self, mock_run):
        """Test getting git commit when git is not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        commit = get_git_commit()
        
        assert commit == "unknown"


class TestGetGitBranch:
    """Tests for get_git_branch function."""
    
    def test_get_git_branch(self):
        """Test getting git branch name."""
        branch = get_git_branch()
        
        # Should return a string (branch name or "unknown")
        assert isinstance(branch, str)
        assert len(branch) > 0
        
        # Common branch names
        if branch != "unknown":
            # Branch name should be alphanumeric with possible - and _
            assert all(c.isalnum() or c in "-_/" for c in branch)
    
    @patch("subprocess.run")
    def test_get_git_branch_not_a_repo(self, mock_run):
        """Test getting git branch when not in a git repo."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        branch = get_git_branch()
        
        assert branch == "unknown"
    
    @patch("subprocess.run")
    def test_get_git_branch_git_not_found(self, mock_run):
        """Test getting git branch when git is not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        branch = get_git_branch()
        
        assert branch == "unknown"


class TestGetBuildDate:
    """Tests for get_build_date function."""
    
    def test_get_build_date(self):
        """Test getting build date."""
        build_date = get_build_date()
        
        # Should return a string in format "YYYY-MM-DD HH:MM:SS UTC"
        assert isinstance(build_date, str)
        assert "UTC" in build_date
        assert len(build_date) > 10
        
        # Should contain date parts
        parts = build_date.split()
        assert len(parts) == 3  # Date, Time, UTC
        
        # Date should be YYYY-MM-DD
        date_part = parts[0]
        assert len(date_part) == 10
        assert date_part.count("-") == 2
        
        # Time should be HH:MM:SS
        time_part = parts[1]
        assert len(time_part) == 8
        assert time_part.count(":") == 2


class TestGetVersionInfo:
    """Tests for get_version_info function."""
    
    def test_get_version_info_structure(self):
        """Test getting version info returns correct structure."""
        info = get_version_info()
        
        # Should return a dictionary
        assert isinstance(info, dict)
        
        # Should have all required keys
        assert "version" in info
        assert "git_commit" in info
        assert "git_branch" in info
        assert "build_date" in info
    
    def test_get_version_info_values(self):
        """Test getting version info returns valid values."""
        info = get_version_info()
        
        # All values should be strings
        assert isinstance(info["version"], str)
        assert isinstance(info["git_commit"], str)
        assert isinstance(info["git_branch"], str)
        assert isinstance(info["build_date"], str)
        
        # All values should be non-empty
        assert len(info["version"]) > 0
        assert len(info["git_commit"]) > 0
        assert len(info["git_branch"]) > 0
        assert len(info["build_date"]) > 0
    
    @patch("hoa.version.get_git_commit", return_value="abc123")
    @patch("hoa.version.get_git_branch", return_value="main")
    @patch("hoa.version.get_build_date", return_value="2025-10-23 19:00:00 UTC")
    def test_get_version_info_with_mocks(self, mock_date, mock_branch, mock_commit):
        """Test getting version info with mocked values."""
        info = get_version_info()
        
        assert info == {
            "version": "1.0.0",
            "git_commit": "abc123",
            "git_branch": "main",
            "build_date": "2025-10-23 19:00:00 UTC",
        }
    
    @patch("hoa.version.get_git_commit", return_value="unknown")
    @patch("hoa.version.get_git_branch", return_value="unknown")
    def test_get_version_info_all_unknown(self, mock_branch, mock_commit):
        """Test getting version info when git info is unknown."""
        info = get_version_info()
        
        # version should always be the constant
        assert info["version"] == "1.0.0"
        assert info["git_commit"] == "unknown"
        assert info["git_branch"] == "unknown"
        # build_date should still have a value
        assert info["build_date"] != "unknown"
        assert "UTC" in info["build_date"]

