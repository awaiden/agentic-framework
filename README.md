# Agentic Development Framework (`agentic-framework`)

A global multi-agent software engineering framework for the **Antigravity CLI (`agy`)**. It packages **6 specialized subagents**, **5 slash-command orchestration skills** backed by reusable `run_workflow` Python scripts, **always-on routing rules**, and a **`PreToolUse` command safety gate** into a single toggleable plugin.

Manage this plugin in Antigravity via `[agentic-framework](customization://agentic-framework)`.

---

## Installation

### Global (all workspaces)

```bash
git clone https://github.com/awaiden/agentic-framework.git ~/.gemini/config/plugins/agentic-framework
```

### Project-scoped (single workspace)

```bash
git clone https://github.com/awaiden/agentic-framework.git .agents/plugins/agentic-framework
```

Verify the plugin manifest and files:

```bash
agy plugin validate ~/.gemini/config/plugins/agentic-framework --strict
```

---

## 1. Subagent Roster (`agents/*.md`)

All 6 subagents can be invoked directly via `invoke_subagent(TypeName="<name>", ...)` or orchestrated in parallel/pipelines via `run_workflow`:

| Subagent `TypeName` | Access Level | Primary Responsibility |
| :--- | :--- | :--- |
| **`architect`** | Read-Only + Inspection | Explores the codebase, maps dependencies, evaluates trade-offs, and produces atomic implementation plans & task briefs. |
| **`implementer`** | Read + Write + Command | Executes scoped task briefs using TDD and minimal-diff (`ponytail`) engineering principles. |
| **`code-reviewer`** | Read-Only + Git Diff | Audits changes against the spec for logic errors, concurrency bugs, edge cases, and unnecessary complexity. |
| **`security-auditor`** | Read-Only + Security Scan | Audits trust boundaries, authz/authn, injection vectors, secrets exposure, and dependency risks. |
| **`debugger`** | Read-Only + Diagnostics | Reproduces failures, traces state/call stacks, tests root-cause hypotheses, and isolates minimal fixes. |
| **`verifier`** | Read-Only + Build/Test | Auto-detects project toolchains and runs build, typecheck, lint, and test suites to produce pass/fail evidence. |

---

## 2. Slash Commands & Orchestration Skills (`skills/*`)

Type any of the following slash commands in `agy` CLI (or ask naturally) to trigger the corresponding multi-agent workflow:

- **`/adf-build`** (`skills/adf-build/scripts/build_pipeline.py`)
  End-to-end feature development pipeline:
  `Architect (Plan & Task Briefs) -> Implementer (Staged Execution) -> Parallel Review (Code Reviewer + Security Auditor) -> Fix Loop (if needed) -> Verifier (Build/Typecheck/Test)`.
- **`/adf-parallel`** (`skills/adf-parallel/scripts/parallel_fanout.py`)
  Dynamic parallel fan-out across independent files, modules, or tasks using `parallel()` and isolated workspaces, followed by unified integration verification.
- **`/adf-review`** (`skills/adf-review/scripts/multi_angle_review.py`)
  Simultaneous 4-angle audit (`code-reviewer`, `security-auditor`, `architect`, `verifier`) that synthesizes and deduplicates findings by severity (`CRITICAL`, `IMPORTANT`, `MINOR`).
- **`/adf-debug`** (`skills/adf-debug/scripts/hypothesis_hunt.py`)
  Formulates 2–4 distinct root-cause hypotheses for a bug or failing test, investigates all hypotheses in parallel using `debugger` agents, and verifies the winning fix.
- **`/adf-ship`** (`skills/adf-ship/scripts/ship_readiness.py`)
  Pre-PR / pre-release gate that runs build/lint/test verification, security diff scanning, and regression checks in parallel, then generates a Go/No-Go checklist and PR summary.

---

## 3. Lifecycle Safety Gate (`hooks.json`)

The `adf-safety-gate` `PreToolUse` hook (`./scripts/safety-gate.sh`) inspects `run_command` executions and prompts for explicit confirmation (`"decision": "force_ask"`) before running high-risk destructive operations:
- Recursive deletion of root, `$HOME`, `~`, or `.git`
- Force-pushing (`--force` / `-f`) to `main` or `master`
- Destructive working-tree resets (`git reset --hard`, `git clean -fdx`)
- Database drops (`DROP DATABASE`, `DROP TABLE`) or disk formatting (`mkfs`, `dd if=`)
