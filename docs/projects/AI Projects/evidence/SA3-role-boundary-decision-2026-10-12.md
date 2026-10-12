# SA3 role boundary decision — 2026-10-12

Jason clarified the intended architecture: the operational sysadmin role is
handed to a Codex instance. This is a role assignment, not a claim that the
B60-backed local Qwen runtime is equivalent to Codex.

Codex owns the sysadmin investigation loop, authorized tool use, repair
planning and execution, and independent verification. Deterministic policy,
AI-PAM, narrow adapters, human authorization and recovery controls remain
mandatory. Aster/Qwen remains useful for explicitly bounded local analysis,
private email/calendar work, summaries and other scheduled workloads, but does
not receive implied sysadmin authority.

The SA3 holdout and citation-repair results remain retained as negative
engineering evidence: they demonstrate contract and role limits, not a reason
to keep tuning Qwen toward Codex parity. Further Qwen sysadmin evaluations are
paused unless Jason explicitly reopens that research question. No production
runtime, permission, routing or schedule change is implied by this decision.
