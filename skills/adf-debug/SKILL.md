---
name: adf-debug
description: >-
  Parallel root-cause hypothesis testing and bug-hunt workflow (/adf-debug). Uses the debugger
  subagent to formulate 2-4 distinct root-cause hypotheses, investigates all hypotheses in
  parallel via run_workflow, and optionally applies and verifies the minimal root-cause fix.
  Use when the user invokes /adf-debug or needs to diagnose a non-trivial bug, regression,
  or failing test.
---

# `/adf-debug` — Parallel Hypothesis Bug-Hunt Workflow

Use this skill when diagnosing a bug, crash, race condition, or test failure where the root cause is not immediately obvious.

## Workflow Architecture

1. **Phase 1 — Symptom Analysis & Hypothesis Generation (`debugger`)**:
   - Inspects the failure symptom, stack trace, or reproduction command and generates 2–4 distinct, falsifiable hypotheses covering different potential root causes.
2. **Phase 2 — Parallel Hypothesis Investigation (`parallel` + `debugger`)**:
   - Dispatches one read-only `debugger` agent per hypothesis concurrently to gather code and runtime evidence supporting or refuting that hypothesis.
3. **Phase 3 — Root-Cause Verdict, Optional Fix & Verification (`implementer` + `verifier`)**:
   - Synthesizes the evidence to identify the proven root cause.
   - When `apply_fix: true` (default), dispatches `implementer` to apply the minimal fix + regression test, followed by `verifier` to confirm the fix passes.

## How to Run

Invoke `run_workflow` with `hypothesis_hunt.py`:

```python
run_workflow(
    # Resolve <skill_dir> to the directory containing this SKILL.md
    ScriptPath="<skill_dir>/scripts/hypothesis_hunt.py",
    Description="ADF Parallel Hypothesis Bug Hunt",
    Args={
        "symptom": "<Error message, failing test name, stack trace, or unexpected behavior>",
        "repro_command": "<Optional shell command to reproduce the failure>",
        "apply_fix": True
    }
)
```
