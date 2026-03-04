# Release Guide

This guide covers the release process for Rhiza-based projects.

## 🚀 The Release Process

The release process can be done in two separate steps (**Bump** then **Release**), or in a single step using **Publish**.

### Option A: One-Step Publish (Recommended)

Bump the version and release in a single flow:

```bash
make publish
```

This combines the bump and release steps below into one interactive command.

### Option B: Two-Step Process

#### 1. Bump Version

First, update the version in `pyproject.toml`:

```bash
make bump
```

This command will interactively guide you through:
1. Selecting a bump type (patch, minor, major) or entering a specific version
2. Warning you if you're not on the default branch
3. Showing the current and new version
4. Prompting whether to commit the changes
5. Prompting whether to push the changes

The script ensures safety by:
- Checking for uncommitted changes before bumping
- Validating that the tag doesn't already exist
- Verifying the version format

#### 2. Release

Once the version is bumped and committed, run the release command:

```bash
make release
```

This command will interactively guide you through:
1. Checking if your branch is up-to-date with the remote
2. If your local branch is ahead, showing the unpushed commits and prompting you to push them
3. Creating a git tag (e.g., `v1.2.4`)
4. Pushing the tag to the remote, which triggers the GitHub Actions release workflow

The script provides safety checks by:
- Warning if you're not on the default branch
- Verifying no uncommitted changes exist
- Checking if the tag already exists locally or on remote
- Showing the number of commits since the last tag

### Checking Release Status

After releasing, you can check the status of the release workflow and the latest release:

```bash
make release-status
```

This will display:
- The last 5 release workflow runs with their status and conclusion
- The latest GitHub release details (tag, author, published time, status, URL)

> **Note:** `release-status` is currently supported for GitHub repositories only. GitLab support is planned for a future release.

## What Happens After Release

The release workflow (`.github/workflows/rhiza_release.yml`) triggers on the tag push and:

1. **Validates** - Checks the tag format and ensures no duplicate releases
2. **Builds** - Builds the Python package (if `pyproject.toml` exists)
3. **Drafts** - Creates a draft GitHub release with artifacts
4. **PyPI** - Publishes to PyPI (if not marked private)
5. **Devcontainer** - Publishes devcontainer image (if `PUBLISH_DEVCONTAINER=true`)
6. **Finalizes** - Publishes the GitHub release with links to PyPI and container images

## Configuration Options

### PyPI Publishing

- Automatic if package is registered as a Trusted Publisher
- Use `PYPI_REPOSITORY_URL` and `PYPI_TOKEN` for custom feeds
- Mark as private with `Private :: Do Not Upload` in `pyproject.toml`

### Devcontainer Publishing

- Set repository variable `PUBLISH_DEVCONTAINER=true` to enable
- Override registry with `DEVCONTAINER_REGISTRY` variable (defaults to ghcr.io)
- Requires `.devcontainer/devcontainer.json` to exist
- Image published as `{registry}/{owner}/{repository}/devcontainer:vX.Y.Z`
