#!/bin/bash
set -euo pipefail

# Session End Hook
# Runs quality gates after the agent finishes work.

echo "[copilot-hook] Running post-work quality gates..."

# Format code
echo "[copilot-hook] Formatting code..."
if ! make fmt; then
    echo "[copilot-hook] [ERROR] Formatting check failed"
    echo "[copilot-hook] [INFO] Remediation: Review the formatting errors above"
    echo "[copilot-hook] [INFO] Common fixes:"
    echo "[copilot-hook]    - Run 'make fmt' locally to see detailed errors"
    echo "[copilot-hook]    - Check for syntax errors in modified files"
    echo "[copilot-hook]    - Ensure all files follow project style guidelines"
    exit 1
fi
echo "[copilot-hook] [OK] Code formatting passed"

# Run tests
echo "[copilot-hook] Running tests..."
if ! make test; then
    echo "[copilot-hook] [ERROR] Tests failed"
    echo "[copilot-hook] [INFO] Remediation: Review the test failures above"
    echo "[copilot-hook] [INFO] Common fixes:"
    echo "[copilot-hook]    - Run 'make test' locally to see detailed output"
    echo "[copilot-hook]    - Check if new code broke existing functionality"
    echo "[copilot-hook]    - Verify test assertions match expected behavior"
    echo "[copilot-hook]    - Review test logs in _tests/ directory"
    exit 1
fi
echo "[copilot-hook] [OK] Tests passed"

echo "[copilot-hook] [OK] All quality gates passed"
