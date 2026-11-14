# ADF End-to-End Feature Build Pipeline (run_workflow script)
# Orchestrates: architect -> staged implementer -> parallel (code-reviewer + security-auditor) -> verifier

wf_args = globals().get("args") or {}
goal = str(wf_args.get("goal") or "").strip()
constraints = str(wf_args.get("constraints") or "Follow existing project conventions and Ponytail minimal-diff principles.").strip()
max_fix_rounds = max(0, int(wf_args.get("max_fix_rounds", 2)))

if not goal:
    raise ValueError("Missing required 'goal' in Args for build_pipeline.py")

PLAN_SCHEMA = {
    "type": "object",
    "required": ["summary", "global_constraints", "tasks", "verification_commands"],
    "properties": {
        "summary": {"type": "string"},
        "global_constraints": {"type": "string"},
        "verification_commands": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "files_owned", "requirements", "verification"],
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "files_owned": {"type": "array", "items": {"type": "string"}},
                    "requirements": {"type": "string"},
                    "verification": {"type": "string"}
                }
            }
        }
    }
}

IMPL_SCHEMA = {
    "type": "object",
    "required": ["status", "files_changed", "test_summary", "notes"],
    "properties": {
        "status": {"type": "string", "enum": ["DONE", "DONE_WITH_CONCERNS", "BLOCKED"]},
        "files_changed": {"type": "array", "items": {"type": "string"}},
        "test_summary": {"type": "string"},
        "notes": {"type": "string"}
    }
}

REVIEW_SCHEMA = {
    "type": "object",
    "required": ["verdict", "blocking_issues", "summary"],
    "properties": {
        "verdict": {"type": "string", "enum": ["APPROVED", "CHANGES_REQUESTED"]},
        "blocking_issues": {
            "type": "array",
            "items": {"type": "string"}
        },
        "summary": {"type": "string"}
    }
}

VERIFY_SCHEMA = {
    "type": "object",
    "required": ["verdict", "checks", "failure_details"],
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "checks": {"type": "array", "items": {"type": "string"}},
        "failure_details": {"type": "string"}
    }
}

phase("1. Architecture & Task Decomposition")
log(f"Planning feature: {goal}")

plan = await agent(
    prompt=(
        f"Design an atomic, step-by-step implementation plan for the following goal:\n\n"
        f"GOAL:\n{goal}\n\n"
        f"CONSTRAINTS:\n{constraints}\n\n"
        f"Explore the codebase in read-only mode, identify existing utilities and conventions, "
        f"and decompose the work into ordered, self-contained tasks (1 to 5 tasks) with explicit file ownership."
    ),
    schema=PLAN_SCHEMA,
    role="Architect: Feature Plan",
    type_name="architect",
)

tasks = plan.get("tasks") or []
if not tasks:
    raise ValueError("Architect returned an empty task list for build_pipeline.py")

log(f"Plan Summary: {plan['summary']}")
log(f"Tasks decomposed: {len(tasks)}")

phase("2. Staged TDD Implementation & Review Gates")

completed_tasks = []
has_blockers = False

