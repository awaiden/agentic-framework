# ADF Parallel Multi-Agent Fan-Out (run_workflow script)
# Orchestrates: architect (partitioning) -> parallel(implementer) -> parallel(verifier, code-reviewer)

wf_args = globals().get("args") or {}
goal = str(wf_args.get("goal") or "").strip()
workspace_mode = str(wf_args.get("workspace_mode") or "inherit").strip()
provided_tasks = wf_args.get("tasks") or []

if workspace_mode not in ("inherit", "share", "branch"):
    raise ValueError(f"Invalid workspace_mode '{workspace_mode}'. Must be 'inherit', 'share', or 'branch'.")

if not goal and not provided_tasks:
    raise ValueError("Provide 'goal' or 'tasks' in Args for parallel_fanout.py")

PARTITION_SCHEMA = {
    "type": "object",
    "required": ["shared_constraints", "slices"],
    "properties": {
        "shared_constraints": {"type": "string"},
        "slices": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "files_owned", "requirements"],
                "properties": {
                    "title": {"type": "string"},
                    "files_owned": {"type": "array", "items": {"type": "string"}},
                    "requirements": {"type": "string"}
                }
            }
        }
    }
}

SLICE_RESULT_SCHEMA = {
    "type": "object",
    "required": ["title", "status", "files_changed", "summary"],
    "properties": {
        "title": {"type": "string"},
        "status": {"type": "string", "enum": ["DONE", "DONE_WITH_CONCERNS", "BLOCKED"]},
        "files_changed": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"}
    }
}

INTEGRATION_SCHEMA = {
    "type": "object",
    "required": ["verdict", "findings"],
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "findings": {"type": "array", "items": {"type": "string"}}
    }
}

if provided_tasks:
    phase("1. Using Provided Task Slices")
    shared_constraints = wf_args.get(
        "constraints",
        "Stay strictly within your assigned files_owned. Do not edit shared files outside your slice.",
    )
    slices = provided_tasks
else:
    phase("1. Partitioning Independent Work Slices")
    partition = await agent(
        prompt=(
            f"Partition the following goal into 2 to 8 strictly independent work slices "
            f"that can be implemented in parallel with ZERO overlapping files:\n\n"
            f"GOAL:\n{goal}\n\n"
            f"Ensure each slice lists its exact 'files_owned' and complete 'requirements'."
        ),
        schema=PARTITION_SCHEMA,
        role="Architect: Parallel Partitioner",
        type_name="architect",
    )
    shared_constraints = partition["shared_constraints"]
    slices = partition["slices"]

if not slices:
    raise ValueError("No parallel work slices to execute.")

# Guard against concurrent file collisions when running in shared workspace ('inherit')
if workspace_mode == "inherit":
    seen_files = {}
    overlapping = set()
    for s in slices:
        for f in s.get("files_owned", []):
            norm_f = f.strip()
            if norm_f in seen_files:
                overlapping.add(norm_f)
            seen_files[norm_f] = s["title"]
    if overlapping:
        log(
            f"Warning: Overlapping files_owned detected ({', '.join(sorted(overlapping))}). "
            f"Upgrading workspace_mode from 'inherit' to 'share' to prevent write collisions."
        )
        workspace_mode = "share"

log(f"Dispatching {len(slices)} parallel implementer slices (workspace={workspace_mode})...")

phase("2. Parallel Slice Implementation")

slice_results = await parallel(
    slices,
    lambda s: agent(
        prompt=(
            f"You are an Implementer executing one parallel slice of a larger task.\n\n"
            f"SLICE TITLE: {s['title']}\n"
            f"FILES YOU OWN (DO NOT TOUCH OTHER FILES): {', '.join(s.get('files_owned', []))}\n\n"
            f"SHARED CONSTRAINTS:\n{shared_constraints}\n\n"
            f"SLICE REQUIREMENTS:\n{s['requirements']}\n\n"
            f"Implement your slice cleanly and return your structured result."
        ),
        schema=SLICE_RESULT_SCHEMA,
        role=f"Implementer: {s['title']}",
        type_name="implementer",
        workspace=workspace_mode,
    ),
)

all_changed_files = sorted({
    f
    for res in slice_results
    for f in res.get("files_changed", [])
})
for res in slice_results:
    log(f"Slice '{res['title']}' -> {res['status']}: {res['summary']}")

phase("3. Parallel Integration Verification & Review")

integration_checks = [
    {
        "type_name": "verifier",
        "role": "Verifier: Integration Build & Tests",
        "prompt": (
            f"Verify that all parallel slices integrate cleanly.\n"
            f"Files modified across slices: {', '.join(all_changed_files)}\n"
            f"Run build, typecheck, lint, and tests. Report PASS or FAIL and any errors in findings."
        ),
    },
    {
        "type_name": "code-reviewer",
        "role": "Code Reviewer: Cross-Slice Consistency",
        "prompt": (
            f"Review the combined changes across all parallel slices for interface mismatches, "
            f"broken imports, or logic bugs.\n"
            f"Files modified: {', '.join(all_changed_files)}\n"
            f"Report PASS if clean, or FAIL with blocking issues in findings."
        ),
    },
]

integration_results = await parallel(
    integration_checks,
    lambda chk: agent(
        prompt=chk["prompt"],
        schema=INTEGRATION_SCHEMA,
        role=chk["role"],
        type_name=chk["type_name"],
    ),
)

for ir in integration_results:
    log(f"Integration check verdict: {ir['verdict']} ({len(ir.get('findings', []))} findings)")

print({
    "slice_results": slice_results,
    "integration_verification": integration_results[0],
    "integration_review": integration_results[1],
})
