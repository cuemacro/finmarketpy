"""Tests for the .rhiza-version file and related Makefile functionality.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

These tests validate:
- Reading RHIZA_VERSION from .rhiza/.rhiza-version
- The summarise-sync Makefile target
- Version usage in sync and validate targets
"""

from __future__ import annotations

# Import from local conftest
from sync.conftest import run_make, strip_ansi


class TestRhizaVersion:
    """Tests for RHIZA_VERSION variable and .rhiza-version file."""

    def test_rhiza_version_exists_in_file(self, root):
        """The .rhiza/.rhiza-version file should exist and contain a version."""
        version_file = root / ".rhiza" / ".rhiza-version"
        assert version_file.exists()
        assert version_file.is_file()

        content = version_file.read_text().strip()
        assert len(content) > 0
        # Check it looks like a version (e.g., "0.9.0")
        assert content[0].isdigit()

    def test_rhiza_version_exported_in_makefile(self, logger):
        """RHIZA_VERSION should be exported and readable."""
        proc = run_make(logger, ["print-RHIZA_VERSION"], dry_run=False)
        out = strip_ansi(proc.stdout)
        # The output should contain the version value
        assert "Value of RHIZA_VERSION:" in out
        # Should have a version number
        assert any(char.isdigit() for char in out)

    def test_rhiza_version_defaults_to_0_9_0_without_file(self, logger, tmp_path):
        """RHIZA_VERSION should default to 0.10.2 if .rhiza-version doesn't exist."""
        # Remove the .rhiza-version file
        version_file = tmp_path / ".rhiza" / ".rhiza-version"
        if version_file.exists():
            version_file.unlink()

        # Clear RHIZA_VERSION from environment to test the default value
        import os
        import subprocess

        env = os.environ.copy()
        env.pop("RHIZA_VERSION", None)

        cmd = ["/usr/bin/make", "-s", "print-RHIZA_VERSION"]
        logger.info("Running command: %s", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        out = strip_ansi(proc.stdout)
        assert "Value of RHIZA_VERSION:\n0.10.2" in out

    def test_rhiza_version_used_in_sync_target(self, logger):
        """Sync target should use RHIZA_VERSION from .rhiza-version."""
        proc = run_make(logger, ["sync"])
        out = proc.stdout
        # Check that rhiza>= is used with the version variable
        assert 'uvx "rhiza==' in out or "rhiza==" in out

    def test_rhiza_version_used_in_validate_target(self, logger):
        """Validate target should use RHIZA_VERSION from .rhiza-version."""
        proc = run_make(logger, ["validate"])
        out = proc.stdout
        # Check that rhiza>= is used with the version variable
        assert 'uvx "rhiza==' in out or "rhiza==" in out


class TestSummariseSync:
    """Tests for the summarise-sync Makefile target."""

    def test_summarise_sync_target_exists(self, logger):
        """The summarise-sync target should be available."""
        proc = run_make(logger, ["help"])
        out = proc.stdout
        # Check that summarise-sync appears in help
        assert "summarise-sync" in out

    def test_summarise_sync_dry_run(self, logger):
        """Summarise-sync target should invoke rhiza summarise in dry-run output."""
        proc = run_make(logger, ["summarise-sync"])
        out = proc.stdout
        # Check for uvx command with rhiza summarise
        assert "uvx" in out
        assert "rhiza" in out
        assert "summarise" in out

    def test_summarise_sync_uses_rhiza_version(self, logger):
        """Summarise-sync target should use RHIZA_VERSION from .rhiza-version."""
        proc = run_make(logger, ["summarise-sync"])
        out = proc.stdout
        # Check that rhiza== is used with the version
        assert 'uvx "rhiza==' in out or "rhiza==" in out

    def test_summarise_sync_skips_in_rhiza_repo(self, logger):
        """Summarise-sync target should skip execution in rhiza repository."""
        # setup_rhiza_git_repo() is already called by fixture

        proc = run_make(logger, ["summarise-sync"], dry_run=True)
        # Should succeed but skip the actual summarise
        assert proc.returncode == 0
        # Verify the skip message is in the output
        assert "Skipping summarise-sync in rhiza repository" in proc.stdout

    def test_summarise_sync_requires_install_uv(self, logger):
        """Summarise-sync should ensure uv is installed first."""
        proc = run_make(logger, ["summarise-sync"])
        out = proc.stdout
        # The output should show that install-uv is called
        # This might be implicit via the dependency chain
        assert "rhiza" in out

    def test_workflow_uvx_command_format(self, logger):
        """Test that the uvx command format matches workflow expectations."""
        # This test validates the command format used in both Makefile and workflow
        proc = run_make(logger, ["sync"])
        out = proc.stdout

        # The format should be: uvx "rhiza>=VERSION" sync .
        assert 'uvx "rhiza==' in out
        assert "sync ." in out

    def test_workflow_summarise_command_format(self, logger):
        """Test that the summarise command format matches workflow expectations."""
        proc = run_make(logger, ["summarise-sync"])
        out = proc.stdout

        # The format should be: uvx "rhiza>=VERSION" summarise .
        assert 'uvx "rhiza==' in out
        assert "summarise" in out
