# ADF Multi-Angle Parallel Audit (run_workflow script)
# Simultaneously dispatches: code-reviewer, security-auditor, architect, and verifier

wf_args = globals().get("args") or {}
scope = wf_args.get("scope", "Current uncommitted git changes (git status / git diff HEAD)").strip()
context = wf_args.get("context", "General comprehensive quality, security, and architecture audit.").strip()

ANGLE_SCHEMA = {
    "type": "object",
    "required": ["angle", "verdict", "findings", "summary"],
    "properties": {
        "angle": {"type": "string"},
        "verdict": {"type": "string", "enum": ["PASS", "WARN", "FAIL"]},
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["severity", "location", "title", "detail", "fix"],
                "properties": {
                    "severity": {"type": "string", "enum": ["CRITICAL", "IMPORTANT", "MINOR"]},
                    "location": {"type": "string"},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "fix": {"type": "string"}
                }
            }
        }
    }
}

phase("1. Parallel 4-Angle Audit")
log(f"Auditing scope: {scope}")

angles = [
    {
        "angle": "Correctness & Logic",
        "type_name": "code-reviewer",
        "role": "Code Reviewer: Correctness & Edge Cases",
        "prompt": (
            f"Audit the following scope for logic errors, concurrency bugs, broken callers, "
            f"missing error handling, and spec compliance.\n\n"
            f"SCOPE: {scope}\nCONTEXT: {context}\n\n"
            f"Set angle='Correctness & Logic' and return structured findings."
        ),
    },
    {
        "angle": "Security & Trust Boundaries",
        "type_name": "security-auditor",
        "role": "Security Auditor: Vulns & Auth",
        "prompt": (
            f"Audit the following scope for security vulnerabilities (auth bypass, IDOR, injection, "
            f"XSS, SSRF, secrets exposure, unsafe deserialization).\n\n"
            f"SCOPE: {scope}\nCONTEXT: {context}\n\n"
            f"Map CRITICAL/HIGH to CRITICAL, MEDIUM to IMPORTANT, LOW to MINOR. "
            f"Set angle='Security & Trust Boundaries'."
        ),
    },
    {
        "angle": "Architecture & Simplicity",
        "type_name": "architect",
        "role": "Architect: Coupling & YAGNI Audit",
        "prompt": (
            f"Audit the following scope for architectural boundary violations, tight coupling, "
            f"redundant abstractions, or YAGNI bloat that could be simplified.\n\n"
            f"SCOPE: {scope}\nCONTEXT: {context}\n\n"
            f"Set angle='Architecture & Simplicity' and return structured findings."
        ),
    },
    {
        "angle": "Build, Types & Test Coverage",
        "type_name": "verifier",
        "role": "Verifier: Build & Test Audit",
        "prompt": (
            f"Run build, typecheck, linter, and relevant tests for the following scope, "
            f"and check if risky code paths lack tests.\n\n"
            f"SCOPE: {scope}\nCONTEXT: {context}\n\n"
            f"Report any failing checks as CRITICAL and missing test coverage on risky logic as IMPORTANT. "
            f"Set angle='Build, Types & Test Coverage'."
        ),
    },
]

reports = await parallel(
    angles,
    lambda a: agent(
        prompt=a["prompt"],
        schema=ANGLE_SCHEMA,
        role=a["role"],
        type_name=a["type_name"],
    ),
)

phase("2. Aggregating & Ranking Findings")

severity_order = {"CRITICAL": 0, "IMPORTANT": 1, "MINOR": 2}
all_findings = []

for rep in reports:
    log(f"[{rep['angle']}] Verdict: {rep['verdict']} — {rep['summary']}")
    for f in rep.get("findings", []):
        f_with_angle = dict(f)
        f_with_angle["angle"] = rep["angle"]
        all_findings.append(f_with_angle)

all_findings.sort(key=lambda item: severity_order.get(item.get("severity", "MINOR"), 3))

overall_verdict = "PASS"
if any(f["severity"] == "CRITICAL" for f in all_findings):
    overall_verdict = "FAIL"
elif any(f["severity"] == "IMPORTANT" for f in all_findings):
    overall_verdict = "WARN"

log(f"Overall Review Verdict: {overall_verdict} ({len(all_findings)} total findings)")

print({
    "overall_verdict": overall_verdict,
    "angle_summaries": [
        {"angle": r["angle"], "verdict": r["verdict"], "summary": r["summary"]}
        for r in reports
    ],
    "findings": all_findings,
})
