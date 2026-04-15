#compdef make
# Zsh completion for Rhiza make targets
#
# Installation:
#   Add this file to your fpath and ensure compinit is called:
#
#   Method 1 (User-local):
#     mkdir -p ~/.zsh/completion
#     cp .rhiza/completions/rhiza-completion.zsh ~/.zsh/completion/_make
#     Add to ~/.zshrc:
#       fpath=(~/.zsh/completion $fpath)
#       autoload -U compinit && compinit
#
#   Method 2 (Source directly):
#     Add to ~/.zshrc:
#       source /path/to/.rhiza/completions/rhiza-completion.zsh
#
#   Method 3 (System-wide):
#     sudo cp .rhiza/completions/rhiza-completion.zsh /usr/local/share/zsh/site-functions/_make
#

_rhiza_make() {
    local -a targets variables

    # Check if we're in a directory with a Makefile
    if [[ ! -f "Makefile" ]]; then
        return 0
    fi

    # Extract make targets with descriptions
    # Format: target:description
    targets=(${(f)"$(
        make -qp 2>/dev/null | \
        awk -F':' '
            /^# Files/,/^# Finished Make data base/ {
                if (/^[a-zA-Z0-9_-]+:.*##/) {
                    target=$1
                    desc=$0
                    sub(/^[^#]*## */, "", desc)
                    gsub(/^[ 	]+/, "", target)
                    print target ":" desc
                }
            }
        ' | \
        grep -v '^Makefile:' | \
        sort -u
    )"})

    # Also get targets without descriptions
    local -a plain_targets
    plain_targets=(${(f)"$(
        make -qp 2>/dev/null | \
        awk -F':' '/^[a-zA-Z0-9_-]+:([^=]|$)/ {
            split($1,A,/ /)
            for(i in A) print A[i]
        }' | \
        grep -v '^Makefile$' | \
        sort -u
    )"})

    # Common make variables
    variables=(
        'DRY_RUN=1:preview mode without making changes'
        'BUMP=patch:bump patch version'
        'BUMP=minor:bump minor version'
        'BUMP=major:bump major version'
        'ENV=dev:development environment'
        'ENV=staging:staging environment'
        'ENV=prod:production environment'
        'COVERAGE_FAIL_UNDER=:minimum coverage threshold'
        'PYTHON_VERSION=:override Python version'
    )

    # Combine all completions
    local -a all_completions
    all_completions=($targets $plain_targets $variables)

    # Show completions with descriptions
    _describe 'make targets' all_completions
}

# Register the completion function
compdef _rhiza_make make

# Optional: Add completion for common aliases
# Uncomment these if you use these aliases
# alias m='make'
# compdef _rhiza_make m
