## .rhiza/make.d/releasing.mk - Releasing and Versioning
# This file provides targets for version bumping and release management.

# Declare phony targets (they don't produce files)
.PHONY: bump release publish release-status pre-bump post-bump pre-release post-release

# Hook targets (double-colon rules allow multiple definitions)
pre-bump:: ; @:
post-bump:: ; @:
pre-release:: ; @:
post-release:: ; @:

# DRY_RUN support: pass DRY_RUN=1 to preview changes without applying them
_DRY_RUN_FLAG := $(if $(DRY_RUN),--dry-run,)
_VERSION=0.3.3

##@ Releasing and Versioning
bump: pre-bump ## bump version of the project (supports DRY_RUN=1)
	@if [ -f "pyproject.toml" ]; then \
		$(MAKE) install; \
		PATH="$(abspath ${VENV})/bin:$$PATH" ${UVX_BIN} "rhiza-tools>=$(_VERSION)" bump $(_DRY_RUN_FLAG); \
		if [ -z "$(DRY_RUN)" ]; then \
			printf "${BLUE}[INFO] Checking uv.lock file...${RESET}\n"; \
			${UV_BIN} lock; \
		fi; \
	else \
		printf "${YELLOW}[WARN] No pyproject.toml found, skipping bump${RESET}\n"; \
	fi
	@$(MAKE) post-bump

release: pre-release install-uv ## create tag and push to remote repository triggering release workflow (supports DRY_RUN=1)
	${UVX_BIN} "rhiza-tools>=$(_VERSION)" release $(_DRY_RUN_FLAG);
	@$(MAKE) post-release

publish: pre-release install-uv ## bump version, create tag and push in one step (supports DRY_RUN=1)
	${UVX_BIN} "rhiza-tools>=$(_VERSION)" release --with-bump $(_DRY_RUN_FLAG);
	@$(MAKE) post-release

release-status: ## show release workflow status and latest release information
ifeq ($(FORGE_TYPE),github)
	@{ $(MAKE) --no-print-directory workflow-status; printf "\n"; $(MAKE) --no-print-directory latest-release; } 2>&1 | $${PAGER:-less -R}
else ifeq ($(FORGE_TYPE),gitlab)
	@printf "${YELLOW}[WARN] GitLab detected — release-status is not yet supported for GitLab repositories.${RESET}\n"
	@printf "${BLUE}[INFO] Please check your pipeline status in the GitLab UI.${RESET}\n"
else
	@printf "${RED}[ERROR] Could not detect forge type (.github/workflows/ or .gitlab-ci.yml not found)${RESET}\n"
endif



