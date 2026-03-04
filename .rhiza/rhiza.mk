## Makefile for jebel-quant/rhiza
# (https://github.com/jebel-quant/rhiza)
#
# Purpose: Developer tasks using uv/uvx (install, test, docs, marimushka, book).
# Lines with `##` after a target are parsed into help text,
# and lines starting with `##@` create section headers in the help output.
#
# Colours for pretty output in help messages
BLUE := \033[36m
BOLD := \033[1m
GREEN := \033[32m
RED := \033[31m
YELLOW := \033[33m
RESET := \033[0m

# Default goal when running `make` with no target
.DEFAULT_GOAL := help

# Declare phony targets (they don't produce files)
.PHONY: \
	help \
	post-bump \
	post-install \
	post-release \
	post-sync \
	post-validate \
	pre-bump \
	pre-install \
	pre-release \
	pre-sync \
	pre-validate \
	print-logo \
	readme \
	summarise-sync \
	sync \
	sync-experimental \
	validate \
	version-matrix

# we need absolute paths!
INSTALL_DIR ?= $(abspath ./bin)
UV_BIN ?= $(shell command -v uv 2>/dev/null || echo ${INSTALL_DIR}/uv)
UVX_BIN ?= $(shell command -v uvx 2>/dev/null || echo ${INSTALL_DIR}/uvx)
VENV ?= .venv

# Read Python version from .python-version (single source of truth)
PYTHON_VERSION ?= $(shell cat .python-version 2>/dev/null || echo "3.13")
export PYTHON_VERSION

# Read Rhiza version from .rhiza/.rhiza-version (single source of truth for rhiza-tools)
RHIZA_VERSION ?= $(shell cat .rhiza/.rhiza-version 2>/dev/null || echo "0.10.2")
export RHIZA_VERSION

export UV_NO_MODIFY_PATH := 1
export UV_VENV_CLEAR := 1

# Unset VIRTUAL_ENV to prevent uv from warning about path mismatches
# when a virtual environment is already activated in the shell
unexport VIRTUAL_ENV

# Load .rhiza/.env (if present) and export its variables so recipes see them.
-include .rhiza/.env

# ==============================================================================
# Rhiza Core
# ==============================================================================

# RHIZA_LOGO definition
define RHIZA_LOGO
  ____  _     _
 |  _ \| |__ (_)______ _
 | |_) | '_ \| |_  / _\`|
 |  _ <| | | | |/ / (_| |
 |_| \_\_| |_|_/___\__,_|

endef
export RHIZA_LOGO

# Declare phony targets for Rhiza Core
.PHONY: print-logo sync sync-experimental validate readme pre-sync post-sync pre-validate post-validate

# Hook targets (double-colon rules allow multiple definitions)
# Note: pre-install/post-install are defined in bootstrap.mk
# Note: pre-bump/post-bump/pre-release/post-release are defined in releasing.mk
pre-sync:: ; @:
post-sync:: ; @:
pre-validate:: ; @:
post-validate:: ; @:

##@ Rhiza Workflows

print-logo:
	@printf "${BLUE}$$RHIZA_LOGO${RESET}\n"


sync: pre-sync ## sync with template repository as defined in .rhiza/template.yml
	@if git remote get-url origin 2>/dev/null | grep -iqE 'jebel-quant/rhiza(\.git)?$$'; then \
		printf "${BLUE}[INFO] Skipping sync in rhiza repository (no template.yml by design)${RESET}\n"; \
	else \
		$(MAKE) install-uv; \
		${UVX_BIN} "rhiza>=$(RHIZA_VERSION)" sync .; \
	fi
	@$(MAKE) post-sync

sync-experimental: pre-sync ## sync with template repository using cruft-based merge (experimental, requires rhiza-cli >= 0.11.1-beta.1)
	@printf "${YELLOW}[WARN] sync-experimental uses a beta version of rhiza-cli (>= 0.11.1-beta.1) and is not yet stable${RESET}\n"
	@if git remote get-url origin 2>/dev/null | grep -iqE 'jebel-quant/rhiza(\.git)?$$'; then \
		printf "${BLUE}[INFO] Skipping sync-experimental in rhiza repository (no template.yml by design)${RESET}\n"; \
	else \
		$(MAKE) install-uv; \
		${UVX_BIN} "rhiza>=0.11.1b1" sync .; \
	fi
	@$(MAKE) post-sync

summarise-sync: install-uv ## summarise differences created by sync with template repository
	@if git remote get-url origin 2>/dev/null | grep -iqE 'jebel-quant/rhiza(\.git)?$$'; then \
		printf "${BLUE}[INFO] Skipping summarise-sync in rhiza repository (no template.yml by design)${RESET}\n"; \
	else \
		$(MAKE) install-uv; \
		${UVX_BIN} "rhiza>=$(RHIZA_VERSION)" summarise .; \
	fi

rhiza-test: install ## run rhiza's own tests (if any)
	@if [ -d ".rhiza/tests" ]; then \
		${UV_BIN} run pytest .rhiza/tests; \
	else \
		printf "${YELLOW}[WARN] No .rhiza/tests directory found, skipping rhiza-tests${RESET}\n"; \
	fi

validate: pre-validate rhiza-test ## validate project structure against template repository as defined in .rhiza/template.yml
	@if git remote get-url origin 2>/dev/null | grep -iqE 'jebel-quant/rhiza(\.git)?$$'; then \
		printf "${BLUE}[INFO] Skipping validate in rhiza repository (no template.yml by design)${RESET}\n"; \
	else \
		$(MAKE) install-uv; \
		${UVX_BIN} "rhiza>=$(RHIZA_VERSION)" validate .; \
	fi
	@$(MAKE) post-validate

readme: install-uv ## update README.md with current Makefile help output
	@${UVX_BIN} "rhiza-tools>=0.2.0" update-readme

##@ Meta

help: print-logo ## Display this help message
	+@printf "$(BOLD)Usage:$(RESET)\n"
	+@printf "  make $(BLUE)<target>$(RESET)\n\n"
	+@printf "$(BOLD)Targets:$(RESET)\n"
	+@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	+@printf "\n"

version-matrix: install-uv ## Emit the list of supported Python versions from pyproject.toml
	@${UVX_BIN} "rhiza-tools>=0.2.2" version-matrix

print-% : ## print the value of a variable (usage: make print-VARIABLE)
	@printf "${BLUE}[INFO] Printing value of variable '$*':${RESET}\n"
	@printf "${BOLD}Value of $*:${RESET}\n"
	@printf "${GREEN}"
	@printf "%s\n" "$($*)"
	@printf "${RESET}"
	@printf "${BLUE}[INFO] End of value for '$*'${RESET}\n"

# Optional: repo extensions (committed)
-include .rhiza/make.d/*.mk

