# S1 collection activation checkpoint

Date: 2026-09-26

Status: **AUTHORIZED AND EMPTY; COLLECTION CLOCK NOT STARTED**

Jason instructed “Approve push and continue.” The approved Stream A branch was
pushed to Forgejo, and both Forgejo and the GitHub protection mirror reported
`a769867e5187b30e3b8ed52613119708bab29566` for
`codex/aster-m2-reconcile-20260925`.

The instruction also approved the concrete collection window in
`COLLECTION-GATE.md`. Before activation, the packet manifest SHA-256
`93b9671b4a7c8e216fec00c1351499441e6e08a1aed50f765566645f3a578911`
and all eight artifact hashes were recomputed successfully.

Read-only custody revalidation found:

- proposed scratch path absent and outside all four named repositories;
- current `$TMPDIR` parent reported Time Machine excluded;
- Spotlight server reported disabled; and
- no reviewed Aster agent/operations/mirror configuration named the resolved path.

The single authorized directory was then created at the current per-user temporary
path with mode `0700`. Its `bundle.json` has mode `0600`, 619 bytes and SHA-256
`3ad58d8f775527a06dc7e045fffd88e1ba5e113ed3e71ad6813ecd763f5199aa`,
exactly matching the approved empty template. The syntax validator reports zero
cases, zero receipts, `structurally_ready=false`, and all authority/confidence/
identity/privacy claims false.

No case, label, acceptance, active-effort claim or collection/review timestamp was
created. The 30-day, seven-day and 30/90-day clocks begin only when Jason supplies
the first request. Evaluation, services, model calls, routing predictions,
production changes and further push remain excluded.

Next action: collect request text before showing or discussing labels, beginning
with up to five sanitized timer/alarm requests authored by Jason.

## 2026-09-28 — first accepted batch

Jason supplied and accepted five sanitized timer/alarm requests, then completed a
human-authored label review in a local workbook. He self-reported ten active
labeling minutes and explicitly approved durable local-Git retention. The accepted
records and exact hash-bound receipts are in
[`accepted/2026-09-28-timer-batch.json`](accepted/2026-09-28-timer-batch.json).

The syntax-only validator accepted all five cases and receipts against the frozen
plan and registry hashes. The partial batch has five timer strata and five
composition cases, but zero adverse-constraint cases; it is consequently not a
complete S1 corpus and cannot authorize evaluation, deployment, routing, policy or
credential changes. The collection clock began at `2026-09-27T04:21:34Z`; its
draft expiry and 30/90-day review timestamps remain recorded in the bundle.
