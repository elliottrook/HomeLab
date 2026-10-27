# SA2 Doctor-status producer install card — 2026-10-27

Status: **prepared and independently reviewed; not executed**

This rollback installer applies only the three files in the reviewed
`sa2-fixed-doctor-status-producer-20261027` manifest. It accepts no arguments,
uses a fixed staging path, requires all recorded predecessor hashes and private
root custody, and checkpoints every predecessor before staging a candidate.

## Exact installer

- installer SHA-256:
  `37e334e7be2a7e4ffc61f824b8b2e337c9b2aac55033ae5a1494a896bea48b68`;
- installer test SHA-256:
  `413b571c55782c7f65b54c4eaf61f515bdc88a2c050da19dac6f738b04b8ba53`;
- reviewed manifest SHA-256:
  `d65cab046facf2dde8c985d15401362b8333ea98c35a058114622f488672c641`.

## Effect and rollback

After a packet-first target-Python import check, the installer atomically
replaces the Doctor adapter, incident store and registered-producer module. It
restarts only `aster-agent.service`, requires fixed health, zero restart
failures, unauthenticated API denial and exact installed hashes. On failure it
restores all three root-only checkpoints, restarts only Aster Agent and waits
for health. The checkpoint is retained after success.

## Validation and gates

- shell syntax: **pass**;
- focused installer tests: **4/4 passed**;
- manifest plus installer suite: **7/7 passed**;
- independent installer source review: **PASS**.

Execution remains blocked until the protected F2/F3/full-Aster window is over,
the three live predecessors are re-read, target-Python tests pass from the
exact packet, and Jason approves the Aster Agent restart. No llama/model
restart or change, model call, automatic routing, Doctor refresh, schedule
change or repair authority is included.

