#!/usr/bin/env bash
# PostToolUse hook: auto-lint Python files with Ruff (runs sync, can block)
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Skip if no file_path or not a Python file
[ -z "$file_path" ] && exit 0
[[ "$file_path" != *.py ]] && exit 0

# Skip if file doesn't exist
[ -f "$file_path" ] || exit 0

# First pass: auto-fix what we can
ruff check --fix --quiet "$file_path" 2>/dev/null || true

# Second pass: check for remaining issues
lint_output=$(ruff check "$file_path" 2>&1) || true

if [ -n "$lint_output" ]; then
  echo '{"decision": "block", "reason": "Ruff lint errors remain after auto-fix:\n'"$(echo "$lint_output" | jq -Rs .)"'"}'
  exit 0
fi

exit 0
