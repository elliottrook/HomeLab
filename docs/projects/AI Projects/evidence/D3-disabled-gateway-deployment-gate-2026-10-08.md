# D3 — attach the gateway with delegation disabled

Status: APPROVED DISABLED DEPLOYMENT COMPLETE; approval consumed.
Real credential provisioning is complete; this is the next software integration
step, not another credential or model experiment.

## Executed result — 2026-10-08

Jason approved the bounded deployment. Rechecked live main-source hash, original
service command/user, 35-path route digest, healthy endpoints, destination absence
and inactive Authentik identity. Verified the frozen archive and all 14 members.
Created the root-0700 checkpoint with mode-0600 non-secret baseline manifest,
installed the 13 Python files and one disabled drop-in create-only, verified
hashes, compiled syntax in memory and passed `systemd-analyze verify`.

Reloaded systemd and restarted only `aster-agent.service` once. It returned active
and passed the first post-restart acceptance check within the 60-second window:

- `/health` and `/companion`: HTTP 200.
- Owner delegation route and POST worker offer route: HTTP 404.
- Same 35 OpenAPI paths and exact pre-deployment route/method digest.
- Main `aster_agent.py` hash unchanged; existing drop-ins retained.
- No delegation state directory or delivered runtime worker credential file.
- Authentik worker remains inactive; AI-PAM healthy with zero active requests and
  37 existing recorded outcomes; vault remains unsealed.

No rollback required. New disabled code/drop-in and recovery checkpoint remain as
approved. No credentials read, identity activation, model calls, network changes
or Git push. Tests establish disabled integration and route/health preservation,
not a claim that every household action was exercised.

Next: prepare the separately authorized authenticated pilot, including exact
worker subject, runtime credential delivery, admission of one fictional job and
actual owner-visible result. Do not repeat this successful disabled deployment.
Earlier prospective approval wording below is retained as the executed scope.

## Finding and implementation

Read-only inspection found the running `aster_agent.py` SHA-256 is
`f2c45986a9201d0fe01024a8ac47962600633f6bfa979972bf700762e2e3308f`,
while this branch's older copy is
`24bdc580f074003fe8fbb064c0f5effbded9f15a33e0a8ef07b37075d6511fb0`.
The difference is verified; its contents/cause have not been analyzed here.
Do not overwrite the running application with the older project copy.

Added `aster_with_delegation.py`, a small entrypoint that imports the existing
installed application and its existing Companion owner verifier. New
`delegation/deployment.py` attaches the gateway only for an explicit `1` setting.
Default/`0` registers no routes and does not import credential/gateway consumers,
open state, read credentials, call a broker or contact a network service.

For a later enabled deployment, attachment requires a pinned worker subject,
systemd credential path, vault CA path and no conflicting routes. These settings
are intentionally absent in this deployment. There is no job creation endpoint,
automatic worker startup or model dispatch.

230 local delegation tests pass. Four new tests cover preservation of the host
application's route/lifecycle behavior, disabled custody imports, refusal of
incomplete enabled configuration, duplicate attachment and reuse of the installed
application object. The local environment uses FastAPI 0.133.1 / Starlette 1.7.0;
the live environment reports FastAPI 0.133.1 / Starlette 1.6.0. Live verification is
therefore a deployment acceptance requirement, not claimed by local tests.

## Verified deployment baseline

- LXC 104, service `aster-agent.service`, user/group `aster`, working directory
  `/opt/aster-agent`, one Uvicorn worker bound to `192.168.70.10:9120`, no access log.
- Existing entrypoint: `aster_agent:app`. Five existing drop-ins remain untouched.
- New wrapper, delegation package, proposed drop-in and delegation state directory
  are absent. Do not assume a missing parent directory: create the explicitly
  listed new paths only, and verify existing `/opt/aster-agent` and service drop-in
  parent ownership before writing.
