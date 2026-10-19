# F2 slow preflight snapshot — source-only review

Status: offline candidate; not installed, scheduled, or run against the live
backup chain. This candidate does not create a receipt or advance F2.

## Purpose

The October 19 automation missed the complete preflight before the narrow
01:10–01:19 scan window. `scripts/local-ai/f2_preflight_snapshot.py` moves the
slow read-only observations earlier: Proxmox artifact identity, fixed backup
job, all three TrueNAS schedule results, exact LXC110 mirror identity, and
manual lease readiness. It stores only content-free digests and booleans.

The final guard rechecks that the snapshot is no more than 90 seconds old and
that the active exclusion token is unchanged. A stale snapshot, changed
exclusion, missing source, malformed JSON, artifact/mirror mismatch, schedule
failure, or lease drift fails closed.

The snapshot's archive field means verified artifact identity and metadata
binding, not a full archive-content hash or retained-integrity proof. F2/F3
still require the separately reviewed retained-integrity and receipt paths.

## Fixed source and evidence

The candidate uses the existing fixed TrueNAS observer identity and host-key
path from `fixed_source_adapters.py`; it does not use root SSH or print task
logs, archive paths, secrets, or credentials. Its tests cover a complete chain,
stale snapshot, exclusion drift, and missing artifact failure.

The same source-only change adds
`scripts/local-ai/lab_macbook_admission_adapter.py`. It constructs the lab
manifest only from an authenticated session principal, client-key fingerprint,
and pinned host key; caller request JSON cannot supply those identities. The
adapter is not a network listener and does not grant GPU access.

## Pinned local result

The complete `scripts/local-ai` suite passes **309 tests, 4 expected skips**.
The source remains uninstalled. Target staging still requires exact hashes,
private root-owned replay-store custody, authenticated MacBook session proof,
and separate approval. No F2 scan, zstd run, receipt write, lease start,
service stop, timer enablement, or model call occurred.
