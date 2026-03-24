#!/usr/bin/env bash
# Run pytest with consistent flags for TDD reporting.
# Usage: ./run-tests.sh [filter]
# Examples:
#   ./run-tests.sh                    # all tests
#   ./run-tests.sh tests/unit/        # unit tests only
#   ./run-tests.sh -k "auth"          # tests matching "auth"

set -euo pipefail

# Find the backend directory
if [ -d "backend" ]; then
    cd backend
fi

# Activate venv if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run pytest with short traceback and verbose output
python -m pytest --tb=short -v "$@" 2>&1
