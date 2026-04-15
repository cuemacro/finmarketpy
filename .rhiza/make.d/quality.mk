## .rhiza/make.d/quality.mk - Quality and Formatting
# This file provides targets for code quality checks, linting, and formatting.

# Configurable list of licenses that fail the compliance scan (semicolon-separated)
LICENSE_FAIL_ON ?= GPL;LGPL;AGPL

# Declare phony targets (they don't produce files)
.PHONY: all deptry fmt license todos suppression-audit

##@ Quality and Formatting
all: fmt deptry test docs-coverage security license typecheck rhiza-test ## run all CI targets locally

deptry: install-uv ## Run deptry
	@if [ -d ${SOURCE_FOLDER} ]; then \
		$(UVX_BIN) -p ${PYTHON_VERSION} deptry ${SOURCE_FOLDER}; \
	fi

	@if [ -d ${MARIMO_FOLDER} ]; then \
		if [ -d ${SOURCE_FOLDER} ]; then \
			$(UVX_BIN) -p ${PYTHON_VERSION} deptry ${MARIMO_FOLDER} ${SOURCE_FOLDER} --ignore DEP004; \
		else \
		  	$(UVX_BIN) -p ${PYTHON_VERSION} deptry ${MARIMO_FOLDER} --ignore DEP004; \
		fi \
	fi

fmt: install-uv ## check the pre-commit hooks and the linting
	@${UVX_BIN} -p ${PYTHON_VERSION} pre-commit run --all-files

todos: ## search and report all TODO/FIXME/HACK comments in the codebase
	@printf "${BLUE}[INFO] Searching for TODO, FIXME, and HACK comments...${RESET}\n"
	@printf "${BOLD}Found the following items:${RESET}\n\n"
	@find . -type f \( -name "*.py" -o -name "*.mk" -o -name "*.sh" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \) \
		-not -path "./.venv/*" \
		-not -path "./.git/*" \
		-not -path "./node_modules/*" \
		-not -path "./.tox/*" \
		-not -path "./build/*" \
		-not -path "./dist/*" \
		-print0 | xargs -0 grep -nHE "(TODO|FIXME|HACK):" 2>/dev/null | \
		grep -v "make todos" | \
		awk -F: '{ printf "${YELLOW}%s${RESET}:${GREEN}%s${RESET}: %s\n", $$1, $$2, substr($$0, index($$0,$$3)) }' || \
		printf "${GREEN}[SUCCESS] No TODO/FIXME/HACK comments found!${RESET}\n"
	@printf "\n${BLUE}[INFO] Search complete.${RESET}\n"

suppression-audit: ## scan codebase for inline suppressions and report (grade, detail, histogram)
	@printf "${BLUE}[INFO] Running suppression audit...${RESET}\n"
	@${UV_BIN} run python .rhiza/utils/suppression_audit.py

license: install ## run license compliance scan (fail on GPL, LGPL, AGPL)
	@printf "${BLUE}[INFO] Running license compliance scan...${RESET}\n"
	@${UV_BIN} run --with pip-licenses pip-licenses --fail-on="${LICENSE_FAIL_ON}"
