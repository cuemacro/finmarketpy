## Makefile.tests - Testing and benchmarking targets
# This file is included by the main Makefile.
# It provides targets for running the test suite with coverage and
# executing performance benchmarks.

# Declare phony targets (they don't produce files)
.PHONY: test benchmark typecheck security docs-coverage hypothesis-test coverage-badge stress

# Default directory for tests
TESTS_FOLDER := tests

# Minimum coverage percent for tests to pass
# (Can be overridden in local.mk or via environment variable)
COVERAGE_FAIL_UNDER ?= 90

##@ Development and Testing

# The 'test' target runs the complete test suite.
# 1. Cleans up any previous test results in _tests/.
# 2. Creates directories for HTML coverage and test reports.
# 3. Invokes pytest via the local virtual environment.
# 4. Generates terminal output, HTML coverage, JSON coverage, and HTML test reports.
test:: install ## run all tests
	@rm -rf _tests;

	if [ -z "$$(find ${TESTS_FOLDER} -name 'test_*.py' -o -name '*_test.py' 2>/dev/null)" ]; then \
	  printf "${YELLOW}[WARN] No test files found in ${TESTS_FOLDER}, skipping tests.${RESET}\n"; \
	  exit 0; \
	fi; \
	mkdir -p _tests/html-coverage _tests/html-report; \
	if [ -d ${SOURCE_FOLDER} ]; then \
	  ${UV_BIN} run pytest \
	  --ignore=${TESTS_FOLDER}/benchmarks \
	  --ignore=${TESTS_FOLDER}/stress \
	  --cov=${SOURCE_FOLDER} \
	  --cov-report=term \
	  --cov-report=html:_tests/html-coverage \
	  --cov-fail-under=$(COVERAGE_FAIL_UNDER) \
	  --cov-report=json:_tests/coverage.json \
	  --cov-report=xml:_tests/coverage.xml \
	  --html=_tests/html-report/report.html; \
	else \
	  printf "${YELLOW}[WARN] Source folder ${SOURCE_FOLDER} not found, running tests without coverage${RESET}\n"; \
	  ${UV_BIN} run pytest \
	  --ignore=${TESTS_FOLDER}/benchmarks \
	  --ignore=${TESTS_FOLDER}/stress \
	  --html=_tests/html-report/report.html; \
	fi

# The 'typecheck' target runs static type analysis using ty.
# 1. Checks if the source directory exists.
# 2. Runs ty on the source folder.
typecheck: install ## run ty type checking
	@if [ -d ${SOURCE_FOLDER} ]; then \
	  printf "${BLUE}[INFO] Running ty type checking...${RESET}\n"; \
	  ${UV_BIN} run ty check ${SOURCE_FOLDER}; \
	else \
	  printf "${YELLOW}[WARN] Source folder ${SOURCE_FOLDER} not found, skipping typecheck${RESET}\n"; \
	fi

# The 'security' target performs security vulnerability scans.
# 1. Runs pip-audit to check for known vulnerabilities in dependencies.
# 2. Runs bandit to find common security issues in the source code.
security: install ## run security scans (pip-audit and bandit)
	@printf "${BLUE}[INFO] Running pip-audit for dependency vulnerabilities...${RESET}\n"
	@${UVX_BIN} pip-audit
	@printf "${BLUE}[INFO] Running bandit security scan...${RESET}\n"
	@${UVX_BIN} bandit -r ${SOURCE_FOLDER} -ll -q -c pyproject.toml

# The 'benchmark' target runs performance benchmarks using pytest-benchmark.
# 1. Installs benchmarking dependencies (pytest-benchmark, pygal).
# 2. Executes benchmarks found in the benchmarks/ subfolder.
# 3. Generates histograms and JSON results.
# 4. Runs a post-analysis script to process the results.
benchmark:: install ## run performance benchmarks
	@if [ -d "${TESTS_FOLDER}/benchmarks" ]; then \
	  printf "${BLUE}[INFO] Running performance benchmarks...${RESET}\n"; \
	  ${UV_BIN} pip install pytest-benchmark==5.2.3 pygal==3.1.0; \
	  mkdir -p _tests/benchmarks; \
	  ${UV_BIN} run pytest "${TESTS_FOLDER}/benchmarks/" \
	  		--benchmark-only \
			--benchmark-histogram=_tests/benchmarks/histogram \
			--benchmark-json=_tests/benchmarks/results.json; \
	  ${UVX_BIN} "rhiza-tools>=0.2.3" analyze-benchmarks --benchmarks-json _tests/benchmarks/results.json --output-html _tests/benchmarks/report.html; \
	else \
	  printf "${YELLOW}[WARN] Benchmarks folder not found, skipping benchmarks${RESET}\n"; \
	fi

