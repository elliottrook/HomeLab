# SA1/SA2 one-run Doctor evidence canary

Date: 2026-09-28
Status: **completed one-run read-only canary; adapter disabled afterward**

## Scope and authorization

Jason authorized this bounded run after the disabled-baseline deployment. The
only temporary production change was a systemd drop-in that set
`ASTER_SYSADMIN_DOCTOR_EVIDENCE=1` for `aster-agent`; no other configuration,
model, identity, listener, target or tool permission changed. The canary opened
one service-local test incident, read the existing fixed sanitized Doctor report
once, generated the concise reconnect representation, then removed the drop-in
and restarted only `aster-agent` with the feature disabled again.

It did not refresh Doctor, contact the Mac/Proxmox source, use a human bearer
credential, invoke Lab Operations, make a repair, or claim that the observed
failure was fixed.

## Result

The canary produced exactly one observation:

| Field | Observed value |
|---|---|
| Source | `homelab-doctor-report/v1` |
| Aggregate state | `fail` |
| Report age | 27,768 seconds at read time |
| Observation count | 1 |
| Next state | `sufficient_or_escalate` |
| Presentation check | Facts and hypotheses excluded |

The `fail` result is the existing sanitized Doctor aggregate state. It is an
input observation, not an explanation, repair result or broad health claim.

The first invocation attempted to run the one-shot script from `/tmp`, where a
temporary staged module shadowed the installed Aster module and failed before
the adapter could read a report. Re-running the identical script from the
installed Aster directory succeeded. This found and resolved a test-staging
path issue; no service rollback was needed.

## Cleanup and limits

The temporary enablement drop-in and runner were removed. The single canary
SQLite record and its journal files were removed after recording the sanitized
result. The service was restarted once more, confirmed active, and its service
user confirmed `SYSADMIN_DOCTOR_EVIDENCE` false. `GET /health` returned the
normal Aster gateway response.

This establishes one fixed-path read observation and presentation proof only.
It does not establish an authenticated real-user Companion flow, incident
retention behavior, repeated/deduplicated report handling, a 36-hour stale
case, streaming client behavior, Qwen diagnostic quality, SA1/SA2 completion or
any authorization for repair.
