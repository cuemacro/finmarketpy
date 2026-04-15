"""Security configuration validation tests.

This test suite validates that security tooling is properly configured.
It does NOT duplicate security checks performed by pre-commit hooks (Bandit, Ruff).

The actual security scanning is handled by:
- Bandit (pre-commit hook): Detects shell=True, eval/exec, hardcoded secrets, etc.
- Ruff S-rules (pre-commit hook): Additional security linting

These tests only verify that:
1. Security tools are properly configured
2. Security exceptions are documented
3. Custom security patterns not covered by standard tools
"""

import pathlib
import re


class TestFileOperations:
    """Validate secure file handling practices."""

    def test_no_world_writable_file_creation(self) -> None:
        """Verify that no code creates world-writable files (777 permissions).

        World-writable files are a security risk as any user can modify them.
        This test only checks production code, not test files.

        Note: This check is NOT covered by Bandit, hence included here.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent.parent
        violations = []
        # Look for chmod calls with overly permissive modes (world-writable: 0o77x)
        # We're specifically looking for 0o777, 0o776, 0o775, etc. (world-writable)
        chmod_pattern = re.compile(r"\.chmod\s*\(\s*0o77[0-9]")

        for py_file in repo_root.rglob("*.py"):
            # Skip test files and virtual environment
            if ".venv" not in str(py_file) and "test" not in str(py_file).lower():
                content = py_file.read_text()
                if chmod_pattern.search(content):
                    violations.append(str(py_file))

        assert not violations, (
            f"Found world-writable file permissions (0o77x) in production code:\n"
            f"{', '.join(violations)}\n"
            f"Avoid using 0o77x permissions; use 0o755 or more restrictive"
        )


class TestSecurityConfiguration:
    """Validate security-related configuration."""

    def test_ruff_security_checks_enabled(self) -> None:
        """Verify that Ruff's security checks (S) are enabled.

        This ensures the project has Ruff security rules configured.
        The actual security scanning happens in pre-commit hooks.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent.parent
        ruff_config = repo_root / "ruff.toml"

        assert ruff_config.exists(), "ruff.toml not found"

        content = ruff_config.read_text()
        # Check that "S" is in either select or extend-select
        assert '"S"' in content or "'S'" in content, "Ruff security checks (S) should be enabled in ruff.toml"

    def test_bandit_configured_in_precommit(self) -> None:
        """Verify that Bandit is configured in pre-commit hooks.

        This ensures Bandit security scanning is part of the development workflow.
        The actual security scanning happens in pre-commit hooks.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent.parent
        precommit_config = repo_root / ".pre-commit-config.yaml"

        assert precommit_config.exists(), ".pre-commit-config.yaml not found"

        content = precommit_config.read_text()
        assert "bandit" in content.lower(), "Bandit should be configured in pre-commit hooks"

    def test_security_policy_exists(self) -> None:
        """Verify that a SECURITY.md file exists at the repository root.

        GitHub displays a security policy link when SECURITY.md is present in
        the root, .github/, or docs/ directory. Root-level placement ensures
        maximum visibility in the GitHub UI.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent.parent
        root_security = repo_root / "SECURITY.md"

        assert root_security.exists(), (
            "No SECURITY.md found. Create SECURITY.md in the repository root "
            "to publish a responsible disclosure policy."
        )

    def test_secret_scanning_config_exists(self) -> None:
        """Verify that a secret scanning configuration file exists.

        The .github/secret_scanning.yml file configures GitHub secret scanning
        for the repository. Secret scanning must also be enabled in repository
        Settings > Security > Code security and analysis.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent.parent
        secret_scanning_config = repo_root / ".github" / "secret_scanning.yml"

        assert secret_scanning_config.exists(), (
            ".github/secret_scanning.yml not found. "
            "Create this file to configure GitHub secret scanning. "
            "Remember to also enable secret scanning in repository settings."
        )

    def test_dependabot_configured(self) -> None:
        """Verify that Dependabot is configured for dependency updates.

        The .github/dependabot.yml file configures Dependabot version and
        security updates. Dependabot security updates must also be enabled in
        repository Settings > Security > Code security and analysis.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent.parent
        dependabot_config = repo_root / ".github" / "dependabot.yml"

        assert dependabot_config.exists(), (
            ".github/dependabot.yml not found. Create this file to configure Dependabot version and security updates."
        )

        content = dependabot_config.read_text()
        assert "package-ecosystem" in content, (
            ".github/dependabot.yml should define at least one package-ecosystem entry"
        )

    def test_test_security_exceptions_documented(self) -> None:
        """Verify that security exceptions in test code are documented.

        Test files should have docstrings or comments explaining why security
        exceptions (like S101, S603, S607) are safe in the test context.

        This is a custom requirement for this project to ensure security
        exceptions are justified and understood.
        """
        repo_root = pathlib.Path(__file__).parent.parent.parent.parent
        conftest_files = list(repo_root.rglob("conftest.py"))

        # For each conftest, verify it has security documentation
        for conftest in conftest_files:
            if ".venv" in str(conftest):
                continue

            content = conftest.read_text()
            # Check for security-related comments or docstrings
            has_security_docs = (
                "S101" in content or "S603" in content or "S607" in content or "security" in content.lower()
            )

            assert has_security_docs, f"{conftest} should document security exceptions (S101/S603/S607)"
