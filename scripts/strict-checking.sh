#!/usr/bin/env bash
set -euo pipefail

TARGET_CONFIG="pyproject.toml"
SRC_DIR="src"
TESTS_DIR="tests"

echo "Checking pipeline security bounds..."

# 1. Enforce no per-file-ignore blocks exist in the config file
if grep -q "per-file-ignores" "$TARGET_CONFIG"; then
  echo "Error: 'per-file-ignores' block detected in $TARGET_CONFIG. Overrides are forbidden." >&2
  exit 1
fi

# 2. Scan source trees for inline linting escapes
# This catches # noqa, # type: ignore, and pylint/eslint suppressions
VIOLATING_LINES=$(grep -rnE "(#\s*noqa|#\s*type:\s*ignore|#\s*pylint:\s*disable)" "$SRC_DIR" "$TESTS_DIR" || true)

if [[ -n "$VIOLATING_LINES" ]]; then
  echo "Error: Inline suppression markers detected. Code modification rejected." >&2
  echo "$VIOLATING_LINES" >&2
  echo "Resolution: Fix the fundamental type definition or architectural layer instead of suppressing." >&2
  exit 1
fi

echo "Pipeline validation passed. Proceeding to linter execution..."
exit 0
