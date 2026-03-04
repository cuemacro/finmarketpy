## gh-aw.mk - GitHub Agentic Workflows (gh-aw) integration
# This file provides Makefile targets for GitHub Agentic Workflows

# Declare phony targets
.PHONY: install-gh-aw gh-aw-compile gh-aw-compile-strict gh-aw-status gh-aw-run gh-aw-init gh-aw-secrets gh-aw-logs gh-aw-validate gh-aw-setup

# Detect if gh-aw extension is installed
GH_AW_BIN ?= $(shell gh extension list 2>/dev/null | grep -q gh-aw && echo "gh aw" || echo "")

##@ GitHub Agentic Workflows (gh-aw)

install-gh-aw: require-gh ## install the gh-aw CLI extension
	@if gh extension list 2>/dev/null | grep -q gh-aw; then \
		printf "$${GREEN}[INFO] gh-aw extension already installed.${RESET}\n"; \
	else \
		printf "$${BLUE}[INFO] Installing gh-aw extension...${RESET}\n"; \
		gh extension install github/gh-aw; \
		printf "$${GREEN}[INFO] gh-aw extension installed.${RESET}\n"; \
	fi

gh-aw-compile: install-gh-aw ## compile all agentic workflow .md files to .lock.yml
	@gh aw compile

gh-aw-compile-strict: install-gh-aw ## compile with strict security validation
	@gh aw compile --strict

gh-aw-status: install-gh-aw ## show status of all agentic workflows
	@gh aw status

gh-aw-run: install-gh-aw ## run a specific agentic workflow (usage: make gh-aw-run WORKFLOW=<name>)
	@if [ -z "$(WORKFLOW)" ]; then \
		printf "$${RED}[ERROR] Specify WORKFLOW=<name>. Example: make gh-aw-run WORKFLOW=daily-repo-status${RESET}\n"; \
		exit 1; \
	fi
	@gh aw run $(WORKFLOW)

gh-aw-init: install-gh-aw ## initialise repository for gh-aw (adds .vscode, prompts, settings)
	@gh aw init

gh-aw-secrets: install-gh-aw ## bootstrap/check gh-aw secrets
	@gh aw secrets bootstrap

gh-aw-logs: install-gh-aw ## show logs for recent agentic workflow runs
	@gh aw logs

gh-aw-validate: install-gh-aw ## validate lock files are up-to-date
	@gh aw compile --check

gh-aw-setup: install-gh-aw ## guided setup for gh-aw secrets and engine configuration
	@printf "$${BLUE}[INFO] Setting up GitHub Agentic Workflows...${RESET}\n"
	@printf "$${BLUE}Which AI engine will you use?${RESET}\n"
	@printf "  1) Copilot (requires COPILOT_GITHUB_TOKEN)\n"
	@printf "  2) Claude  (requires ANTHROPIC_API_KEY)\n"
	@printf "  3) Codex   (requires OPENAI_API_KEY)\n"
	@printf "$${BLUE}Choice [1]: ${RESET}"; \
	read -r choice; \
	case "$${choice:-1}" in \
		1) gh aw secrets set COPILOT_GITHUB_TOKEN ;; \
		2) gh aw secrets set ANTHROPIC_API_KEY ;; \
		3) gh aw secrets set OPENAI_API_KEY ;; \
		*) printf "$${RED}Invalid choice.${RESET}\n"; exit 1 ;; \
	esac
	@gh aw secrets bootstrap
	@printf "$${GREEN}[INFO] Setup complete. Run 'make gh-aw-status' to verify.${RESET}\n"
