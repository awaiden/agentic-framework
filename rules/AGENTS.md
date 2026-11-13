# Agentic Development Framework (ADF) — Global Orchestration Rules

You have access to the **Agentic Development Framework (`agentic-framework`)** plugin, which equips you with 6 specialized subagents (`architect`, `implementer`, `code-reviewer`, `security-auditor`, `debugger`, `verifier`) and 5 multi-agent orchestration skills (`/adf-build`, `/adf-parallel`, `/adf-review`, `/adf-debug`, `/adf-ship`).

Follow these routing and context-hygiene rules to maximize accuracy, speed, and context efficiency.

---

## 1. Execution Mode Decision Matrix

Before starting work on a coding, debugging, architectural, or review task, pick the lightest execution mode that matches the task's topology:

| Task Topology | Execution Mode | How to Execute |
| :--- | :--- | :--- |
| **Single-file or small change** (<30 lines, clear location, 1-2 files) | **Inline Direct** | Execute directly in the main conversation following `ponytail` simplicity rules. |
| **Single isolated role** (read-only codebase exploration, root-cause isolation of one failure, focused task implementation, or single-pass verification) | **Subagent (`invoke_subagent`)** | Dispatch one specialized subagent (`architect`, `debugger`, `implementer`, `code-reviewer`, `security-auditor`, or `verifier`) with a self-contained brief. |
| **Staged pipeline or parallel fan-out** (multi-step feature build with review gates, parallel module edits, multi-angle code review, or parallel bug hypothesis testing) | **Workflow (`run_workflow`)** | Run the matching `/adf-*` skill workflow script (`build_pipeline.py`, `parallel_fanout.py`, `multi_angle_review.py`, `hypothesis_hunt.py`, `ship_readiness.py`) or a custom `run_workflow` script. |
| **Open-ended collaborative team** (4+ long-running workers needing peer-to-peer handoffs and a live shared message board) | **Swarm (`swarm`)** | Activate the `swarm` skill and coordinate workers on the shared board. |

---

## 2. Specialized Subagent Roster

When calling `invoke_subagent(TypeName="<name>", Role="...", Prompt="...")` or `agent(type_name="<name>", ...)` inside `run_workflow`, select the specialized agent built for the job:

1. **`architect`** *(Read-only + inspection commands)*:
   - **Use for**: Deep codebase discovery, dependency mapping, schema/API design, and decomposing complex requests into atomic, ordered implementation plans and task briefs.
   - **Never use for**: Writing or editing source files.
2. **`implementer`** *(Full read/write/command tools)*:
   - **Use for**: Executing a single, well-scoped task brief using Test-Driven Development (write/update test -> confirm failure -> minimal implementation -> confirm pass).
   - **Workspace**: Use `Workspace="inherit"` for sequential tasks or strictly disjoint file sets; use `Workspace="share"` or `"branch"` when running concurrent implementers that build/test in parallel.
3. **`code-reviewer`** *(Read-only + git diff/log commands)*:
   - **Use for**: Auditing diffs and connected callers for spec compliance, logic bugs, concurrency hazards, missing edge cases, and YAGNI bloat.
4. **`security-auditor`** *(Read-only + security inspection)*:
   - **Use for**: Reviewing authentication/authorization boundaries, input validation, injection vectors (SQLi, command, XSS, SSRF), secrets handling, and dependency risks.
5. **`debugger`** *(Read-only + diagnostic/reproduction commands)*:
   - **Use for**: Reproducing test failures or runtime bugs, tracing data flow across call stacks, testing root-cause hypotheses, and specifying minimal root-cause fixes.
6. **`verifier`** *(Read-only + build/test/lint commands)*:
   - **Use for**: Running the project's build, typecheck, linter, and unit/integration test suites in an isolated context and returning a structured pass/fail report.

---

## 3. Subagent & Workflow Context Hygiene

1. **Self-Contained Briefs Only**:
   - Subagents and workflow agents start with a fresh context and cannot see your conversation history.
   - Every dispatch prompt MUST state:
     - **Objective & Scope**: Exact files or modules owned, and what must *not* be touched.
     - **Interfaces & Constraints**: Existing types, signatures, and architectural rules discovered so far.
     - **Definition of Done & Output Contract**: What verification commands must pass and what structured summary to return.
2. **Never Paste Session Transcripts**:
   - Pass file paths, git commit ranges (`BASE..HEAD`), or artifact paths rather than pasting huge code blocks or prior turn logs into subagent prompts.
3. **Evidence Before Completion**:
   - Never claim a bug is fixed or a feature works without fresh verification evidence (either from running the test/build command directly or dispatching `verifier`).
4. **Simplicity First (Ponytail Alignment)**:
   - Instruct `architect` and `implementer` to prefer the smallest complete change that reuses existing codebase patterns and standard library features over new abstractions or dependencies.
