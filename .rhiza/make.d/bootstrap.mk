## .rhiza/make.d/bootstrap.mk - Bootstrap and Installation
# This file provides targets for setting up the development environment,
# installing dependencies, and cleaning project artifacts.

# Declare phony targets (they don't produce files)
.PHONY: install-uv install clean pre-install post-install

# Hook targets (double-colon rules allow multiple definitions)
pre-install:: ; @:
post-install:: ; @:

##@ Bootstrap
install-uv: ## ensure uv/uvx is installed
	# Ensure the ${INSTALL_DIR} folder exists
	@mkdir -p ${INSTALL_DIR}

	# Install uv/uvx only if they are not already present in PATH or in the install dir
	@if command -v uv >/dev/null 2>&1 && command -v uvx >/dev/null 2>&1; then \
	  :; \
	elif [ -x "${INSTALL_DIR}/uv" ] && [ -x "${INSTALL_DIR}/uvx" ]; then \
	  printf "${BLUE}[INFO] uv and uvx already installed in ${INSTALL_DIR}, skipping.${RESET}\n"; \
	else \
	  printf "${BLUE}[INFO] Installing uv and uvx into ${INSTALL_DIR}...${RESET}\n"; \
	  if ! curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="${INSTALL_DIR}" sh >/dev/null 2>&1; then \
	    printf "${RED}[ERROR] Failed to install uv${RESET}\n"; \
	    exit 1; \
	  fi; \
	fi

install: pre-install install-uv ## install
	# Create the virtual environment only if it doesn't exist
	@if [ ! -d "${VENV}" ]; then \
	  ${UV_BIN} venv $(if $(PYTHON_VERSION),--python $(PYTHON_VERSION)) ${VENV} || { printf "${RED}[ERROR] Failed to create virtual environment${RESET}\n"; exit 1; }; \
	else \
	  printf "${BLUE}[INFO] Using existing virtual environment at ${VENV}, skipping creation${RESET}\n"; \
	fi

	# Install the dependencies from pyproject.toml (if it exists)
	@if [ -f "pyproject.toml" ]; then \
	  if [ -f "uv.lock" ]; then \
	    if ! ${UV_BIN} lock --check >/dev/null 2>&1; then \
	      printf "${YELLOW}[WARN] uv.lock is out of sync with pyproject.toml${RESET}\n"; \
	      printf "${YELLOW}       Run 'uv sync' to update your lock file and environment${RESET}\n"; \
	      printf "${YELLOW}       Or run 'uv lock' to update only the lock file${RESET}\n"; \
	      exit 1; \
	    fi; \
	    printf "${BLUE}[INFO] Installing dependencies from lock file${RESET}\n"; \
	    ${UV_BIN} sync --all-extras --all-groups --frozen || { printf "${RED}[ERROR] Failed to install dependencies${RESET}\n"; exit 1; }; \
	  else \
	    printf "${YELLOW}[WARN] uv.lock not found. Generating lock file and installing dependencies...${RESET}\n"; \
	    ${UV_BIN} sync --all-extras || { printf "${RED}[ERROR] Failed to install dependencies${RESET}\n"; exit 1; }; \
	  fi; \
	else \
	  printf "${YELLOW}[WARN] No pyproject.toml found, skipping install${RESET}\n"; \
	fi

	# Install dev dependencies from .rhiza/requirements/*.txt files
	@if [ -d ".rhiza/requirements" ] && ls .rhiza/requirements/*.txt >/dev/null 2>&1; then \
	  for req_file in .rhiza/requirements/*.txt; do \
	    if [ -f "$$req_file" ]; then \
	      printf "${BLUE}[INFO] Installing requirements from $$req_file${RESET}\n"; \
	      ${UV_BIN} pip install -r "$$req_file" || { printf "${RED}[ERROR] Failed to install requirements from $$req_file${RESET}\n"; exit 1; }; \
	    fi; \
	  done; \
	fi

	# Check if there is requirements.txt file in the tests folder (legacy support)
	@if [ -f "tests/requirements.txt" ]; then \
	  printf "${BLUE}[INFO] Installing requirements from tests/requirements.txt${RESET}\n"; \
	  ${UV_BIN} pip install -r tests/requirements.txt || { printf "${RED}[ERROR] Failed to install test requirements${RESET}\n"; exit 1; }; \
	fi

	# Install pre-commit hooks
	@if [ -f ".pre-commit-config.yaml" ]; then \
	  printf "${BLUE}[INFO] Installing pre-commit hooks...${RESET}\n"; \
	  ${UVX_BIN} -p ${PYTHON_VERSION} pre-commit install || { printf "${YELLOW}[WARN] Failed to install pre-commit hooks${RESET}\n"; }; \
	fi

	@$(MAKE) post-install
	
	# Display success message with activation instructions
	@printf "\n${GREEN}[SUCCESS] Installation complete!${RESET}\n\n"
	@printf "${BLUE}To activate the virtual environment, run:${RESET}\n"
	@printf "${YELLOW}  source ${VENV}/bin/activate${RESET}\n\n"

clean: ## Clean project artifacts and stale local branches
	@printf "%bCleaning project...%b\n" "$(BLUE)" "$(RESET)"

	# Remove ignored files/directories, but keep .env files, tested with futures project
	@git clean -d -X -f \
		-e '!.env' \
		-e '!.env.*'

	# Remove build & test artifacts
	@rm -rf \
		dist \
		build \
		*.egg-info \
		.coverage \
		.pytest_cache \
		.benchmarks

	@printf "%bRemoving local branches with no remote counterpart...%b\n" "$(BLUE)" "$(RESET)"

	@git fetch --prune

	@git branch -vv | awk '/: gone]/{print $$1}' | xargs -r git branch -D
