# Run 002 evidence

Run 002 was invoked once on 2026-09-26 under the fresh, bounded approval
recorded in `RUN-002-AUTHORIZATION.md`. The launcher verified the reviewed
manifest and approval record before opening the exclusive journal.

The result was `failed-or-inconclusive` during preflight. Records 001–004 show
that the unit-state, path, guest-health and host-LXC-status observations all
completed. Record 005 retains the bounded resource observation. Record 006
proves `mutation_attempted=false` and `manual_recovery_required=false`. There
is no create intent, run intent, canary receipt or remote stop. No accepted
corpus was evaluated and the one-shot approval was consumed; no retry is
authorized.

`reviewed-manifest.json` and `approval-record.json` are the exact bytes used
for the invocation, reconstructed after a concurrent documentation-only edit
and verified against the hashes in record 000 and the coordinating task's
pre-invocation output. `reviewed-LXC100-FEASIBILITY-PLAN.md` preserves the only
pinned artifact whose working-tree bytes changed after invocation. Every other
pinned artifact still matched the reviewed manifest when this evidence was
captured.

The lifecycle catches and deliberately does not journal exception text. The
failure happened after the resource observation and before `preflight-verified`,
so its precise cause is **UNKNOWN / REQUIRES VERIFICATION**. A separate fixed,
read-only two-query DNS diagnostic succeeded after the run. That establishes
current reachability only; it does not prove what failed during the attempt.
