## docs.mk - Documentation generation targets
# This file is included by the main Makefile.
# It provides targets for generating API documentation using pdoc
# and building/serving MkDocs documentation sites.

# Declare phony targets (they don't produce files)
.PHONY: docs mkdocs mkdocs-serve mkdocs-build

# Default output directory for MkDocs (HTML site)
MKDOCS_OUTPUT ?= _mkdocs

# MkDocs config file location
MKDOCS_CONFIG ?= docs/mkdocs.yml

# Default pdoc template directory (can be overridden)
PDOC_TEMPLATE_DIR ?= book/pdoc-templates

##@ Documentation

# The 'docs' target generates API documentation using pdoc.
# 1. Identifies Python packages within the source folder.
# 2. Detects the docformat (google, numpy, or sphinx) from ruff.toml or defaults to google.
# 3. Installs pdoc and generates HTML documentation in _pdoc.
docs:: install ## create documentation with pdoc
	# Clean up previous docs
	rm -rf _pdoc;

	@if [ -d "${SOURCE_FOLDER}" ]; then \
	  PKGS=""; for d in "${SOURCE_FOLDER}"/*; do [ -d "$$d" ] && PKGS="$$PKGS $$(basename "$$d")"; done; \
	  if [ -z "$$PKGS" ]; then \
	    printf "${YELLOW}[WARN] No packages found under ${SOURCE_FOLDER}, skipping docs${RESET}\n"; \
	  else \
	    TEMPLATE_ARG=""; \
	    if [ -d "$(PDOC_TEMPLATE_DIR)" ]; then \
	      TEMPLATE_ARG="-t $(PDOC_TEMPLATE_DIR)"; \
	      printf "$(BLUE)[INFO] Using pdoc templates from $(PDOC_TEMPLATE_DIR)$(RESET)\n"; \
	    fi; \
	    DOCFORMAT="$(DOCFORMAT)"; \
	    if [ -z "$$DOCFORMAT" ]; then \
	      if [ -f "ruff.toml" ]; then \
	        DOCFORMAT=$$(${UV_BIN} run python -c "import tomllib; print(tomllib.load(open('ruff.toml', 'rb')).get('lint', {}).get('pydocstyle', {}).get('convention', ''))"); \
	      fi; \
	      if [ -z "$$DOCFORMAT" ]; then \
	        DOCFORMAT="google"; \
	      fi; \
	      printf "${BLUE}[INFO] Detected docformat: $$DOCFORMAT${RESET}\n"; \
	    else \
	      printf "${BLUE}[INFO] Using provided docformat: $$DOCFORMAT${RESET}\n"; \
	    fi; \
	    LOGO_ARG=""; \
	    if [ -n "$(LOGO_FILE)" ]; then \
	      if [ -f "$(LOGO_FILE)" ]; then \
	        MIME=$$(file --mime-type -b "$(LOGO_FILE)"); \
	        DATA=$$(base64 < "$(LOGO_FILE)" | tr -d '\n'); \
	        LOGO_ARG="--logo data:$$MIME;base64,$$DATA"; \
	        printf "${BLUE}[INFO] Embedding logo: $(LOGO_FILE)${RESET}\n"; \
	      else \
	        printf "${YELLOW}[WARN] Logo file $(LOGO_FILE) not found, skipping${RESET}\n"; \
	      fi; \
	    fi; \
	    ${UV_BIN} pip install pdoc && \
	    PYTHONPATH="${SOURCE_FOLDER}" ${UV_BIN} run pdoc --docformat $$DOCFORMAT --output-dir _pdoc $$TEMPLATE_ARG $$LOGO_ARG $$PKGS; \
	  fi; \
	else \
	  printf "${YELLOW}[WARN] Source folder ${SOURCE_FOLDER} not found, skipping docs${RESET}\n"; \
	fi

# The 'mkdocs-build' target builds the MkDocs documentation site.
# 1. Checks if the mkdocs.yml config file exists.
# 2. Cleans up any previous output.
# 3. Builds the static site using mkdocs with material theme.
mkdocs-build:: install-uv ## build MkDocs documentation site
	@printf "${BLUE}[INFO] Building MkDocs site...${RESET}\n"
	@if [ -f "$(MKDOCS_CONFIG)" ]; then \
	  rm -rf "$(MKDOCS_OUTPUT)"; \
	  MKDOCS_OUTPUT_ABS="$$(pwd)/$(MKDOCS_OUTPUT)"; \
	  ${UVX_BIN} --with "mkdocs-material<10.0" --with "pymdown-extensions>=10.0" --with "mkdocs<2.0" mkdocs build \
	    -f "$(MKDOCS_CONFIG)" \
	    -d "$$MKDOCS_OUTPUT_ABS"; \
	else \
	  printf "${YELLOW}[WARN] $(MKDOCS_CONFIG) not found, skipping MkDocs build${RESET}\n"; \
	fi

# The 'mkdocs-serve' target serves the documentation with live reload.
# Useful for local development and previewing changes.
mkdocs-serve: install-uv ## serve MkDocs site with live reload
	@if [ -f "$(MKDOCS_CONFIG)" ]; then \
	  ${UVX_BIN} --with "mkdocs-material<10.0" --with "pymdown-extensions>=10.0" --with "mkdocs<2.0" mkdocs serve \
	    -f "$(MKDOCS_CONFIG)"; \
	else \
	  printf "${RED}[ERROR] $(MKDOCS_CONFIG) not found${RESET}\n"; \
	  exit 1; \
	fi

# Convenience alias
mkdocs: mkdocs-serve ## alias for mkdocs-serve
