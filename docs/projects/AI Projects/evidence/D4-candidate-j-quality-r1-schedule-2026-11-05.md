# D4 Candidate-J quality R1 schedule — 2026-11-05

## Result

Candidate-J's distinct untouched-quality transaction is scheduled under the
authoritative Lab Hours ledger:

- booking `aster-stream-a-sa3-candidate-j-quality-20261105-1016-r1`;
- owner/workload `aster-stream-a` /
  `sa3-evidence-matrix-candidate-j-quality-v1`;
- window 10:16–11:16 PST (`-07:00`), start epoch `1793898960`, end epoch
  `1793902560`;
- state `scheduled`, with the required 900-second restoration reserve.

The first proposed 08:30 window conflicted with the existing TTS experiment.
That booking owns 08:30–10:00 and its recovery reserve protects the stack
through 10:15. The authoritative check returned the complete 10:16–11:16
window clear before the Candidate-J reservation was created. No existing work
was cancelled, shortened or overlapped.

## Static evidence

The installed release remains
`aster-tts-dual-cpu-screen-plus-candidate-j-quality-v1`; all 46 manifest pins
reread exactly. The Candidate-J quality workload is registered and admitted.
LXC104/110/116 are running; Aster Agent, accepted llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` are active. Dispatcher and Doctor timers are
enabled and active and both last service results are success/exit zero. No
restart or model/backend change occurred.

## Remaining fresh gates

The dispatcher owns the once-only claim. At 10:16 it must recheck the exact
reservation and installed pins, acquire the whole-host lease and shared
operation lock, verify the quiet-host and production baselines, and retain a
bounded terminal result. Success requires exactly 20 rows, 14 model requests,
six no-transport abstentions, zero retries/errors/effects, restored production,
no residual Candidate-J state/process/locks and healthy postchecks. Any failed,
late, changed or uncertain gate is a terminal NO-GO without retry.

Blind review and any promotion decision remain downstream of a complete
transaction. This schedule grants no route, tool authority, restart,
model/backend change or automatic promotion.

## Offline terminal reconciliation

The post-run reconciler is now source-complete before the booking fires. It
accepts only the exact complete terminal schema, this fixed workload, 20
processed cases, restored production and the already-frozen deterministic
quality gate. It returns only bounded counts and digests, omits model identity
and case content, and can advance a passing result only to the existing
three-reviewer model-blind review. It explicitly records promotion as
unauthorized. Candidate-J's complete focused suite passes 43/43, including
terminal drift and quality-regression fail-closed tests.

The model-blind review handoff is also automated before execution. It accepts
only the complete frozen result shape, emits the bound 20-case review packet
and empty review template, requires three distinct reviewers, and excludes the
result's model/backend identity. Incomplete output fails closed. With this
handoff included, the complete Candidate-J suite passes 45/45.

The frozen decision now also has a file-oriented runner. It requires exactly
three review files before reading any input, delegates all schema, identity and
conservative-intersection checks to the frozen decision, emits only the bounded
content-free decision and keeps promotion explicitly unauthorized. The full
Candidate-J suite passes 47/47.

A passing decision can now be converted into a bounded owner-review release
candidate without granting an effect. The builder requires the exact passing
20-case/three-reviewer decision, all six abstentions and zero false-completion
failures. Its output recommends only acceptance as the D4 investigation
release candidate and names bounded SA4 repair-class design as the next
milestone; owner decision remains required and deployment, authority, routing
and promotion remain false. The full Candidate-J suite passes 49/49.

## Intervening TTS transaction check

The separate 08:30 TTS booking claimed exactly but ended `NO_GO` after 96
seconds. Stream A did not retry, shorten or repair that other owner's workload.
Its restoration boundary passed: the lease is ready, lease/state/operation
locks are absent, Doctor and dispatcher last results are success, and
`pvescheduler`/`pvestatd` are active. Aster Agent, accepted llama.cpp/SYCL and
Speech are active. The installed combined release still reads as
`aster-tts-dual-cpu-screen-plus-candidate-j-quality-v1` with 46/46 exact pins.
Candidate-J therefore remains scheduled at its original 10:16 time; the
earlier protected window and recovery reserve are not reused.

## Clean-archive release check

The exact mirrored Stream A source was exported from Git into a fresh temporary
tree with no working-copy files. All 49 Candidate-J contract, runtime,
reconciliation, blind-review, decision and release-candidate tests passed in
that clean archive. This rules out an untracked-file dependency in the
post-run path before the booked transaction.

The broader dependency-free `test_sa3_*.py` regression also passes 250/250.
A raw full-suite discovery under the Mac system Python is not accepted as a
release result: it ran 233 tests but could not import 11 service-dependent
modules because that interpreter lacks `jwt`, `fastapi` and `cryptography`.
No ad-hoc dependency installation was performed. The missing interpreter
dependencies do not weaken the clean-archive Candidate-J or SA3 results and
are not represented as a production or candidate failure.

One joined synthetic pipeline test now crosses the exact runtime result,
terminal reconciliation, blind handoff, three complete review files,
conservative decision and bounded owner-review release packet. It reaches only
`ready-for-owner-D4-release-review`, retains authority `none` and routing
`off`, excludes model identity and leaves deployment false. The complete
Candidate-J suite therefore passes 50/50 end to end before the live result.

## Independent release-path audit and correction

An independent agent audit found two pre-run release-chain gaps. The scorer
accepted fewer prediction invariants than the blind handoff, and the owner
release packet consumed the quality decision without binding the exact booked
terminal reconciliation. Both are corrected before the live result exists.

One shared strict result contract now validates every prediction field,
transport/abstention count, deterministic prose source, model binding, finite
latency and zero-error/effect boundary for both scoring and review. Duplicate
JSON keys fail closed in the file-oriented reconciliation, handoff, decision
and release paths. The reconciliation now hashes the exact retained terminal
and result file bytes. The owner release packet requires that reconciliation,
binds its booking ID and digest, and requires the same canonical result digest
as the three-reviewer decision. Review and artifact digests must be canonical
64-hex values and the three review-response digests must be distinct.

Reviewer names must be canonical non-whitespace strings. The decision now
states the accurate assurance level:
`separate-execution-not-authenticated-custody`. Candidate-J review uses three
separately invoked model-blind review passes; it does not claim the stronger
externally authenticated custody required by private M3 corpus governance.
The corrected complete Candidate-J suite passes 52/52.
