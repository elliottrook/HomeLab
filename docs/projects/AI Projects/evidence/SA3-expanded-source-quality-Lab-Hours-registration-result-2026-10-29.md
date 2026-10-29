# SA3 expanded-source quality Lab Hours registration result — 2026-10-29

Status: **SOURCE REGISTRATION PASS; LIVE TRANSACTION NO-GO**

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

No registration, transaction, adapter or guest wrapper is installed on Proxmox
or LXC110, and no booking, window check,
schedule, model call, backend change, restart, routing, repair or production
effect occurred.
