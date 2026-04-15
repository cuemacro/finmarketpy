## book.mk - Book-building targets (MkDocs-based)

.PHONY: book mkdocs-build test benchmark stress hypothesis-test _book-reports _book-notebooks mkdocs-serve mkdocs

# No-op stubs — overridden by test.mk / bench.mk when present
test:: ; @:
benchmark:: ; @:
stress:: ; @:
hypothesis-test:: ; @:

BOOK_OUTPUT ?= _book

# Additional uvx --with packages to inject into mkdocs build and serve.
# Projects can extend the package list without editing this template, e.g.:
#   MKDOCS_EXTRA_PACKAGES = --with "mkdocs-graphviz"
MKDOCS_EXTRA_PACKAGES ?=

# Detect mkdocs config: prefer root-level, fall back to docs/mkdocs-base.yml
_MKDOCS_CFG := $(if $(wildcard mkdocs.yml),mkdocs.yml,$(if $(wildcard docs/mkdocs-base.yml),docs/mkdocs-base.yml,))

##@ Book

_book-reports: test benchmark stress hypothesis-test
	@mkdir -p docs/reports
	@for src_dir in \
	  "_tests/html-coverage:reports/coverage" \
	  "_tests/html-report:reports/test-report" \
	  "_tests/benchmarks:reports/benchmarks" \
	  "_tests/stress:reports/stress" \
	  "_tests/hypothesis:reports/hypothesis"; do \
	  src=$${src_dir%%:*}; dest=docs/$${src_dir#*:}; \
	  if [ -d "$$src" ] && [ -n "$$(ls -A "$$src" 2>/dev/null)" ]; then \
	    printf "${BLUE}[INFO] Copying $$src -> $$dest${RESET}\n"; \
	    mkdir -p "$$dest"; cp -r "$$src/." "$$dest/"; \
	  else \
	    printf "${YELLOW}[WARN] $$src not found, skipping${RESET}\n"; \
	  fi; \
	done
	@printf "# Reports\n\n" > docs/reports.md
	@[ -f "docs/reports/test-report/report.html" ] && echo "- [Test Report](reports/test-report/report.html)"       >> docs/reports.md || true
	@[ -f "docs/reports/hypothesis/report.html" ]  && echo "- [Hypothesis Report](reports/hypothesis/report.html)" >> docs/reports.md || true
	@[ -f "docs/reports/benchmarks/report.html" ]  && echo "- [Benchmarks](reports/benchmarks/report.html)"        >> docs/reports.md || true
	@[ -f "docs/reports/stress/report.html" ]      && echo "- [Stress Report](reports/stress/report.html)"          >> docs/reports.md || true
	@[ -f "docs/reports/coverage/index.html" ]     && echo "- [Coverage Report](reports/coverage/index.html)"      >> docs/reports.md || true

_book-notebooks:
	@if [ -d "$(MARIMO_FOLDER)" ]; then \
	  for nb in $(MARIMO_FOLDER)/*.py; do \
	    name=$$(basename "$$nb" .py); \
	    printf "${BLUE}[INFO] Exporting $$nb${RESET}\n"; \
	    abs_output="$$(pwd)/docs/notebooks/$$name.html"; \
	    mkdir -p docs/notebooks; \
	    (cd "$$(dirname "$$nb")" && ${UV_BIN} run marimo export html --sandbox "$$(basename "$$nb")" -o "$$abs_output"); \
	  done; \
	  printf "# Marimo Notebooks\n\n" > docs/notebooks.md; \
	  for html in docs/notebooks/*.html; do \
	    name=$$(basename "$$html" .html); \
	    echo "- [$$name]($$name.html)" >> docs/notebooks.md; \
	  done; \
	fi

book:: _book-reports _book-notebooks ## compile the companion book via MkDocs
	@if [ -n "$(_MKDOCS_CFG)" ]; then \
	  rm -rf "$(BOOK_OUTPUT)"; \
	  ${UVX_BIN} --with "mkdocs-material<10.0" --with "pymdown-extensions>=10.0" --with "mkdocs<2.0" $(MKDOCS_EXTRA_PACKAGES) mkdocs build \
	    -f "$(_MKDOCS_CFG)" \
	    -d "$$(pwd)/$(BOOK_OUTPUT)"; \
	else \
	  printf "${YELLOW}[WARN] No mkdocs config found, skipping MkDocs build${RESET}\n"; \
	fi
	@mkdir -p "$(BOOK_OUTPUT)"
	@touch "$(BOOK_OUTPUT)/.nojekyll"
	@printf "${GREEN}[SUCCESS] Book built at $(BOOK_OUTPUT)/${RESET}\n"
	@tree $(BOOK_OUTPUT)

mkdocs-build: install-uv ## build MkDocs documentation site
	@if [ -n "$(_MKDOCS_CFG)" ]; then \
	  rm -rf "$(BOOK_OUTPUT)"; \
	  ${UVX_BIN} --with "mkdocs-material<10.0" --with "pymdown-extensions>=10.0" --with "mkdocs<2.0" $(MKDOCS_EXTRA_PACKAGES) mkdocs build \
	    -f "$(_MKDOCS_CFG)" \
	    -d "$$(pwd)/$(BOOK_OUTPUT)"; \
	else \
	  printf "${RED}[ERROR] No mkdocs config found${RESET}\n"; \
	  exit 1; \
	fi
	@mkdir -p "$(BOOK_OUTPUT)"
	@touch "$(BOOK_OUTPUT)/.nojekyll"
	@printf "${GREEN}[SUCCESS] Docs built at $(BOOK_OUTPUT)/${RESET}\n"

mkdocs-serve: install-uv ## serve MkDocs site with live reload
	@if [ -n "$(_MKDOCS_CFG)" ]; then \
	  ${UVX_BIN} --with "mkdocs-material<10.0" --with "pymdown-extensions>=10.0" --with "mkdocs<2.0" $(MKDOCS_EXTRA_PACKAGES) mkdocs serve \
	    -f "$(_MKDOCS_CFG)"; \
	else \
	  printf "${RED}[ERROR] No mkdocs config found${RESET}\n"; \
	  exit 1; \
	fi

mkdocs: mkdocs-serve ## alias for mkdocs-serve
