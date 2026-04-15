"""Integration test for SBOM generation using cyclonedx-bom.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Tests the SBOM (Software Bill of Materials) generation workflow to ensure
the cyclonedx-bom tool works correctly with uvx.
"""

import subprocess  # nosec B404


def test_sbom_generation_json(git_repo, logger):
    """Test that SBOM generation works in JSON format."""
    # Run the SBOM generation command for JSON
    result = subprocess.run(  # nosec B603
        [
            "uvx",
            "--from",
            "cyclonedx-bom>=7.0.0",
            "cyclonedx-py",
            "environment",
            "--pyproject",
            "pyproject.toml",
            "--of",
            "JSON",
            "-o",
            "sbom.cdx.json",
        ],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=False,
    )

    logger.info("SBOM JSON stdout: %s", result.stdout)
    logger.info("SBOM JSON stderr: %s", result.stderr)

    # Verify command succeeded
    assert result.returncode == 0, f"SBOM JSON generation failed: {result.stderr}"

    # Verify output file exists
    sbom_file = git_repo / "sbom.cdx.json"
    assert sbom_file.exists(), "SBOM JSON file was not created"
    assert sbom_file.stat().st_size > 0, "SBOM JSON file is empty"

    # Verify it's valid JSON
    import json

    with open(sbom_file) as f:
        sbom_data = json.load(f)

    # Basic CycloneDX structure validation
    assert "bomFormat" in sbom_data, "SBOM missing bomFormat field"
    assert sbom_data["bomFormat"] == "CycloneDX", "SBOM has incorrect bomFormat"
    assert "components" in sbom_data, "SBOM missing components field"

    # Verify primary component (metadata.component) is present for NTIA compliance
    assert "metadata" in sbom_data, "SBOM missing metadata field"
    assert "component" in sbom_data["metadata"], "SBOM missing primary component (metadata.component)"
    primary = sbom_data["metadata"]["component"]
    assert primary.get("name"), "Primary component missing name"
    assert primary.get("version"), "Primary component missing version"


def test_sbom_generation_xml(git_repo, logger):
    """Test that SBOM generation works in XML format."""
    # Run the SBOM generation command for XML
    result = subprocess.run(  # nosec B603
        [
            "uvx",
            "--from",
            "cyclonedx-bom>=7.0.0",
            "cyclonedx-py",
            "environment",
            "--pyproject",
            "pyproject.toml",
            "--of",
            "XML",
            "-o",
            "sbom.cdx.xml",
        ],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=False,
    )

    logger.info("SBOM XML stdout: %s", result.stdout)
    logger.info("SBOM XML stderr: %s", result.stderr)

    # Verify command succeeded
    assert result.returncode == 0, f"SBOM XML generation failed: {result.stderr}"

    # Verify output file exists
    sbom_file = git_repo / "sbom.cdx.xml"
    assert sbom_file.exists(), "SBOM XML file was not created"
    assert sbom_file.stat().st_size > 0, "SBOM XML file is empty"

    # Verify it's valid XML with CycloneDX structure
    import defusedxml.ElementTree

    tree = defusedxml.ElementTree.parse(sbom_file)
    root = tree.getroot()

    # Check for CycloneDX namespace
    assert "cyclonedx" in root.tag.lower(), "SBOM XML root is not CycloneDX"
    # Check for components element
    components = root.find(".//{*}components")
    assert components is not None, "SBOM XML missing components element"


def test_sbom_command_syntax(git_repo, logger):
    """Test that the uvx command syntax is correct (no npm-style @^version)."""
    # This test verifies that we're using the correct syntax
    # Bad: uvx cyclonedx-bom@^7.0.0
    # Good: uvx --from 'cyclonedx-bom>=7.0.0' cyclonedx-py

    # Try the old (incorrect) syntax - should fail
    result_bad = subprocess.run(  # nosec B603
        [
            "uvx",
            "cyclonedx-bom@^7.0.0",
            "environment",
            "--of",
            "JSON",
            "-o",
            "sbom.test.json",
        ],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=False,
    )

    logger.info("Bad syntax stdout: %s", result_bad.stdout)
    logger.info("Bad syntax stderr: %s", result_bad.stderr)

    # Old syntax should fail
    assert result_bad.returncode != 0, "Old npm-style syntax should not work"

    # Try the new (correct) syntax - should succeed
    result_good = subprocess.run(  # nosec B603
        [
            "uvx",
            "--from",
            "cyclonedx-bom>=7.0.0",
            "cyclonedx-py",
            "environment",
            "--pyproject",
            "pyproject.toml",
            "--of",
            "JSON",
            "-o",
            "sbom.test.json",
        ],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=False,
    )

    logger.info("Good syntax stdout: %s", result_good.stdout)
    logger.info("Good syntax stderr: %s", result_good.stderr)

    # New syntax should succeed
    assert result_good.returncode == 0, f"Correct syntax failed: {result_good.stderr}"

    # Cleanup
    test_file = git_repo / "sbom.test.json"
    if test_file.exists():
        test_file.unlink()
