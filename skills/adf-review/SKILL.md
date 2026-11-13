---
name: adf-review
description: >-
  Multi-angle parallel code, security, architecture, and verification audit (/adf-review).
  Dispatches code-reviewer, security-auditor, architect, and verifier concurrently via
  run_workflow, then deduplicates and ranks findings by severity (CRITICAL, IMPORTANT, MINOR).
  Use when the user invokes /adf-review or asks for a comprehensive multi-agent review.
---

# `/adf-review` — Multi-Angle Parallel Review Workflow

Use this skill to run a simultaneous 4-angle audit across uncommitted changes, a branch diff, or specific files/modules:

1. **Correctness & Edge Cases (`code-reviewer`)**: Logic flaws, concurrency hazards, error handling, and spec compliance.
2. **Security & Trust Boundaries (`security-auditor`)**: Authz/authn gaps, injection vectors, SSRF, secrets, and data exposure.
3. **Architecture & Simplicity (`architect`)**: Coupling, boundary violations, dead code, and YAGNI / Ponytail bloat.
4. **Build & Test Health (`verifier`)**: Typecheck, lint, test execution, and missing test coverage for risky branches.

## How to Run

Invoke `run_workflow` with `multi_angle_review.py`:

```python
run_workflow(
    # Resolve <skill_dir> to the directory containing this SKILL.md
    ScriptPath="<skill_dir>/scripts/multi_angle_review.py",
    Description="ADF 4-Angle Parallel Audit (Code, Security, Architecture, Verification)",
    Args={
        "scope": "git diff HEAD (or specific files/directories/branch range)",
        "context": "Optional summary of what the change is supposed to accomplish"
    }
)
```

After the workflow finishes, present the deduplicated findings grouped by severity (`CRITICAL`, `IMPORTANT`, `MINOR`) with clickable `file://` links and offer to dispatch `implementer` to fix any flagged items.
