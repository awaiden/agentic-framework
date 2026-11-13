---
name: adf-build
description: >-
  End-to-end multi-agent feature build pipeline (/adf-build). Orchestrates the architect,
  implementer, code-reviewer, security-auditor, and verifier subagents via run_workflow to
  plan, implement with TDD, audit, auto-remediate findings, and verify a feature or change.
  Use when the user invokes /adf-build or asks to build a multi-step feature end-to-end.
---

# `/adf-build` — End-to-End Multi-Agent Build Pipeline

Use this skill to execute a complete, quality-gated feature build using the Agentic Development Framework's specialized subagents (`architect`, `implementer`, `code-reviewer`, `security-auditor`, `verifier`).

## Workflow Architecture

1. **Phase 1 — Architecture & Task Decomposition (`architect`)**:
   - Explores the workspace, identifies reusable patterns, and decomposes the user's goal into ordered, atomic task briefs with explicit file ownership and verification commands.
2. **Phase 2 — Staged TDD Implementation & Dual Review Gate (`implementer` + `code-reviewer` + `security-auditor`)**:
   - Executes each task brief via `implementer`.
   - Runs `code-reviewer` and `security-auditor` in parallel on each completed task.
   - Automatically runs a targeted remediation pass with `implementer` if blocking (`CRITICAL` / `IMPORTANT`) review findings are reported.
3. **Phase 3 — Final Workspace Verification (`verifier`)**:
   - Runs project build, typecheck, lint, and test suites and returns a complete readiness report.

## How to Run

Invoke `run_workflow` pointing at the bundled `build_pipeline.py` script:

```python
run_workflow(
    # Resolve <skill_dir> to the directory containing this SKILL.md
    ScriptPath="<skill_dir>/scripts/build_pipeline.py",
    Description="ADF End-to-End Feature Build Pipeline",
    Args={
        "goal": "<Full description of the feature or change requested by the user>",
        "constraints": "<Optional architectural constraints, target files, or test commands>",
        "max_fix_rounds": 2
    }
)
```

## Fallback (Single-Task Mode)

If the request touches only 1–2 files and the architecture is already clear:
1. Dispatch `invoke_subagent(TypeName="implementer", Role="Feature Implementer", Prompt="...")`.
2. Dispatch `invoke_subagent(TypeName="code-reviewer", ...)` and `invoke_subagent(TypeName="verifier", ...)` in parallel to verify the implementation.
