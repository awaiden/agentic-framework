# ADF Parallel Hypothesis Bug-Hunt Workflow (run_workflow script)
# Orchestrates: debugger (hypotheses) -> parallel(debugger investigations) -> implementer (fix) -> verifier

wf_args = globals().get("args") or {}
symptom = wf_args.get("symptom", "").strip()
repro_command = wf_args.get("repro_command", "").strip()
apply_fix = bool(wf_args.get("apply_fix", True))

if not symptom:
    raise ValueError("Missing required 'symptom' in Args for hypothesis_hunt.py")

HYPOTHESES_SCHEMA = {
    "type": "object",
    "required": ["observed_behavior", "hypotheses"],
    "properties": {
        "observed_behavior": {"type": "string"},
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "theory", "files_to_check"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "theory": {"type": "string"},
                    "files_to_check": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    }
}

INVESTIGATION_SCHEMA = {
    "type": "object",
    "required": ["id", "status", "confidence", "root_cause_location", "evidence", "proposed_fix"],
    "properties": {
        "id": {"type": "string"},
        "status": {"type": "string", "enum": ["CONFIRMED", "PLAUSIBLE", "REFUTED"]},
        "confidence": {"type": "integer"},
        "root_cause_location": {"type": "string"},
        "evidence": {"type": "string"},
        "proposed_fix": {"type": "string"}
    }
}

FIX_SCHEMA = {
    "type": "object",
    "required": ["status", "files_changed", "test_added", "summary"],
    "properties": {
        "status": {"type": "string", "enum": ["DONE", "DONE_WITH_CONCERNS", "BLOCKED"]},
        "files_changed": {"type": "array", "items": {"type": "string"}},
        "test_added": {"type": "string"},
        "summary": {"type": "string"}
    }
}

VERIFY_SCHEMA = {
    "type": "object",
    "required": ["verdict", "checks", "details"],
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "checks": {"type": "array", "items": {"type": "string"}},
        "details": {"type": "string"}
    }
}

phase("1. Symptom Analysis & Hypothesis Formulation")
log(f"Analyzing symptom: {symptom}")

initial = await agent(
    prompt=(
        f"Analyze the following bug or failure symptom and formulate 2 to 4 distinct, "
        f"falsifiable root-cause hypotheses:\n\n"
        f"SYMPTOM:\n{symptom}\n\n"
        f"REPRODUCTION COMMAND:\n{repro_command or '(None provided — inspect code & tests)'}\n\n"
        f"Do not edit any files. Return your hypotheses in the required JSON schema."
    ),
    schema=HYPOTHESES_SCHEMA,
    role="Debugger: Hypothesis Generator",
    type_name="debugger",
)

hypotheses = initial.get("hypotheses") or []
if not hypotheses:
    raise ValueError("Debugger did not return any hypotheses to investigate.")
log(f"Formulated {len(hypotheses)} hypotheses to test in parallel.")

phase("2. Parallel Hypothesis Investigation")

investigations = await parallel(
    hypotheses,
    lambda h: agent(
        prompt=(
            f"Investigate Hypothesis {h['id']}: {h['title']}\n\n"
            f"SYMPTOM:\n{symptom}\n\n"
            f"THEORY TO TEST:\n{h['theory']}\n\n"
            f"FILES TO INSPECT:\n{', '.join(h.get('files_to_check', []))}\n\n"
            f"Gather concrete code and runtime evidence for and against this hypothesis. "
            f"Mark status as CONFIRMED (proven with exact line/state evidence), PLAUSIBLE, or REFUTED."
        ),
        schema=INVESTIGATION_SCHEMA,
        role=f"Debugger [{h['id']}]: {h['title']}",
        type_name="debugger",
    ),
)

status_rank = {"CONFIRMED": 0, "PLAUSIBLE": 1, "REFUTED": 2}
ranked = sorted(
    investigations,
    key=lambda x: (status_rank.get(x["status"], 3), -int(x.get("confidence", 0))),
)

for inv in ranked:
    log(f"Hypothesis {inv['id']} -> {inv['status']} (confidence={inv['confidence']}%): {inv['root_cause_location']}")

winner = ranked[0] if ranked else None
fix_result = None
verification_result = None
verdict = "INCONCLUSIVE"

if apply_fix and winner and winner["status"] in ("CONFIRMED", "PLAUSIBLE"):
    phase("3. Root-Cause Remediation & Regression Verification")
    log(f"Applying minimal fix for confirmed root cause at {winner['root_cause_location']}...")

    fix_result = await agent(
        prompt=(
            f"Apply the minimal root-cause fix and regression test for the following confirmed bug:\n\n"
            f"SYMPTOM:\n{symptom}\n\n"
            f"CONFIRMED ROOT CAUSE ({winner['root_cause_location']}):\n{winner['evidence']}\n\n"
            f"PROPOSED FIX:\n{winner['proposed_fix']}\n\n"
            f"REPRODUCTION COMMAND:\n{repro_command or '(Run relevant unit/integration tests)'}\n\n"
            f"Write or update a regression test and implement the smallest complete fix."
        ),
        schema=FIX_SCHEMA,
        role="Implementer: Root-Cause Fix",
        type_name="implementer",
    )

    if fix_result["status"] == "BLOCKED":
        verdict = "BLOCKED"
        log(f"Fix implementation was BLOCKED: {fix_result['summary']}")
    else:
        verification_result = await agent(
            prompt=(
                f"Verify that the bug fix resolves the issue and breaks no existing tests.\n"
                f"Files changed: {', '.join(fix_result.get('files_changed', []))}\n"
                f"Reproduction command: {repro_command or '(Auto-detect test suite)'}"
            ),
            schema=VERIFY_SCHEMA,
            role="Verifier: Regression Check",
            type_name="verifier",
        )
        verdict = verification_result["verdict"]
        log(f"Post-fix verification verdict: {verdict}")
elif winner and winner["status"] in ("CONFIRMED", "PLAUSIBLE"):
    verdict = "DIAGNOSED_ONLY"

print({
    "verdict": verdict,
    "observed_behavior": initial["observed_behavior"],
    "ranked_hypotheses": ranked,
    "winning_hypothesis": winner,
    "fix_result": fix_result,
    "verification_result": verification_result,
})
