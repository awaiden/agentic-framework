#!/usr/bin/env bash
# ADF PreToolUse Safety Gate for run_command
# Reads AGY PreToolUse JSON payload from stdin and outputs JSON decision on stdout.

set -euo pipefail

python3 -c '
import json
import re
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

tool_call = payload.get("toolCall") or {}
args = tool_call.get("args") or {}
cmd = str(args.get("CommandLine") or "").strip()

if not cmd:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

RULES = [
    (
        r"(^|[;&|]\s*)rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\b.*--force\b|--force\b.*--recursive\b)\s+(/\*?(\s|$)|--no-preserve-root\b|~(/|\s|$)|\"?\$HOME\"?(/|\s|$)|\"?\$\{HOME\}\"?(/|\s|$)|\.git(\s|/|$))",
        "Destructive recursive deletion targeting /, ~, $HOME, or .git detected.",
    ),
    (
        r"git\s+push\s+.*(--force(?!=|-with-lease)|-f\b).*\b(main|master)\b",
        "Force-pushing to main/master branch can overwrite shared history.",
    ),
    (
        r"git\s+push\s+.*(--delete\b.*\b(main|master)\b|:(main|master)\b)",
        "Deleting remote main/master branch can disrupt shared history.",
    ),
    (
        r"git\s+reset\s+--hard\b",
        "git reset --hard permanently discards uncommitted working-tree changes.",
    ),
    (
        r"git\s+clean\s+-[a-zA-Z]*f[a-zA-Z]*d",
        "git clean -fd permanently deletes untracked files and directories.",
    ),
    (
        r"\b(DROP\s+DATABASE|DROP\s+TABLE|TRUNCATE\s+TABLE)\b",
        "Destructive SQL schema/data drop detected.",
    ),
    (
        r"(^|[;&|]\s*)(mkfs(\.[a-z0-9]+)?|dd\s+if=.*of=/dev/)",
        "Low-level disk formatting or block device overwrite detected.",
    ),
    (
        r"(^|[;&|]\s*)(chmod|chown)\s+(-[a-zA-Z]*R[a-zA-Z]*|--recursive)\s+.*\s+/(\s|$)",
        "Recursive permission/ownership change on root (/) detected.",
    ),
    (
        r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba)?sh\b",
        "Piping remote script directly into a shell detected.",
    ),
]

for pattern, reason in RULES:
    if re.search(pattern, cmd, re.IGNORECASE):
        print(json.dumps({
            "decision": "force_ask",
            "reason": f"[ADF Safety Gate] {reason} Command: {cmd[:120]}"
        }))
        sys.exit(0)

print(json.dumps({"decision": "allow"}))
'
