# Shell Completion for Rhiza Make Targets

This directory contains shell completion scripts for Bash and Zsh that provide tab-completion for make targets in Rhiza-based projects.

## Features

- ✅ Tab-complete all available make targets
- ✅ Show target descriptions in Zsh
- ✅ Complete common make variables (DRY_RUN, BUMP, ENV, etc.)
- ✅ Works with any Rhiza-based project
- ✅ Auto-discovers targets from Makefile and included .mk files

## Installation

### Bash

#### Method 1: Source in your shell config

Add to your `~/.bashrc` or `~/.bash_profile`:

```bash
# Rhiza make completion
if [ -f /path/to/project/.rhiza/completions/rhiza-completion.bash ]; then
    source /path/to/project/.rhiza/completions/rhiza-completion.bash
fi
```

Replace `/path/to/project` with the actual path to your Rhiza project.

#### Method 2: System-wide installation

```bash
# Copy to bash completion directory
sudo cp .rhiza/completions/rhiza-completion.bash /etc/bash_completion.d/rhiza

# Reload completions
source /etc/bash_completion.d/rhiza
```

#### Method 3: User-local installation

```bash
# Create local completion directory
mkdir -p ~/.local/share/bash-completion/completions

# Copy completion script
cp .rhiza/completions/rhiza-completion.bash ~/.local/share/bash-completion/completions/make

# Reload bash
source ~/.bashrc
```

### Zsh

#### Method 1: User-local installation (Recommended)

```bash
# Create completion directory
mkdir -p ~/.zsh/completion

# Copy completion script
cp .rhiza/completions/rhiza-completion.zsh ~/.zsh/completion/_make

# Add to ~/.zshrc (if not already present)
echo 'fpath=(~/.zsh/completion $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc

# Reload zsh
source ~/.zshrc
```

#### Method 2: Source directly

Add to your `~/.zshrc`:

```zsh
# Rhiza make completion
if [ -f /path/to/project/.rhiza/completions/rhiza-completion.zsh ]; then
    source /path/to/project/.rhiza/completions/rhiza-completion.zsh
fi
```

#### Method 3: System-wide installation

```bash
# Copy to system completion directory
sudo cp .rhiza/completions/rhiza-completion.zsh /usr/local/share/zsh/site-functions/_make

# Reload zsh
exec zsh
```

## Usage

Once installed, you can tab-complete make targets:

```bash
# Tab-complete targets
make <TAB>

# Complete with prefix
make te<TAB>  # Expands to: make test

# Complete variables
make BUMP=<TAB>  # Shows: patch, minor, major

# Works with any target
make doc<TAB>  # Shows: docs, docker-build, docker-run, etc.
```

### Zsh Benefits

In Zsh, you'll also see descriptions for targets:

```bash
make <TAB>
# Shows:
# test        -- run all tests
# fmt         -- check the pre-commit hooks and the linting
# install     -- install
# docs        -- create documentation with pdoc
# ...
```

## Common Variables

The completion scripts understand these common variables:

| Variable | Values | Description |
|----------|--------|-------------|
| `DRY_RUN` | `1` | Preview mode without making changes |
| `BUMP` | `patch`, `minor`, `major` | Version bump type |
| `ENV` | `dev`, `staging`, `prod` | Target environment |
| `COVERAGE_FAIL_UNDER` | (number) | Minimum coverage threshold |
| `PYTHON_VERSION` | (version) | Override Python version |

Example usage:

```bash
# Tab-complete after typing DRY_
make DRY_<TAB>     # Expands to: make DRY_RUN=1

# Tab-complete variable values
make BUMP=<TAB>    # Shows: patch minor major

# Combine with targets
make bump BUMP=<TAB>
```

## Troubleshooting

### Bash: Completions not working

1. Check if bash-completion is installed:
   ```bash
   # Debian/Ubuntu
   sudo apt-get install bash-completion

   # macOS
   brew install bash-completion@2
   ```

2. Ensure completion is enabled in your shell:
   ```bash
   # Add to ~/.bashrc if not present
   if [ -f /etc/bash_completion ]; then
       . /etc/bash_completion
   fi
   ```

3. Reload your shell configuration:
   ```bash
   source ~/.bashrc
   ```

### Zsh: Completions not working

1. Check if compinit is called in your `~/.zshrc`:
   ```zsh
   autoload -U compinit && compinit
   ```

2. Clear the completion cache:
   ```bash
   rm -f ~/.zcompdump
   compinit
   ```

3. Ensure the script is in your fpath:
   ```zsh
   echo $fpath
   ```

4. Reload your shell configuration:
   ```zsh
   source ~/.zshrc
   ```

### No targets appearing

1. Ensure you're in a directory with a Makefile:
   ```bash
   ls -la Makefile
   ```

2. Test that make can parse the Makefile:
   ```bash
   make -qp 2>/dev/null | head
   ```

3. Manually source the completion script to test:
   ```bash
   # Bash
   source .rhiza/completions/rhiza-completion.bash

   # Zsh
   source .rhiza/completions/rhiza-completion.zsh
   ```

## Optional Aliases

You can add shortcuts in your shell config:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias m='make'

# For bash:
complete -F _rhiza_make_completion m

# For zsh:
compdef _rhiza_make m
```

Then use:
```bash
m te<TAB>  # Expands to: m test
```

## Technical Details

### How it works

1. **Target Discovery**: Parses `make -qp` output to find all targets
2. **Description Extraction**: Looks for `##` comments after target names
3. **Variable Detection**: Includes common Makefile variables
4. **Dynamic Completion**: Regenerates list each time you tab

### Performance

- Completions are generated on-demand (when you press Tab)
- For large Makefiles (100+ targets), there may be a small delay
- Results are not cached to ensure targets are always current

## See Also

- [Tools Reference](../../docs/reference/TOOLS_REFERENCE.md) - Complete command reference
- [Quick Reference](../../docs/guides/QUICK_REFERENCE.md) - Quick command reference
- [Extending Rhiza](../../docs/guides/EXTENDING_RHIZA.md) - How to add custom targets

---

*Last updated: 2026-02-15*
