#!/usr/bin/env bash
# Bash completion for Rhiza make targets
#
# Installation:
#   Source this file in your ~/.bashrc or ~/.bash_profile:
#     source /path/to/.rhiza/completions/rhiza-completion.bash
#
#   Or copy to bash completion directory:
#     sudo cp .rhiza/completions/rhiza-completion.bash /etc/bash_completion.d/rhiza
#

_rhiza_make_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Check if we're in a directory with a Makefile
    if [[ ! -f "Makefile" ]]; then
        return 0
    fi

    # Extract make targets from Makefile and all included .mk files
    # Looks for lines like: target: ## description
    opts=$(make -qp 2>/dev/null | \
           awk -F':' '/^[a-zA-Z0-9][^$#\/	=]*:([^=]|$)/ {split($1,A,/ /);for(i in A)print A[i]}' | \
           grep -v '^Makefile$' | \
           sort -u)

    # Add common make variables that can be overridden
    local vars="DRY_RUN=1 BUMP=patch BUMP=minor BUMP=major ENV=dev ENV=staging ENV=prod"
    opts="$opts $vars"

    # Generate completions
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

# Register the completion function for make command
complete -F _rhiza_make_completion make

# Also complete for direct make invocation with path
complete -F _rhiza_make_completion ./Makefile

# Helpful aliases (optional - uncomment if desired)
# alias m='make'
# complete -F _rhiza_make_completion m
