# October31 preparation — recognized pending-journal rollback

Extended the offline diagnostic transaction core with an explicit
`resolve_pending_rollback` operation. No production adapter/CLI, deployment,
lease, model/GPU call, timer, schedule or production configuration changed.
This continuation stayed offline apart from authoritative Git coordination.

## Implemented recovery case

Previously any retained `update.json.next` blocked further writes. The new
operation resolves only a complete, recognized pending journal with an
existing committed state. It independently rechecks the exact immutable
transition plan, schema, digest, permitted phase edge, recognized full source
map, verified checkpoint and strict idle proof. It then preserves the original
pending file by renaming it into a separate bounded archive and fsyncs the
directory before invoking **rollback only**. It never resumes apply or adopts
a pending `installed` phase as successful activation.

The preserved archive name includes the canonical pending-state digest and a
bounded0–31 slot. Existing evidence is not overwritten or deleted. Lost control
after the archive rename still leaves the committed state and checkpoint
available to ordinary rollback. The future adapter must hold the shared host
exclusion throughout; the core's journal lock alone is not host authority.

Malformed/truncated JSON, wrong checkpoint, impossible phase, unknown source
bytes, absent idle/checkpoint proof and full archive slots refuse without
moving the pending file or replacing source. If the initial checkpoint state
was never committed, its pending write remains for explicit pre-effect
reconciliation: the core cannot have replaced source before that initial
commit. No uncertain file is deleted to force a retry.

## Validation and exact dependency receipts

Implementation commit `5c8453192b1bb114fdad0b42f36162900bcd5edb` follows
`8b3e2c324` and the earlier pinned source-preflight/diagnostic dependencies.
Nine additional fake-effect/disposable-journal tests cover:

- recognized archive plus rollback;
- a fresh object resolving a pending write after the first source replacement's
  simulated process loss;
- truncated evidence retention;
- checkpoint/phase mismatch;
- idle denial and unknown source drift;
- uncommitted initial state retention;
- simulated loss after archive, then ordinary rollback;
- preservation of an existing archive;
- bounded archive exhaustion without losing pending evidence.

These simulate exception/process-loss boundaries with fake digest-map effects;
they do not qualify real host source replacement, true process kill, power loss
or an independent live recovery owner. No human/security review is invented.

Validation against exact independent replay:158 Lab Hours tests,10 dormant
installer tests and115 B60 tests pass, no skips. Implementation and replay tree
equal `4efe6e128585558f2ae6a3406b373c797ea744cd`.

- Core `scripts/local-ai/lab_hours_source_update.py` SHA-256:
  `8fbd3719ec7fb63fda0822220212128fe21c1e051fe200b3f555f439df3e9d38`.
- Portable patch
  `scripts/b60-inference/source-update-pending-20261031/0001-Preserve-recognized-pending-source-journals-before-r.patch`,
  SHA-256 `3db9db58384d53cb9829942b95ed2206b9bb5dd5b55146aee277c5c2d7cdc6f5`.

The core remains outside the installed30-file runtime closure. Installed
source/profile/guest-helper pins are untouched, and no new booking is armed.

## Next safe action and unchanged prerequisites

Implement the bounded host adapter: complete shared-exclusion and owner /
guardian / future-timer exclusion; protected checkpoint/candidate custody;
recognized atomic file replacement; safe import proof; bounded attempt identity
and recovery entry point. Exercise its real filesystem operations only against
disposable local targets first, including actual child-process termination and
all journal boundaries. Reconcile initial pre-effect pending records without
discarding evidence. Review the complete transaction before deployment.

Separately resolve the [cross-host backup clocks](backup-clock-hazard-20261101.md)
before a future source/date/booking-bound qualification. Neither this core nor
passing fake tests makes the backup chain or live restoration qualified.
Preserve accepted SYCL recovery,04:15 protection and old immutable records.
Never replay October30/31, automatically retry a device failure or claim the
27B+ reasoning/useful-answer latency milestone from preparation. No additional
per-model permission is being requested; these are unfinished technical gates.

## Authoritative receipt refresh

Fetched and read BOTH liaison and owning platform records. Adaptive remains
`d88f8239b6771836c3e56c59229db81a8c18ddd6`, registry
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`, booking owner
`5a9c3471398cfeecc0c6db35bfb264f87d8318f9`; their exact path/hash receipts
remain those in [the preceding core record](source-update-core-20261031.md).
No new peer reply or reading is inferred. B60 received commit
`7c72908ce57027cb51f64ce9f82e5c2e92c77421`, path
`docs/projects/B60-Inference-Engineering/source-update-core-20261031.md`,
SHA-256 `922563ef3277a3caa9df4d3eca3dd9b9ceead1045e26db1e81c49ab44cdfed4c`.
Publish sanitized artifacts only to the standing-authorized coordination branch
and verify the automatic GitHub protection mirror read-only. Programme active;
no new background executor or completion claim.
