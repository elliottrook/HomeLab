# D4 candidate-g 12:30 NO-GO and EPUB path correction — 2026-11-04

## Decision

The exact booking `aster-stream-a-sa3-envelope-20261104-1230` is **NO-GO** and
spent. It may not be retried. The dispatcher claimed it at exactly 12:30:00
America/Vancouver and the owner transaction began at 12:31:01, then stopped at
12:31:09 before drain, listener or model work.

The authoritative reservation is `failed` with result `NO_GO`. Its terminal
record reports first phase `owner-transaction`, failure code
`PRODUCTION_RESTORATION_INVALID` and `production_restored=false`. That final
code is a diagnostic false negative: the retained traceback shows the actual
first failure was the source preflight's stale EPUB health predicate, and the
same predicate was reused by the postcheck. No production drain occurred.

## Measured failure

The retained root-custodied traceback ends at:

`FullDrainSourceError: EPUB narration timer and worker are not healthy`

The installed source still expected a removed guest
`epub-narration-worker.timer`. Current production instead has an active and
enabled host `epub-narration-scheduler.timer`, an active and enabled guest
`epub-narration-monitor.timer`, and an idle worker service whose last result is
`success`.

The attempt contains no candidate result and owner stdout is empty. Independent
postchecks found no drain state, drain lock, operation lock, lab listener or
candidate process. The lease was `ready`; LXC 104, 110 and 116 were running;
Aster Agent, accepted llama/SYCL and Aster Speech were active. Production impact
was therefore none.

## Full-path correction

The first two-file correction fixed the source predicate but its first inactive
apply failed closed on an unordered multi-property systemd query and rolled
back. Platform commit `5b8c5e58` queries `ActiveState` and `Result` separately.
It installed inactive with exact source hash
`c07c2966a13144b8ca2b68639917381bad7381f9d8fa61adc265f1b30f59c5d9`
and manifest hash
`d92f9b34c500310fd3427955a0dc53b5965400067edde36639312d1cc14266d0`.

That postcheck exposed two more references to the retired timer before another
booking was created: the five-minute Lab Hours Doctor and the effectful
drain/restore command set. Platform commits `c9dc481b`, `a8d1650d` and
`a96cd26f` complete the architecture correction and its reversible installer.
The first revision-3 apply attempts changed no installed file; the partial
root-only checkpoint from the mixed-mode custody failure is retained. The
successful `r3b` apply installed exactly:

- `full_inference_lab_session.py` —
  `b3c38f030cbe1c0d45f59947cb2bc68cb7f80ed6410ef1669c88c18027296e9a`,
  root:root 0644;
- `lab_hours_doctor.py` —
  `32fbe1d9e63fdab78a00496c36ca4b3da7a81809e14cf930a209a32ec9649d76`,
  root:root 0755; and
- `lab_hours_release_manifest.json` —
  `b29f1e6c6f0a57622dd81a6274076234db22b141fa75bbbaeecfc6f641f41987`,
  root:root 0644.

The predecessor bytes are retained under root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-epub-scheduler-path-r3b-20261104`.
No service was restarted and no workload or model request ran during either
inactive installation.

## Independent acceptance

The focused source suite passes 48/48. Target validation proves:

- all three installed hashes and custody modes match;
- all 34 release pins load from the actual installed path;
- the Doctor returns `healthy` with zero codes;
- the canonical drain has six effects and restore has eleven effects, with no
  reference to `epub-narration-worker.timer`;
- worker restoration is left to the active booking-aware host scheduler rather
  than starting unbooked EPUB work directly;
- the lease is `ready` and shared state/locks are absent; and
- LXC 104/110/116, Aster Agent, accepted llama/SYCL, Speech, the EPUB scheduler,
  Proxmox daemons, dispatcher timer and Doctor timer are healthy.

This closes the deterministic EPUB path defect. It does not convert the spent
12:30 attempt into a pass or promote candidate-g.

