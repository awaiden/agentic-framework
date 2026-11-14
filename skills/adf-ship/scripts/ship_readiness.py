# ADF Pre-Ship Readiness & Verification Gate (run_workflow script)
# Runs verifier, security-auditor, and code-reviewer in parallel for Go/No-Go release readiness

import re

wf_args = globals().get("args") or {}
base_ref = str(wf_args.get("base_ref") or "HEAD").strip()

if not re.match(r"^[a-zA-Z0-9._/~^-]+$", base_ref):
    raise ValueError(f"Invalid base_ref '{base_ref}' for ship_readiness.py")

GATE_SCHEMA = {
    "type": "object",
    "required": ["gate", "status", "blockers", "summary", "commit_and_pr_draft"],
    "properties": {
        "gate": {"type": "string"},
        "status": {"type": "string", "enum": ["PASS", "FAIL"]},
        "blockers": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "commit_and_pr_draft": {"type": "string"}
    }
}

phase("1. Parallel Pre-Flight Gates (Build/Test, Security, Diff Hygiene)")
log(f"Running pre-ship verification against base_ref='{base_ref}'...")

gates = [
    {
        "type_name": "verifier",
        "role": "Verifier: Build, Lint & Test Gate",
        "prompt": (
            f"Run the project's build, typecheck, linter, and unit/integration test suites.\n"
            f"Set gate='Build, Lint & Tests', status='PASS' if all succeed else 'FAIL', "
            f"list any failing commands in blockers, and leave commit_and_pr_draft empty."
        ),
    },
    {
        "type_name": "security-auditor",
        "role": "Security Auditor: Secret & Vuln Gate",
        "prompt": (
            f"Inspect git status and git diff {base_ref} for leaked secrets, API keys, `.env` files, "
            f"debug bypasses, or high-severity security vulnerabilities.\n"
            f"Set gate='Security & Secrets', status='PASS' if clean else 'FAIL', "
            f"list any blocking risks in blockers, and leave commit_and_pr_draft empty."
        ),
    },
    {
        "type_name": "code-reviewer",
        "role": "Code Reviewer: Diff Hygiene & PR Summary",
        "prompt": (
            f"Inspect git status and git diff {base_ref} for leftover debug logs, accidental edits, "
            f"broken imports, or critical logic bugs.\n"
            f"Set gate='Diff Hygiene & Review', status='PASS' if ready to ship else 'FAIL'.\n"
            f"In commit_and_pr_draft, write a concise Conventional Commit message and a structured "
            f"PR description (Summary, Key Changes, Verification)."
        ),
    },
]

gate_results = await parallel(
    gates,
    lambda g: agent(
        prompt=g["prompt"],
        schema=GATE_SCHEMA,
        role=g["role"],
        type_name=g["type_name"],
    ),
)

phase("2. Go / No-Go Release Verdict")

all_blockers = []
pr_draft = ""

for gr in gate_results:
    log(f"[{gr['gate']}] -> {gr['status']}: {gr['summary']}")
    if gr["status"] == "FAIL" or gr.get("blockers"):
        all_blockers.extend(f"[{gr['gate']}] {b}" for b in gr.get("blockers", []))
    if gr["gate"] == "Diff Hygiene & Review" and gr.get("commit_and_pr_draft"):
        pr_draft = gr["commit_and_pr_draft"]

decision = "GO" if all(g["status"] == "PASS" for g in gate_results) and not all_blockers else "NO_GO"
log(f"Ship Readiness Decision: {decision}")

print({
    "decision": decision,
    "gates": [
        {"gate": g["gate"], "status": g["status"], "summary": g["summary"]}
        for g in gate_results
    ],
    "blockers": all_blockers,
    "commit_and_pr_draft": pr_draft,
})
