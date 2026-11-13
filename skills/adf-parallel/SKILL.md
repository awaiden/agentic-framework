---
name: adf-parallel
description: >-
  Dynamic parallel multi-agent execution workflow (/adf-parallel). Partitions work into
  independent, non-colliding slices and fans out concurrent implementer subagents via
  run_workflow parallel(), followed by unified verification and code review. Use when the
  user invokes /adf-parallel or wants multiple independent modules, files, or tasks built
  or refactored concurrently.
---

# `/adf-parallel` — Parallel Multi-Agent Fan-Out Workflow

Use this skill when a task splits into **2 or more independent units of work** (e.g., migrating multiple components, fixing independent test suites, implementing separate modules or endpoints) with **disjoint file ownership**.

## Workflow Architecture

1. **Phase 1 — Partition & Ownership Check (`architect`)**:
   - If explicit `tasks` are not already provided in `Args`, `architect` inspects the workspace and partitions the work into strictly disjoint slices (`files_owned` per slice must not overlap).
2. **Phase 2 — Concurrent Execution (`parallel` + `implementer`)**:
   - Fans out one `implementer` agent per slice concurrently.
   - Uses `workspace="inherit"` when slices touch completely disjoint files in the same working tree, or `workspace="share"` when requested via `Args["workspace_mode"]`.
3. **Phase 3 — Unified Verification & Integration Audit (`verifier` + `code-reviewer`)**:
   - Runs `verifier` and `code-reviewer` in parallel across the combined changes to confirm zero integration conflicts and passing tests.

## How to Run

Invoke `run_workflow` with `parallel_fanout.py`:

```python
run_workflow(
    # Resolve <skill_dir> to the directory containing this SKILL.md
    ScriptPath="<skill_dir>/scripts/parallel_fanout.py",
    Description="ADF Parallel Multi-Agent Fan-Out",
    Args={
        "goal": "<Overall objective of the parallel work>",
        "workspace_mode": "inherit",  # "inherit" (disjoint files) or "share"
        "tasks": [
            # Optional explicit slices; if omitted, architect partitions automatically
            {
                "title": "Slice 1 title",
                "files_owned": ["src/module_a.ts"],
                "requirements": "Exact instructions for Slice 1"
            }
        ]
    }
)
```
