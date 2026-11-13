---
name: adf-ship
description: >-
  Pre-PR and release readiness verification workflow (/adf-ship). Runs verifier, security-auditor,
  and code-reviewer in parallel via run_workflow to validate build/lint/test health, check for
  leaked secrets or vulnerabilities in the diff, and produce a Go/No-Go checklist, conventional
  commit message, and PR description. Use when the user invokes /adf-ship or asks to prepare
  changes for commit, PR, or deployment.
---

# `/adf-ship` — Pre-Ship Verification & Release Readiness Workflow

Use this skill before committing, merging, or opening a pull request to ensure zero regressions, passing builds/tests, clean security posture, and a ready-to-use commit/PR summary.

## Workflow Architecture

1. **Phase 1 — Parallel Pre-Flight Gates (`verifier` + `security-auditor` + `code-reviewer`)**:
   - **`verifier`**: Runs full build, typecheck, linter, and test suites.
   - **`security-auditor`**: Scans the git diff and untracked files for hardcoded secrets, debug artifacts, or security regressions.
   - **`code-reviewer`**: Checks the diff for leftover `TODO`/`console.log`/debug code, broken exports, or missing migration steps, and drafts the Conventional Commit & PR summary.
2. **Phase 2 — Go / No-Go Release Matrix**:
   - Synthesizes all three gates into a clear `GO` or `NO_GO` decision with exact blockers (if any) and ready-to-copy commit/PR text.

## How to Run

Invoke `run_workflow` with `ship_readiness.py`:

```python
run_workflow(
    # Resolve <skill_dir> to the directory containing this SKILL.md
    ScriptPath="<skill_dir>/scripts/ship_readiness.py",
    Description="ADF Pre-Ship Readiness & Verification Gate",
    Args={
        "base_ref": "HEAD"  # or e.g. "origin/main" for branch-wide PR readiness
    }
)
```