# The 'docs-coverage' target checks documentation coverage using interrogate.
# 1. Checks if SOURCE_FOLDER exists.
# 2. Runs interrogate on the source folder with verbose output.
docs-coverage: install ## check documentation coverage with interrogate
	@if [ -d "${SOURCE_FOLDER}" ]; then \
	  printf "${BLUE}[INFO] Checking documentation coverage in ${SOURCE_FOLDER}...${RESET}\n"; \
	  ${UV_BIN} run interrogate -vv ${SOURCE_FOLDER}; \
	else \
	  printf "${YELLOW}[WARN] Source folder ${SOURCE_FOLDER} not found, skipping docs-coverage${RESET}\n"; \
	fi

# The 'hypothesis-test' target runs property-based tests using Hypothesis.
# 1. Checks if hypothesis tests exist in the tests directory.
# 2. Runs pytest with hypothesis-specific settings and statistics.
# 3. Generates detailed hypothesis examples and statistics.
hypothesis-test:: install ## run property-based tests with Hypothesis
	@if [ -z "$$(find ${TESTS_FOLDER} -name 'test_*.py' -o -name '*_test.py' 2>/dev/null)" ]; then \
	  printf "${YELLOW}[WARN] No test files found in ${TESTS_FOLDER}, skipping hypothesis tests.${RESET}\n"; \
	  exit 0; \
	fi; \
	printf "${BLUE}[INFO] Running Hypothesis property-based tests...${RESET}\n"; \
	mkdir -p _tests/hypothesis; \
	PYTEST_HTML_TITLE="Hypothesis tests" ${UV_BIN} run pytest \
	  --ignore=${TESTS_FOLDER}/benchmarks \
	  -v \
	  --hypothesis-show-statistics \
	  --hypothesis-seed=0 \
	  -m "hypothesis or property" \
	  --tb=short \
	  --html=_tests/hypothesis/report.html; \
	exit_code=$$?; \
	if [ $$exit_code -eq 5 ]; then \
	  printf "${YELLOW}[WARN] No hypothesis/property tests collected, skipping.${RESET}\n"; \
	  exit 0; \
	fi; \
	exit $$exit_code

# The 'coverage-badge' target generates an SVG coverage badge and pushes it to gh-pages.
# 1. Checks if SOURCE_FOLDER exists; skips if not (no source means no coverage).
# 2. Checks if the coverage JSON file exists.
# 3. Runs genbadge via uvx to produce the SVG badge in /tmp.
# 4. Checks out (or creates) the gh-pages branch and commits the badge there.
# 5. Returns to the original branch.
coverage-badge: test ## generate coverage badge and push to gh-pages branch
	@if [ ! -d "${SOURCE_FOLDER}" ]; then \
	  printf "${YELLOW}[WARN] Source folder ${SOURCE_FOLDER} not found, skipping coverage-badge${RESET}\n"; \
	  exit 0; \
	fi; \
	if [ ! -f _tests/coverage.json ]; then \
	  printf "${RED}[ERROR] Coverage report not found at _tests/coverage.json, run 'make test' first.${RESET}\n"; \
	  exit 1; \
	fi; \
	printf "${BLUE}[INFO] Generating coverage badge...${RESET}\n"; \
	${UVX_BIN} genbadge coverage -i _tests/coverage.json -o /tmp/coverage-badge.svg; \
	if [ ! -f /tmp/coverage-badge.svg ]; then \
	  printf "${RED}[ERROR] Badge generation failed.${RESET}\n"; \
	  exit 1; \
	fi; \
	ORIGINAL_BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	printf "${BLUE}[INFO] Pushing coverage badge to gh-pages...${RESET}\n"; \
	if git fetch origin gh-pages 2>/dev/null; then \
	  git checkout gh-pages; \
	else \
	  git checkout --orphan gh-pages; \
	  git rm -rf .; \
	fi; \
	cp /tmp/coverage-badge.svg coverage-badge.svg; \
	git add coverage-badge.svg; \
	if ! git diff --staged --quiet; then \
	  git commit -m "chore: update coverage badge [skip ci]"; \
	  git push origin gh-pages; \
	else \
	  printf "${YELLOW}[INFO] Coverage badge unchanged, skipping push${RESET}\n"; \
	fi; \
	git checkout "$$ORIGINAL_BRANCH"; \
	printf "${GREEN}[SUCCESS] Coverage badge pushed to gh-pages${RESET}\n"

# The 'stress' target runs stress/load tests.
# 1. Checks if stress tests exist in the tests/stress directory.
# 2. Runs pytest with the stress marker to execute only stress tests.
# 3. Generates an HTML report of stress test results.
stress:: install ## run stress/load tests
	@if [ ! -d "${TESTS_FOLDER}/stress" ]; then \
	  printf "${YELLOW}[WARN] Stress tests folder not found, skipping stress tests.${RESET}\n"; \
	  exit 0; \
	fi; \
	printf "${BLUE}[INFO] Running stress/load tests...${RESET}\n"; \
	mkdir -p _tests/stress; \
	${UV_BIN} run pytest \
	  -v \
	  -m stress \
	  --tb=short \
	  --html=_tests/stress/report.html
