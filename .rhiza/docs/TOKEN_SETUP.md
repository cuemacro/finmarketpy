# GitHub Personal Access Token (PAT) Setup

This document explains how to set up a Personal Access Token (PAT) for the repository's automated workflows.

## Why is PAT_TOKEN needed?

The repository uses the `SYNC` workflow (`.github/workflows/rhiza_sync.yml`) to automatically synchronize with a template repository. When this workflow modifies files in `.github/workflows/`, GitHub requires special permissions that the default `GITHUB_TOKEN` doesn't have.

According to GitHub's security policy:
- The default `GITHUB_TOKEN` **cannot** create or update workflow files (`.github/workflows/*.yml`)
- A Personal Access Token with the `workflow` scope **is required** to push changes to workflow files

## Creating a PAT with workflow scope

Follow these steps to create a properly scoped Personal Access Token:

### 1. Navigate to GitHub Settings

1. Go to [GitHub.com](https://github.com)
2. Click your profile picture (top-right corner)
3. Click **Settings**
4. Scroll down and click **Developer settings** (bottom of left sidebar)
5. Click **Personal access tokens** → **Tokens (classic)**

### 2. Generate a new token

1. Click **Generate new token** → **Generate new token (classic)**
2. Give your token a descriptive name, e.g., `TinyCTA Workflow Sync Token`
3. Set an expiration date (recommended: 90 days or less for security)

### 3. Select the required scopes

**Required scopes:**
- ✅ `repo` (Full control of private repositories)
  - This automatically includes all repo sub-scopes
- ✅ `workflow` (Update GitHub Action workflows)
  - **This is critical** - without this scope, pushing workflow changes will fail

**Optional but recommended:**
- `write:packages` (if the workflow publishes packages)

### 4. Generate and copy the token

1. Click **Generate token** at the bottom
2. **Important:** Copy the token immediately - you won't be able to see it again!
3. Store it securely (e.g., in a password manager)

### 5. Add the token to repository secrets

1. Navigate to your repository on GitHub
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Name: `PAT_TOKEN`
6. Value: Paste the token you copied
7. Click **Add secret**

## Verifying the setup

After adding the `PAT_TOKEN` secret:

1. Navigate to **Actions** tab in your repository
2. Find the **SYNC** workflow
3. Click **Run workflow** to manually trigger it
4. If workflow files are modified, the workflow should successfully push them

## Troubleshooting

### Error: "refusing to allow a GitHub App to create or update workflow"

This error means either:
- The `PAT_TOKEN` secret is not set
- The `PAT_TOKEN` exists but lacks the `workflow` scope

**Solution:** Create a new token with the `workflow` scope and update the `PAT_TOKEN` secret.

### Error: "push_succeeded=false"

This usually indicates:
- The token has expired
- The token was revoked
- The token lacks necessary permissions

**Solution:** Generate a new token following the steps above and update the secret.

## Security best practices

1. **Limit scope:** Only grant the minimum required scopes (`repo` and `workflow`)
2. **Set expiration:** Use short-lived tokens (30-90 days) and rotate them regularly
3. **Monitor usage:** Regularly review your token usage in GitHub settings
4. **Revoke unused tokens:** Delete tokens that are no longer needed
5. **Use separate tokens:** Don't reuse tokens across multiple projects

## Alternative: GitHub App (Advanced)

For organizations, consider using a GitHub App instead of PAT:
- More secure and granular permissions
- Better audit logging
- No expiration issues
- Requires more setup complexity

Refer to [GitHub's documentation](https://docs.github.com/en/apps) for details on creating GitHub Apps.
