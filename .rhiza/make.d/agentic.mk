## customisations.mk - User-defined scripts and overrides
# This file is included by the main Makefile

# Declare phony targets
.PHONY: install-copilot install-claude analyse-repo summarise-changes

COPILOT_BIN ?= $(shell command -v copilot 2>/dev/null || echo "$(INSTALL_DIR)/copilot")
CLAUDE_BIN ?= $(shell command -v claude 2>/dev/null || echo "$(HOME)/.local/bin/claude")
DEFAULT_AI_MODEL ?= gpt-4.1

##@ Agentic Workflows

copilot: install-copilot ## open interactive prompt for copilot
	@"$(COPILOT_BIN)" --model "$(DEFAULT_AI_MODEL)"

claude: install-claude ## open interactive prompt for claude code
	@"$(CLAUDE_BIN)"

analyse-repo: install-copilot ## run the analyser agent to update REPOSITORY_ANALYSIS.md
	@"$(COPILOT_BIN)" --agent analyser \
		--model "$(DEFAULT_AI_MODEL)" \
		--prompt "Analyze the repository and update the journal." \
		--allow-tool 'write' --deny-tool 'remove' \
		--allow-all-paths

summarise-changes: install-copilot ## summarise changes since the most recent release/tag
	@"$(COPILOT_BIN)" -p "Show me the commits since the last release/tag and summarise them" --allow-tool 'shell(git)' --model "$(DEFAULT_AI_MODEL)" --agent summarise

install-copilot:  ## checks for copilot and prompts to install
	@if command -v copilot >/dev/null 2>&1; then \
	  printf "${GREEN}[INFO] copilot already installed in PATH, skipping install.${RESET}\n"; \
	elif [ -x "${INSTALL_DIR}/copilot" ]; then \
	  printf "${SUCCESS}[INFO] copilot already installed in ${INSTALL_DIR}, skipping install.${RESET}\n"; \
	else \
		printf "${YELLOW}[WARN] GitHub Copilot CLI not found in ${INSTALL_DIR}.${RESET}\n"; \
		printf "${BLUE}Do you want to install GitHub Copilot CLI? [y/N] ${RESET}"; \
		read -r response; \
		if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
			printf "${BLUE}[INFO] Installing GitHub Copilot CLI to ${INSTALL_DIR}...${RESET}\n"; \
			mkdir -p "${INSTALL_DIR}"; \
			if curl -fsSL https://gh.io/copilot-install | PREFIX="." bash; then \
				printf "${GREEN}[INFO] GitHub Copilot CLI installed successfully.${RESET}\n"; \
			else \
				printf "${RED}[ERROR] Failed to install GitHub Copilot CLI.${RESET}\n"; \
				exit 1; \
			fi; \
		else \
			printf "${BLUE}[INFO] Skipping installation.${RESET}\n"; \
		fi; \
	fi

install-claude:  ## checks for claude and prompts to install
	@if command -v claude >/dev/null 2>&1; then \
	  printf "${GREEN}[INFO] claude already installed in PATH, skipping install.${RESET}\n"; \
	else \
		printf "${YELLOW}[WARN] Claude Code CLI not found in PATH.${RESET}\n"; \
		printf "${BLUE}Do you want to install Claude Code CLI? [y/N] ${RESET}"; \
		read -r response; \
		if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
			printf "${BLUE}[INFO] Installing Claude Code CLI to default location (~/.local/bin/claude)...${RESET}\n"; \
			if curl -fsSL https://claude.ai/install.sh | bash; then \
				printf "${GREEN}[INFO] Claude Code CLI installed successfully.${RESET}\n"; \
			else \
				printf "${RED}[ERROR] Failed to install Claude Code CLI.${RESET}\n"; \
				exit 1; \
			fi; \
		else \
			printf "${BLUE}[INFO] Skipping installation.${RESET}\n"; \
		fi; \
	fi