- `/health` and `/companion` return 200; owner delegation route returns 404.
- OpenAPI has 35 paths; sorted path/method-map SHA-256 is
  `c21b5cb51ab60d4d22788d7ebe6ed1d6d180370921e431a0aa65613f393a1357`.
- Recovery snapshot `aster-worker-preprovision-20261008` already exists. Do not
  recreate it or restore it for a wrapper rollback.

## Exact approval requested

One disabled deployment on LXC 104:

1. Recheck application hash, service command/user, health, route digest, absent
   destinations and that the new Authentik worker is still inactive. Stop on drift.
2. Create fresh root-0700
   `/var/lib/aster-delegation-checkpoints/disabled-20261008` (including new
   root-0700 parent if absent). Save non-secret baseline hashes, effective service
   command, route digest and deployment manifest there mode 0600. Never capture
   service environment values or credentials.
3. Install the 12 reviewed `delegation/*.py` files under new
   `/opt/aster-agent/delegation` (root 0755 directory, root 0644 files), and new
   `/opt/aster-agent/aster_with_delegation.py` root 0644. Verify archive and all
   member hashes; no overwrite. Do not copy this branch's `aster_agent.py`.
4. Install only
   `/etc/systemd/system/aster-agent.service.d/aster-delegation-disabled.conf`
   root 0644. It pins `ASTER_DELEGATION_ENABLED=0`, disables bytecode writes and
   substitutes `aster_with_delegation:app` in the otherwise identical ExecStart.
   It does NOT load the encrypted worker credential or set worker identity fields.
5. Validate Python syntax without executing the application, validate the unit,
   reload systemd and restart only `aster-agent.service` once. Expect a brief
   Aster/Companion interruption; existing independent household services are not
   restarted. No availability guarantee is inferred from prior tests.
6. Within 60 seconds require active service, health/Companion 200, unchanged 35-path
   route digest, delegation paths 404, no delegation state directory, unchanged
   main application hash and AI-PAM health. Confirm the Authentik worker remains
   inactive through non-secret metadata. No actual credential read or model call.
7. Record outcome and retain the new disabled code/drop-in/checkpoint on success.

Archive: `/private/tmp/aster-disabled-gateway-20261008.tar`

SHA-256: `8628de8b633cb9a4ca4148da1ba1988c2ea63f64d47a126d2e1b5fa2584ed83e`

The 14 members are `aster_with_delegation.py`,
`aster-delegation-disabled.conf`, and `delegation/` modules:
`deployment`, `gateway_assembly`, `credentials`, `broker_gate`, `handoff`,
`runtime`, `store`, `worker_auth`, `worker_router`, `usage`, `recovery`, `contract`.
Frozen per-file manifest is `/private/tmp/aster-disabled-gateway-20261008-manifest.json`.

## Explicit rollback authority

If validation fails, remove ONLY the new exact-hash drop-in, reload systemd and
restart Aster once to restore its original `aster_agent:app` command. Verify old
health/routes/hash. Leave inactive source files and checkpoint for diagnosis;
do not restore a guest snapshot, overwrite app code or touch unrelated drop-ins.
If old health does not recover, stop and report instead of repeated restarts.

This approval covers the deployment restart and, only on failure, that single
rollback restart. It does not cover activation, credential loading, Authentik
changes, model execution, tool grants, network changes or Git push. AGENTS.md
requires confirmation because these are remote writes and a service restart.

## Following step

Prepare one bounded authenticated pilot: confirm exact worker subject, verify
credential consumers and negative identity cases, create a single authorized
fictional assignment, allow one manual worker turn and verify owner-visible
result/cancellation controls. That later gate must name enabled settings and
identity changes. It is not authorized by this disabled deployment.

Pilot password expires October 9 at 7:02 PM America/Vancouver; the role SecretID
also has a 24-hour issuance lifetime. Do not rush or bypass checks to beat expiry.
If needed, prepare targeted renewal without recreating the identity or replaying
the completed provisioning controller.
