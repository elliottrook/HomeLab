# SA3 expanded-source quality Lab Hours registration result — 2026-10-29

Status: **PASS — DORMANT RUNTIME AND INACTIVE REGISTRATION VALIDATED**

The Lab Hours platform branch now contains a distinct fixed registration for
`sa3-expanded-source-quality-v1` at commit `53c81e1c`. The platform card is
`services/local-ai-lease/ASTER-LAB-HOURS-SA3-REGISTRATION-INACTIVE-CARD-20261029.md`.

The registration binds the accepted model/binary/unit baseline, exactly 20
requests, 120 seconds per request, a 2,700-second workload deadline, a minimum
3,600-second booking and a 900-second restoration reserve. Its four runtime
pins match the visible packet, validator, one-call/no-retry runner and the
independently reviewed fair scorer needed for Python import closure. The answer
key and independent-review receipt remain excluded.

The inactive validator requires exact hashes, root ownership, regular files,
one hard link, complete local import closure and absent target service/timer
units. The platform's focused registration and fail-closed runner suite passes
**17/17**.

## Deliberate NO-GO

This source registration is not a runnable workload. The existing reservation
runner has no SA3 full-drain transaction. A booking with this identity therefore
validates the inactive target and raises `WORKLOAD_RUNNER_UNAVAILABLE` before
any production drain. The registered 2,700-second guardian boundary replaces
the three-request smoke's 1,800-second value, but no SA3 owner transaction is
installed.

## Corrected source transaction

Platform commit `e3e1872e` now supplies the inactive transaction source at
SHA-256
`0706912279bcb4a511633cfb22f19e691eed94f4aa79e07bdc332f87d0dbbc70`.
The corrected 25/25 platform suite proves exact model and 20-case identity,
finite latency, zero retries, bounded mode-0600 result retention, digest-only
receipt projection, guardian heartbeats, success cleanup before restoration,
and cleanup/restoration on all tested failure paths. The transaction rejects
substituted identities and non-finite latency.

## Fixed listener and guest boundary

Platform commit `0dfe3d28` added the fixed guest wrapper and file-backed
listener adapter. Independent Stream A review accepted the wrapper's fixed
model, binary, four-file runtime, ephemeral key, lease/generation scope and
cleanup boundary, but rejected the adapter's initial silent capture-directory
cleanup and insufficient pre-existing-root custody check.

Platform commit `8dc6eac5` closes that review finding. The adapter at SHA-256
`a6387092f04a8fa8cc35254ce19c9a479cd0177b2fd53caae40ee6012c38f917`
rejects symlink, non-directory, wrong-owner or unsafe-mode capture roots; creates
root-only files without following links; rechecks regular-file, single-link,
owner and mode custody before reading; and fails the transaction if any capture
artifact survives cleanup. The fixed guest wrapper remains pinned at SHA-256
`27949ff1ba37f825de8d3c4aaeaf6388b9535e72d0063e46eac0e491a6604303`.
The combined adapter, wrapper and transaction suite passes 46/46, and all 19
release-manifest pins verify.

The reserved runner still returns `WORKLOAD_RUNNER_UNAVAILABLE`. The source is
accepted but remains inactive until an exact installation card, rollback
checkpoint and target-Linux validation pass.

## Dormant installation and live-baseline reconciliation

The separately reviewed `root-v3` transaction subsequently installed the two
dormant Proxmox modules and five dormant LXC110 files. All reviewed hashes,
modes, owners and host/guest imports passed; both rollback checkpoints remain.
No SA3 registration, unit, booking, lease, model request, drain, restart or
route was created.

The earlier source registration at `53c81e1c` is not suitable for direct live
installation. The working Proxmox baseline contains later exclusive-capacity
reservation behavior which that source commit predates, and its release
manifest incorrectly treated the guest wrapper as a Proxmox file. Platform
commit `8fc3772a98053d9688e927dc2ef9da655567cd51` reconciles the fixed SA3
identity with the measured live baseline while retaining `reserved` state,
exclusive-stack reservations, cancellation of unclaimed exclusive bookings and
the prohibition on dispatching an exclusive handoff through the smoke runner.

The new installer changes exactly five Proxmox files: it adds the fixed
workload registry and inactive-target validator, and replaces the reservation
module, reserved runner and release manifest against their exact live hashes.
It preserves twelve unchanged live manifest pins and excludes the LXC110
wrapper from the Proxmox manifest. The SA3 runner still fails closed with
`WORKLOAD_RUNNER_UNAVAILABLE` before attempt evidence, guardian arming or
production drain.

The registry, reservation, runner, dispatcher, Doctor and installer suite
passes **23/23**. Two independent builds produced the same
`aster-sa3-registration-v1.tar.gz` at SHA-256
`78a4fe9996e784814bc4130b8c849cc46e969f5a6e2511c8e2fb099a77b6ff54`.
The installer requires the exact three live replacement baselines and two
absent targets, validates every unchanged manifest pin, checkpoints exact
bytes/absence under a fresh root-only identity, installs atomically, imports
the complete closure and rolls back all five files on failure or uncertainty.

## Live inactive registration result

The exact five-file transaction installed successfully with its root-only
rollback checkpoint retained. All installed hashes, modes, owners, imports and
eighteen manifest pins passed. The workload is registered but the runner still
returns `WORKLOAD_RUNNER_UNAVAILABLE` before attempt evidence, guardian arming
or production drain.

The first independent validator invocation then found a real namespace defect:
the validator looked for the four evaluation files on Proxmox although the
reviewed dormant installation correctly placed them in LXC110. It failed closed
with no booking, lease, attempt, model request or service effect. Platform
commit `4bad2da3` corrects that boundary with a fixed `pct exec 110` verifier;
it accepts no command or guest input and passes only the registered four-file
pin set on standard input.

The correction passed 29/29 tests and deterministic bundle reproduction. Its
two-file live upgrade passed, retained its second rollback checkpoint, and the
independent installed validator returned `state=valid`, `guest=110`,
`runtime_files=4`, `target_units=absent` and `effects=not-attempted`.
LXC104/110/116 and all production services and Proxmox daemons remained
healthy; the lease remains exactly ready.

Inactive registration and target validation are complete. The next gate is
implementation of the exact reserved-runner transaction using the already
installed host transaction, listener and fixed guest wrapper. Only after that
passes may a later evaluation receive its own authoritative Lab Hours check,
reservation, whole-host lease and shared operation lock.

## Reserved-runner activation

The first activation package failed before any target write because its source
mode check confused repository staging modes with eventual executable target
modes. Corrected platform candidate `2859279c` used a fresh identity, passed
53/53 focused tests and two deterministic builds, and installed successfully.
Independent postcheck verifies the fixed SA3 profile, booking-specific retained
result root, all eighteen manifest pins and healthy production. No SA3 booking
or attempt exists and the lease remains ready. The runner implementation gate
is complete; the immediate next item is an authoritative conflict check and
fixed reservation for one bounded evaluation.