for task in tasks:
    task_id = task["id"]
    task_title = task["title"]
    log(f"Starting Task {task_id}: {task_title}")

    impl_agent = agent(
        prompt=(
            f"You are implementing Task {task_id} ({task_title}) of a feature build.\n\n"
            f"GLOBAL CONSTRAINTS:\n{plan['global_constraints']}\n\n"
            f"FILES OWNED:\n{', '.join(task['files_owned'])}\n\n"
            f"TASK REQUIREMENTS:\n{task['requirements']}\n\n"
            f"TASK VERIFICATION:\n{task['verification']}\n\n"
            f"Implement the task using TDD, run the verification command, and return your structured report."
        ),
        schema=IMPL_SCHEMA,
        role=f"Implementer: Task {task_id} — {task_title}",
        type_name="implementer",
    )

    impl_report = await impl_agent(
        "Execute the task brief now and report your results.",
        IMPL_SCHEMA,
    )
    log(f"Task {task_id} implementation status: {impl_report['status']} ({impl_report['test_summary']})")

    unresolved_issues = []
    if impl_report["status"] == "BLOCKED":
        has_blockers = True
        unresolved_issues.append(f"Task {task_id} reported BLOCKED: {impl_report['notes']}")
        log(f"Task {task_id} is BLOCKED; skipping review gates for this task.")
    else:
        for fix_round in range(1, max_fix_rounds + 1):
            review_specs = [
                {
                    "type_name": "code-reviewer",
                    "role": f"Code Review: Task {task_id} (R{fix_round})",
                    "prompt": (
                        f"Audit the implementation of Task {task_id} ({task_title}).\n"
                        f"Requirements:\n{task['requirements']}\n"
                        f"Files changed: {', '.join(impl_report['files_changed'])}\n"
                        f"Check git diff and connected callers. Flag only CRITICAL or IMPORTANT issues in blocking_issues."
                    ),
                },
                {
                    "type_name": "security-auditor",
                    "role": f"Security Audit: Task {task_id} (R{fix_round})",
                    "prompt": (
                        f"Audit the security of Task {task_id} ({task_title}).\n"
                        f"Files changed: {', '.join(impl_report['files_changed'])}\n"
                        f"Check trust boundaries, auth, input validation, and secrets. "
                        f"Put any CRITICAL or HIGH security issues in blocking_issues."
                    ),
                },
            ]

            reviews = await parallel(
                review_specs,
                lambda spec: agent(
                    prompt=spec["prompt"],
                    schema=REVIEW_SCHEMA,
                    role=spec["role"],
                    type_name=spec["type_name"],
                ),
            )

            blocking = []
            for r in reviews:
                if r["verdict"] == "CHANGES_REQUESTED" and r["blocking_issues"]:
                    blocking.extend(r["blocking_issues"])

            if not blocking:
                log(f"Task {task_id} passed both Code Review and Security Audit.")
                unresolved_issues = []
                break

            unresolved_issues = blocking
            log(f"Task {task_id} review flagged {len(blocking)} blocking issue(s); running fix round {fix_round}...")
            issues_bullet = "\n".join(f"- {issue}" for issue in blocking)
            impl_report = await impl_agent(
                f"Address the following blocking review findings without breaking existing tests:\n{issues_bullet}",
                IMPL_SCHEMA,
            )
            if impl_report["status"] == "BLOCKED":
                has_blockers = True
                unresolved_issues.append(f"Task {task_id} became BLOCKED during fix round {fix_round}: {impl_report['notes']}")
                break

        if unresolved_issues:
            has_blockers = True
            log(f"Task {task_id} finished with {len(unresolved_issues)} unresolved blocking issue(s).")

    del impl_agent
    completed_tasks.append({
        "id": task_id,
        "title": task_title,
        "status": impl_report["status"],
        "files_changed": impl_report["files_changed"],
        "unresolved_issues": unresolved_issues,
    })

phase("3. Final Workspace Verification")

verify_cmds = "\n".join(f"- {c}" for c in plan.get("verification_commands", []))
final_verification = await agent(
    prompt=(
        f"Run final verification for the completed feature:\n{goal}\n\n"
        f"Suggested verification commands from Architect:\n{verify_cmds or '(Auto-detect from project root)'}\n\n"
        f"Execute build, typecheck, lint, and test suites and return the structured verification result."
    ),
    schema=VERIFY_SCHEMA,
    role="Verifier: Final Suite",
    type_name="verifier",
)

log(f"Final Verification Verdict: {final_verification['verdict']}")
for chk in final_verification.get("checks", []):
    log(f"  {chk}")

overall_status = "PASS"
if final_verification["verdict"] != "PASS":
    overall_status = "FAIL"
elif has_blockers:
    overall_status = "NEEDS_ATTENTION"

print({
    "overall_status": overall_status,
    "plan_summary": plan["summary"],
    "completed_tasks": completed_tasks,
    "final_verification": final_verification,
})
