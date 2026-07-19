#!/usr/bin/env bash
set -euo pipefail

ln -sf ../../scripts/pre-commit .git/hooks/pre-commit
chmod +x scripts/pre-commit
echo "pre-commit hook installed"
