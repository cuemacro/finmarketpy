# Git LFS (Large File Storage) Configuration

This document describes the Git LFS integration in the Rhiza framework.

## Overview

Git LFS (Large File Storage) is an extension to Git that allows you to version large files efficiently. Instead of storing large binary files directly in the Git repository, LFS stores them on a remote server and keeps only small pointer files in the repository.

## Available Make Targets

### `make lfs-install`

Installs Git LFS and configures it for the current repository.

**Features:**
- **Cross-platform support**: Works on macOS (both Intel and ARM) and Linux
- **macOS**: Downloads and installs the latest git-lfs binary to `.local/bin/`
- **Linux**: Installs git-lfs via apt-get package manager
- **Automatic configuration**: Runs `git lfs install` to set up LFS hooks

**Usage:**
```bash
make lfs-install
```

**Note for macOS users:** The git-lfs binary is installed locally in `.local/bin/` and added to PATH for the installation. This approach avoids requiring system-level package managers like Homebrew.

### `make lfs-pull`

Downloads all Git LFS files for the current branch.

**Usage:**
```bash
make lfs-pull
```

This is useful after cloning a repository or checking out a branch that contains LFS-tracked files.

### `make lfs-track`

Lists all file patterns currently tracked by Git LFS.

**Usage:**
```bash
make lfs-track
```

### `make lfs-status`

Shows the status of Git LFS files in the repository.

**Usage:**
```bash
make lfs-status
```

## Typical Workflow

1. **Initial setup** (first time only):
   ```bash
   make lfs-install
   ```

2. **Track large files** (configure which files to store in LFS):
   ```bash
   git lfs track "*.psd"
   git lfs track "*.zip"
   git lfs track "data/*.csv"
   ```

3. **Check tracking status**:
   ```bash
   make lfs-track
   ```

4. **Pull LFS files** (after cloning or checking out):
   ```bash
   make lfs-pull
   ```

5. **Check LFS status**:
   ```bash
   make lfs-status
   ```

## CI/CD Integration

### GitHub Actions

When using Git LFS with GitHub Actions, add the `lfs: true` option to your checkout step:

```yaml
- uses: actions/checkout@v4
  with:
    lfs: true
```

### GitLab CI

For GitLab CI, install and pull LFS files in your before_script:

```yaml
before_script:
  - apt-get update && apt-get install -y git-lfs || exit 1
  - git lfs pull
```

## Configuration Files

Git LFS uses `.gitattributes` to track which files should be managed by LFS. Example:

```
# .gitattributes
*.psd filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
data/*.csv filter=lfs diff=lfs merge=lfs -text
```

## Resources

- [Git LFS Official Documentation](https://git-lfs.github.com/)
- [Git LFS Tutorial](https://github.com/git-lfs/git-lfs/wiki/Tutorial)
- [Git LFS GitHub Repository](https://github.com/git-lfs/git-lfs)

## Troubleshooting

### Permission denied during installation (Linux)

If you encounter permission errors on Linux during `make lfs-install`, the installation requires elevated privileges. The command will prompt for sudo access automatically. If it fails, you can run:

```bash
sudo apt-get update && sudo apt-get install -y git-lfs
git lfs install
```

Alternatively, if you don't have sudo access, git-lfs can be installed manually by downloading the binary from the [releases page](https://github.com/git-lfs/git-lfs/releases).

### Failed to detect git-lfs version (macOS)

If the installation fails with "Failed to detect git-lfs version", ensure you have internet connectivity and can access the GitHub API:

```bash
curl -s https://api.github.com/repos/git-lfs/git-lfs/releases/latest
```

If the GitHub API is blocked, you can manually download and install git-lfs from [git-lfs.github.com](https://git-lfs.github.com/).

### LFS files not downloading

If LFS files are not downloading, ensure:
1. Git LFS is installed: `git lfs version`
2. LFS is initialized: `git lfs install`
3. Pull LFS files explicitly: `make lfs-pull`

### Checking LFS storage usage

To see how much storage your LFS files are using:

```bash
git lfs ls-files --size
```
