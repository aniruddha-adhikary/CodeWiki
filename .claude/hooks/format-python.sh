#!/usr/bin/env bash
# PostToolUse hook: auto-format Python files with Black (runs async)
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Skip if no file_path or not a Python file
[ -z "$file_path" ] && exit 0
[[ "$file_path" != *.py ]] && exit 0

# Skip if file doesn't exist (e.g. was deleted)
[ -f "$file_path" ] || exit 0

black --line-length 100 --quiet "$file_path" 2>/dev/null || true

exit 0
