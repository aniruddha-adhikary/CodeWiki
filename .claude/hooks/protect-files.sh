#!/usr/bin/env bash
# PreToolUse hook: block edits to sensitive files
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Nothing to check if no file_path
[ -z "$file_path" ] && exit 0

basename=$(basename "$file_path")
# Normalize to relative path for pattern matching
rel_path="${file_path#"$CLAUDE_PROJECT_DIR"/}"

# Protected patterns
case "$basename" in
  .env|.env.*|credentials*|secrets*|*.key|*.pem)
    echo "Blocked: '$rel_path' is a protected sensitive file." >&2
    exit 2
    ;;
esac

case "$rel_path" in
  *keyring*|.claude/settings.json|.claude/settings.local.json)
    echo "Blocked: '$rel_path' is a protected file." >&2
    exit 2
    ;;
esac

exit 0
