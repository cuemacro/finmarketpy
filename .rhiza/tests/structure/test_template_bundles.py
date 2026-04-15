"""Tests to validate that all files/folders referenced in template-bundles.yml exist.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

This module ensures that template bundle definitions in .rhiza/template-bundles.yml
reference only files and folders that actually exist in the repository.
"""

import pytest
import yaml


class TestTemplateBundles:
    """Tests for template-bundles.yml validation."""

    @pytest.fixture
    def bundles_file(self, root):
        """Return the path to template-bundles.yml."""
        return root / ".rhiza" / "template-bundles.yml"

    @pytest.fixture
    def bundles_data(self, bundles_file):
        """Load and parse the template-bundles.yml file."""
        if not bundles_file.exists():
            pytest.skip("template-bundles.yml does not exist in this project")

        with open(bundles_file) as f:
            data = yaml.safe_load(f)

        if not data or "bundles" not in data:
            pytest.fail("Invalid template-bundles.yml format - missing 'bundles' key")

        return data

    def test_bundles_file_exists_or_skip(self, bundles_file):
        """Test that template-bundles.yml exists, or skip if not present."""
        if not bundles_file.exists():
            pytest.skip("template-bundles.yml does not exist in this project")

    def test_all_bundle_files_exist(self, root, bundles_data):
        """Test that all files referenced in template-bundles.yml exist."""
        bundles = bundles_data["bundles"]
        all_missing = []
        total_files = 0

        # Check each bundle
        for bundle_name, bundle_config in bundles.items():
            if "files" not in bundle_config:
                continue

            files = bundle_config["files"]

            for file_path in files:
                total_files += 1
                path = root / file_path

                if not path.exists():
                    all_missing.append((bundle_name, file_path))

        # Report results
        if all_missing:
            error_msg = f"\nValidation failed: {len(all_missing)} of {total_files} files/folders are missing:\n\n"
            for bundle_name, file_path in all_missing:
                error_msg += f"  [{bundle_name}] {file_path}\n"
            pytest.fail(error_msg)

    def test_each_bundle_files_exist(self, root, bundles_data):
        """Test that files exist for each individual bundle."""
        bundles = bundles_data["bundles"]

        for bundle_name, bundle_config in bundles.items():
            if "files" not in bundle_config:
                continue

            files = bundle_config["files"]
            missing_in_bundle = []

            for file_path in files:
                path = root / file_path

                if not path.exists():
                    missing_in_bundle.append(file_path)

            if missing_in_bundle:
                error_msg = f"\nBundle '{bundle_name}' has {len(missing_in_bundle)} missing path(s):\n"
                for missing in missing_in_bundle:
                    error_msg += f"   - {missing}\n"
                pytest.fail(error_msg)
