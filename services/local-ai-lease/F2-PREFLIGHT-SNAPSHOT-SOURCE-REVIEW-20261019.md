# F2 slow preflight snapshot — source-only review

Status: offline candidate; not installed, scheduled, or run against the live
backup chain. This candidate does not create a receipt or advance F2.

## Purpose

The October 19 automation missed the complete preflight before the narrow
01:10–01:19 scan window. `scripts/local-ai/f2_preflight_snapshot.py` moves the
slow read-only observations earlier: Proxmox artifact identity, fixed backup
job, all three TrueNAS schedule results, exact LXC110 mirror identity, and
manual lease readiness. It stores only content-free digests and booleans.

At the intended 01:10 boundary, the preflight requires task 1 to be complete
after the Proxmox artifacts while validating the fixed schedule identities for
tasks 1/3/2; it does not incorrectly require the future 02:00 and 03:00 jobs
to have run. The final guard independently reads the host clock, confirms the
local cycle and 01:10–01:19 window, requires the real shared `host_exclusion`
flock, re-reads manual lease readiness, lease/receipt absence,
competing-process absence, suitable load, and all
configured installed pins. A
stale snapshot, changed exclusion, missing source, malformed JSON,
artifact/mirror mismatch, schedule failure, or lease drift fails closed.

The snapshot's archive field means verified artifact identity and metadata
binding, not a full archive-content hash or retained-integrity proof. F2/F3
still require the separately reviewed retained-integrity and receipt paths.

## Fixed source and evidence

The candidate uses the existing fixed TrueNAS observer identity and host-key
path from `fixed_source_adapters.py`; it does not use root SSH or print task
logs, archive paths, secrets, or credentials. Its tests cover a complete chain,
stale snapshot, exclusion drift, and missing artifact failure.

The same source-only change adds
`scripts/local-ai/lab_macbook_admission_adapter.py` and
`scripts/local-ai/lab_macbook_forced_command.py`. The fixed forced-command
producer binds the fresh session to sshd's `SSH_ORIGINAL_COMMAND` and
`SSH_CONNECTION`, a reviewed authorized-key fingerprint/host key, a fresh
nonce, and a 120-second expiry. It constructs the lab
manifest only from an authenticated session principal, client-key fingerprint,
and pinned host key; caller request JSON cannot supply those identities. The
forced-command attestation loader requires a root-owned private directory and
0600 regular file. The adapter is not a network listener and does not grant
GPU access.

## Pinned local result

The complete `scripts/local-ai` suite passes **309 tests, 4 expected skips**.
The source remains uninstalled. Target staging still requires exact hashes,
private root-owned replay-store and snapshot custody, authenticated MacBook
forced-command session proof, and separate approval. No F2 scan, zstd run,
receipt write, lease start, service stop, timer enablement, or model call
occurred.
