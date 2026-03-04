# Using Private GitHub Packages

This document explains how to configure your project to use private GitHub packages from the same organization as dependencies.

## Quick Start

If you're using Rhiza's template workflows, git authentication for private packages is **already configured**! All Rhiza workflows automatically include the necessary git configuration to access private repositories in the same organization.

Simply add your private package to `pyproject.toml`:

```toml
[tool.uv.sources]
my-package = { git = "https://github.com/jebel-quant/my-package.git", rev = "v1.0.0" }
```

The workflows will handle authentication automatically using `GITHUB_TOKEN`.

## Detailed Guide

### Problem

When your project depends on private GitHub repositories, you need to authenticate to access them. SSH keys work locally but are complex to set up in CI/CD environments. HTTPS with tokens is simpler and more secure for automated workflows.

## Solution

Use HTTPS URLs with token authentication instead of SSH for git dependencies.

### 1. Configure Dependencies in pyproject.toml

Instead of using SSH URLs like `git@github.com:org/repo.git`, use HTTPS URLs:

```toml
[tool.uv.sources]
my-package = { git = "https://github.com/jebel-quant/my-package.git", rev = "v1.0.0" }
another-package = { git = "https://github.com/jebel-quant/another-package.git", tag = "v2.0.0" }
```

**Key points:**
- Use `https://github.com/` instead of `git@github.com:`
- Specify version using `rev`, `tag`, or `branch` parameter
- No token is included in the URL itself (git config handles authentication)

### 2. Git Authentication in CI (Already Configured!)

**If you're using Rhiza's template workflows, this is already set up for you.** All Rhiza workflows (CI, book, release, etc.) automatically include git authentication steps.

You can verify this by checking any Rhiza workflow file (e.g., `.github/workflows/rhiza_ci.yml`):

```yaml
- name: Configure git auth for private packages
  uses: ./.github/actions/configure-git-auth
```

Or for container-based workflows:

```yaml
- name: Configure git auth for private packages
  run: |
    git config --global url."https://${{ github.token }}@github.com/".insteadOf "https://github.com/"
```

**For custom workflows** (not synced from Rhiza), add the git authentication step yourself:

```yaml
- name: Configure git auth for private packages
  run: |
    git config --global url."https://${{ github.token }}@github.com/".insteadOf "https://github.com/"
```

This configuration tells git to automatically inject the `GITHUB_TOKEN` into all HTTPS GitHub URLs.

### 3. Using the Composite Action (Custom Workflows)

For custom workflows, you can use Rhiza's composite action instead of inline commands:

```yaml
- name: Configure git auth for private packages
  uses: ./.github/actions/configure-git-auth
```

This is cleaner and more maintainable than inline git config commands.

### 4. Complete Workflow Example

Here's a complete example of a GitHub Actions workflow that uses private packages:

```yaml
name: CI with Private Packages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.9.28"

      - name: Configure git auth for private packages
        run: |
          git config --global url."https://${{ github.token }}@github.com/".insteadOf "https://github.com/"

      - name: Install dependencies
        run: |
          uv sync --frozen

      - name: Run tests
        run: |
          uv run pytest
```

## Token Scopes

### Same Repository

The default `GITHUB_TOKEN` automatically has access to the **same repository** where the workflow runs:
- ✅ Is automatically provided by GitHub Actions
- ✅ Is scoped to the workflow run (secure)
- ✅ No manual token management required

This is sufficient if your private packages are defined within the same repository.

### Same Organization (Requires PAT)

**Important:** The default `GITHUB_TOKEN` typically does **not** have permission to read other private repositories, even within the same organization. This is GitHub's default security behavior.

To access private packages in other repositories within your organization, you need a Personal Access Token (PAT):

1. Create a PAT with `repo` scope (see [TOKEN_SETUP.md](TOKEN_SETUP.md) for instructions)
2. Add it as a repository secret (e.g., `PRIVATE_PACKAGES_TOKEN`)
3. Use it in the git config

**Note:** Some organizations configure settings to allow `GITHUB_TOKEN` cross-repository access, but this is not the default and should not be assumed. Using a PAT is the recommended approach for reliability.

### Different Organization

If your private packages are in a **different organization**, you need a Personal Access Token (PAT):

1. Create a PAT with `repo` scope (see [TOKEN_SETUP.md](TOKEN_SETUP.md) for instructions)
2. Add it as a repository secret (e.g., `PRIVATE_PACKAGES_TOKEN`)
3. Use it in the git config:

```yaml
- name: Configure git auth for private packages
  run: |
    git config --global url."https://${{ secrets.PRIVATE_PACKAGES_TOKEN }}@github.com/".insteadOf "https://github.com/"
```

## Local Development

For local development, you have several options:

### Option 1: Use GitHub CLI (Recommended)

```bash
# Install gh CLI
brew install gh  # macOS
# or: apt install gh  # Ubuntu/Debian

# Authenticate
gh auth login

# Configure git
gh auth setup-git
```

The GitHub CLI automatically handles git authentication for private repositories.

### Option 2: Use Personal Access Token

```bash
# Create a PAT with 'repo' scope at:
# https://github.com/settings/tokens

# Configure git
git config --global url."https://YOUR_TOKEN@github.com/".insteadOf "https://github.com/"
```

**Security Note:** Be careful not to commit this configuration. It's better to use `gh` CLI or SSH keys for local development.

### Option 3: Use SSH (Local Only)

For local development, you can continue using SSH:

```toml
[tool.uv.sources]
my-package = { git = "ssh://git@github.com/jebel-quant/my-package.git", rev = "v1.0.0" }
```

However, this won't work in CI without additional SSH key setup.

## Troubleshooting

### Error: "fatal: could not read Username"

This means git cannot find authentication credentials. Ensure:
1. The git config step runs **before** `uv sync`
2. The token has proper permissions
3. The repository URL uses HTTPS format

### Error: "Repository not found" or "403 Forbidden"

This means the token doesn't have access to the repository. Check:
1. The repository is in the same organization (for `GITHUB_TOKEN`)
2. Or use a PAT with `repo` scope (for different organizations)
3. The token hasn't expired

### Error: "Couldn't resolve host 'github.com'"

This is a network issue, not authentication. Check your network connection.

## Best Practices

1. **Use HTTPS URLs** in `pyproject.toml` for better CI/CD compatibility
2. **Rely on `GITHUB_TOKEN`** for same-org packages (automatic and secure)
3. **Pin versions** using `rev`, `tag`, or specific commit SHA for reproducibility
4. **Use `gh` CLI** for local development (easier than managing tokens)
5. **Keep tokens secure** - never commit them to the repository

## Related Documentation

- [TOKEN_SETUP.md](TOKEN_SETUP.md) - Setting up Personal Access Tokens
- [GitHub Actions: Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [uv: Git dependencies](https://docs.astral.sh/uv/concepts/dependencies/#git-dependencies)
