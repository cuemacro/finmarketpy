# Configure Git Auth for Private Packages

This composite action configures git to use token authentication for private GitHub packages.

## Usage

Add this step before installing dependencies that include private GitHub packages:

```yaml
- name: Configure git auth for private packages
  uses: ./.github/actions/configure-git-auth
  with:
    token: ${{ secrets.GH_PAT }}
```

The `GH_PAT` secret should be a Personal Access Token with `repo` scope.

## What It Does

This action runs:

```bash
git config --global url."https://<token>@github.com/".insteadOf "https://github.com/"
```

This tells git to automatically inject the token into all HTTPS GitHub URLs, enabling access to private repositories.

## When to Use

Use this action when your project has dependencies defined in `pyproject.toml` like:

```toml
[tool.uv.sources]
private-package = { git = "https://github.com/your-org/private-package.git", rev = "v1.0.0" }
```

## Token Requirements

By default, this action will use the workflow’s built-in `GITHUB_TOKEN` (`github.token`) if no `token` input is provided or if the provided value is empty (it uses `inputs.token || github.token` internally).

The `GITHUB_TOKEN` is usually sufficient when:

- installing dependencies hosted in the **same repository** as the workflow, or
- accessing **public** repositories.

The default `GITHUB_TOKEN` typically does **not** have permission to read other private repositories, even within the same organization. For that scenario, you should create a Personal Access Token (PAT) with `repo` scope and store it as `secrets.GH_PAT`, then pass it to the action via the `token` input.

If you configure the step as in the example (`token: ${{ secrets.GH_PAT }}`) and `secrets.GH_PAT` is not defined, GitHub Actions passes an empty string to the action. The composite action then falls back to `github.token`, so the configuration step itself still succeeds. However, any subsequent step that tries to access private repositories that are not covered by the permissions of `GITHUB_TOKEN` will fail with an authentication error.
## Example Workflow

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7

      - name: Configure git auth for private packages
        uses: ./.github/actions/configure-git-auth
        with:
          token: ${{ secrets.GH_PAT }}

      - name: Install dependencies
        run: uv sync --frozen

      - name: Run tests
        run: uv run pytest
```

## See Also

- [PRIVATE_PACKAGES.md](../../../.rhiza/docs/PRIVATE_PACKAGES.md) - Complete guide to using private packages
- [TOKEN_SETUP.md](../../../.rhiza/docs/TOKEN_SETUP.md) - Setting up Personal Access Tokens
