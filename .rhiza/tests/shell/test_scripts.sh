#!/bin/bash
# Shell script test suite
# Tests shell scripts in the repository for correctness and error handling
#
# Usage: ./test_scripts.sh [--verbose]
#   --verbose: Show detailed output for each test

set -euo pipefail

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VERBOSE=false
if [ "${1:-}" = "--verbose" ]; then
    VERBOSE=true
fi

# Test helper functions
assert_equal() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ "$expected" = "$actual" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        if [ "$VERBOSE" = true ]; then
            echo -e "${GREEN}✓${NC} PASS: $test_name"
        fi
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} FAIL: $test_name"
        echo "  Expected: $expected"
        echo "  Got: $actual"
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local test_name="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if grep -q "$needle" <<< "$haystack"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        if [ "$VERBOSE" = true ]; then
            echo -e "${GREEN}✓${NC} PASS: $test_name"
        fi
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} FAIL: $test_name"
        echo "  Expected to find: $needle"
        echo "  In output: $haystack"
    fi
}

assert_exit_code() {
    local expected_code="$1"
    local actual_code="$2"
    local test_name="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ "$expected_code" -eq "$actual_code" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        if [ "$VERBOSE" = true ]; then
            echo -e "${GREEN}✓${NC} PASS: $test_name"
        fi
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} FAIL: $test_name"
        echo "  Expected exit code: $expected_code"
        echo "  Got exit code: $actual_code"
    fi
}

# Find repository root (script is in .rhiza/tests/shell/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo -e "${BLUE}=== Shell Script Test Suite ===${NC}"
echo "Repository: $REPO_ROOT"
echo ""

# ============================================================================
# Test Suite: session-start.sh
# ============================================================================
echo -e "${YELLOW}Testing: session-start.sh${NC}"

# Test 1: Script has proper shebang
first_line=$(head -n 1 "$REPO_ROOT/.github/hooks/session-start.sh")
assert_equal "#!/bin/bash" "$first_line" "session-start.sh has bash shebang"

# Test 2: Script uses strict mode
if grep -q "set -euo pipefail" "$REPO_ROOT/.github/hooks/session-start.sh"; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}✓${NC} PASS: session-start.sh uses strict error handling"
    fi
else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} FAIL: session-start.sh missing 'set -euo pipefail'"
fi

# Test 3: Normal mode with valid environment
if [ -d "$REPO_ROOT/.venv" ] && command -v uv >/dev/null 2>&1; then
    output=$(bash "$REPO_ROOT/.github/hooks/session-start.sh" 2>&1) || true
    assert_contains "$output" "Validating environment" "session-start.sh normal mode runs validation"
fi

# ============================================================================
# Test Suite: session-end.sh
# ============================================================================
echo -e "${YELLOW}Testing: session-end.sh${NC}"

# Test 4: Script has proper shebang
first_line=$(head -n 1 "$REPO_ROOT/.github/hooks/session-end.sh")
assert_equal "#!/bin/bash" "$first_line" "session-end.sh has bash shebang"

# Test 5: Script uses strict mode
if grep -q "set -euo pipefail" "$REPO_ROOT/.github/hooks/session-end.sh"; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}✓${NC} PASS: session-end.sh uses strict error handling"
    fi
else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} FAIL: session-end.sh missing 'set -euo pipefail'"
fi

# ============================================================================
# Test Suite: bootstrap.sh
# ============================================================================
echo -e "${YELLOW}Testing: bootstrap.sh${NC}"

# Test 6: Script has proper shebang
first_line=$(head -n 1 "$REPO_ROOT/.devcontainer/bootstrap.sh")
assert_equal "#!/bin/bash" "$first_line" "bootstrap.sh has bash shebang"

# Test 7: Script uses strict mode
if grep -q "set -euo pipefail" "$REPO_ROOT/.devcontainer/bootstrap.sh"; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}✓${NC} PASS: bootstrap.sh uses strict error handling"
    fi
else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} FAIL: bootstrap.sh missing 'set -euo pipefail'"
fi

# Test 8: Script has error handler function
if grep -q "error_with_recovery" "$REPO_ROOT/.devcontainer/bootstrap.sh"; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}✓${NC} PASS: bootstrap.sh has error_with_recovery function"
    fi
else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} FAIL: bootstrap.sh missing error_with_recovery function"
fi

# Test 9: Script includes remediation messages
if grep -q "Remediation\|Suggested fix" "$REPO_ROOT/.devcontainer/bootstrap.sh"; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}✓${NC} PASS: bootstrap.sh includes remediation messages"
    fi
else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} FAIL: bootstrap.sh missing remediation messages"
fi

# Test 10: Script handles .python-version file
if grep -q ".python-version" "$REPO_ROOT/.devcontainer/bootstrap.sh"; then
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    if [ "$VERBOSE" = true ]; then
        echo -e "${GREEN}✓${NC} PASS: bootstrap.sh checks for .python-version"
    fi
else
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} FAIL: bootstrap.sh doesn't check .python-version"
fi

# ============================================================================
# Test Suite: Shell script syntax validation
# ============================================================================
echo -e "${YELLOW}Testing: Syntax validation${NC}"

# Test 11-13: Validate syntax of all shell scripts
for script in \
    "$REPO_ROOT/.devcontainer/bootstrap.sh" \
    "$REPO_ROOT/.github/hooks/session-start.sh" \
    "$REPO_ROOT/.github/hooks/session-end.sh"
do
    script_name=$(basename "$script")
    if bash -n "$script" 2>/dev/null; then
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
        if [ "$VERBOSE" = true ]; then
            echo -e "${GREEN}✓${NC} PASS: $script_name has valid bash syntax"
        fi
    else
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} FAIL: $script_name has syntax errors"
    fi
done

# ============================================================================
# Test Summary
# ============================================================================
echo ""
echo -e "${BLUE}=== Test Summary ===${NC}"
echo "Tests run: $TESTS_RUN"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
