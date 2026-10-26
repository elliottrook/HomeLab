# M3 NLU token-confidence v7 cross-set run card — 2026-10-26

**Status:** prepared; private-packet transfer and execution require explicit
approval.

## Purpose

Run the public-gate-passing candidate over only the six already-spent,
owner-only 60-case development sets. For each outer set, select v2 decision and
route thresholds solely from nested predictions over the other five sets, then
measure transfer to the outer set. This is development evidence, not an
independent calibration.

## Exact inputs

- Stream A source commit: `5e39444c`;
- candidate SHA-256:
  `81df2137c69445361446d6e02ec8a16ff3fc93092c3a499a2f9a614a7605afe7`;
- runner SHA-256:
  `f21db8e84001beac6f64ca5ae8714aebca665df9196eebfe9f2efa5ebbc20db7`;
- narrow source packet: 23,611 bytes, SHA-256
  `ab956d54fb8d52a7568dbfe939737943137d76b4751936c405eb6f541d4a35ac`;
- owner-only spent-set packet: 85,602 bytes, SHA-256
  `dc5e5946fdfebd43920d4ac0afbb1313a5b73448d6b00bf0f206b3bdb219e7b5`.

The private packet contains only `cases.json` and `labels.json` for
`nlu-calibration-v1` through `v6`. It excludes the sealed holdout and every
unspent calibration source.

## Transaction

1. Recheck `local-ai-lease status` is `ready`, LXC110 and the accepted
   `aster-llama.service` are active, and no backup, F2/F3 or maintenance task
   competes.
2. Copy the two exact packets to Proxmox, verify their hashes, push them into a
   new mode-0700 LXC110 temporary directory and extract with owner-only
   custody.
3. Run the candidate once with the existing local service credential remaining
   inside LXC110. The runner has a one-hour wall deadline and per-call timeout;
   it writes one mode-0600 result.
4. Retain only the content-free set digests, invalid-vote totals, nested fold
   statuses, thresholds/aggregate metrics when selected, elapsed time and
   terminal result digest.
5. Remove source, private packet, extracted cases/labels and raw result from
   LXC110, Proxmox and the Mac after reconciliation. Recheck production health,
   zero service restarts and lease state.

## Pass and stop rules

Pass requires all six outer folds to meet at least 60% decision coverage, at
most 10% accepted-decision error, zero unsafe false routes and zero routed
privacy underclassifications using thresholds selected without that outer set.
Any missing/changed hash, malformed response, engine failure, deadline,
uncertain output or failed fold stops qualification. There is no retry.

This transaction does **not** change or restart a model or service, create a
fresh calibration, access the sealed holdout, enable routing, grant tools,
start a lease, alter a schedule, or push Git.

