# M1/D4 fixed Doctor emitter — one-file correction card

**Date:** 2026-10-25  
**Status:** approval-ready; source-only  
**Manifest:** `scripts/deploy/fixed-doctor-emitter-correction-manifest.json`, SHA-256 `91da87921597809156026c54bf4b1e781a7e11549abc6912567b597e4c2f77a8`

## Exact change

Require the live `/Users/jelliott/lab/homelab/scripts/doctor.sh` predecessor to
match `1f7f03d1033c0696d440e1d45d3e38f3691d7446a7596c120785275cd525e587`.
Generate the candidate with
`scripts/deploy/patch_live_doctor_structured_emitter.py`, require SHA-256
`c3f4d961fe7ce2b25990c0e1317a326eeefd82a80bfc6a6e2d74461fcdfe8e09`
and `bash -n`, checkpoint the predecessor, then replace that one file
atomically as `jelliott:staff` mode `0755`.

The diff contains only the private inherited-FD emitter and the current
`check_aster` contract. It preserves all other production Doctor checks. The
new contract observes the Aster Agent, accepted `aster-llama.service`, API,
`xe` driver binding, stopped rollback VM and absence of persistent passthrough.
It no longer claims Vulkan or treats a `vulkaninfo` result as proof of the
accepted production backend. It explicitly says GPU offload is not verified.

## Validation

After replacement, run one builder-only canary under the existing producer
card and 930-second bound. Do not invoke `scheduled-report.sh`. Require:

- exact local/remote digest and timestamp binding;
- fixed check state `pass`, `fail` or `unavailable` from the same invocation;
- no free text in schema 2;
- correct local/remote modes and custody;
- absent remote `.new` files;
- Aster/broker healthy and fixed-Doctor services still disabled/inactive;
- unchanged LaunchAgent schedule and unchanged F2/F6/B60 state.

If the fixed state is `unavailable`, keep the capability closed and diagnose
the bounded observation failure; do not repeat the canary without a new gate.
Doctor exit `1` from unrelated health checks is retained as aggregate health
state and is not itself a producer rollback condition.

## Rollback

On any replacement, builder, publication or postcheck failure, restore the
exact Doctor predecessor plus the pre-canary local and remote report states,
remove both remote `.new` paths and verify the two already installed producer
files remain at their accepted hashes. Do not run the full LaunchAgent job to
prove rollback.

## Exclusions

No caller/gateway activation, broker replacement/restart, AI-PAM enrollment or
grant, model route/call, Companion change, schedule change, Mail-alert repair,
F2/F6/B60 action, Git push or checkpoint deletion is included.

The patch-generator suite passes 3/3, the complete producer/capability
boundary suite passes 40/40 and the generated candidate passes `bash -n`.
