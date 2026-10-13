# Concrete full-path clock and partial-release recovery handoff

2026-10-12. Stream A; offline implementation, not live admission or deployment.
Jason directed continued coordination and all safe concurrent work without
another approval. Main and other projects' branches remain unchanged remotely.

## Exact receipt and accepted boundaries

Received Adaptive `30445d4572eb22c3700e18e5dc5edea087a7b85c`:

- `docs/projects/AI Projects/benchmarks/A1-v2-candidate-adapter-and-admission-2026-10-12.md`,
  SHA-256 `12c0dc6bff93e7cd785b88d44560f49775461e4da1f37274adab20a706578f50`.
- `docs/projects/AI Projects/benchmarks/A1-class-qualification-sample-policy-v0.md`,
  SHA-256 `8d2c29a135d863be121b6fe025548835814789bda52f4140c75e5984e0cc7b34`.

Accept for offline implementation the proposed owner-custody, one-attempt,
terminal-stop, bounded-token/time and content-free evidence interface. It is
not an accepted candidate endpoint or READY run card. Keep v2 in Mini custody,
new scenarios/labels separate, all failures, class-specific outcomes and the
already-agreed original-9B median/p95 ceiling. The human-adjudication requirement
is a qualification gate, not something code or supplied AI labels have met.
Protected-evidence backup and full-path live admission remain unverified.

Platform remains at `fc60e5a2c9eac8f311ce8e6c0a83b901fe55600b`; its controller
is still the earlier manual light adapter. This handoff does not claim owner
acceptance, deployment, new lease authority or a successful live recovery.

## Client clock implemented against actual owner format

Imported exact Adaptive sources:

- `scripts/aster-adaptive/aster_asgi_clock.py`,
  `e7f8240fc38a62772ac2d7e4e9461ee8f3be21580885d9dfc0cab40fe1919305`.
- `scripts/aster-adaptive/join_aster_clock.py`,
  `38318b894be89525be166a19ab1bd933966dfddf12ca060386ff0a2768fc694b`.

B60's `client_display_clock.py` supplies the owner-defined client record:
monotonic accepted-to-final-displayed elapsed time, exact observation ID and
HTTP status. A caller must mark actual display/failure; response arrival is
not silently counted as display. No transport, auth dependency override, UI
hook, prompt, answer, header dump or exception text is recorded. Missing server
ID stays missing and cannot join; no cross-process monotonic subtraction.

Nine tests exercise actual imported ASGI/join functions using a fake app:
successful response, displayed HTTP failure, interrupted stream, gateway
completion without client display, duplicate events, invalid identities and
backward clock. Useful-answer time remains null pending a bound review.
These verify wiring, not native Companion/display behavior or real latency.

Adaptive requested action: review this producer, integrate it into the isolated
synthetic test-client boundary and publish the exact admission/invocation card.
Keep native Companion authentication/bundle-drift work distinct: it is not
evidence that a headless synthetic Aster-path client is measured or admitted.
If native UI timing is required for a specific release bar, say so explicitly;
do not relabel a headless client or block all offline preparation on its UI.

## Partial-restoration algorithm supplied to platform owner

`lease_recovery_candidate.py` is an offline callback algorithm, not a live
controller or alternate lease. It accepts only the three original AI service
keys. It allows reentry from restoring, observes already-active services,
persists start intent before effects, and never retries an uncertain prior
start. It requires a separate exact restoration validator before marking the
record restoration_validated. It cannot clear a lock, acquire a lease, arm a
timer, execute commands, validate a GPU or grant authority by itself.

Eight fake-callback tests cover ordered intent-before-start, partial-restoration
reentry, unconfirmed GPU/service start refusal, lost reply followed by healthy
observation, failed device/exact validation, unknown targets, state-write failure
and validated reentry. Unit-active alone is not accepted production proof.
A durable intent followed by a crash before starting is deliberately uncertain:
fail closed and seek operational review rather than automatic GPU retries.

Platform requested action (Adaptive please relay through the established owner
chat): review/adapt this algorithm in the owned controller and publish the actual
receipt-bound admission, expiry/watchdog and command/recovery interface. Supply
independent deadline recovery before 04:15, News/other-consumer quiescence,
source-bound backup/mirror proof, sanitized bounded commands, exact accepted
SYCL/device/auth correctness validation and reviewed host-backed model staging.
Keep lease/lock until all owner-required postchecks pass. No firmware, reset,
reboot or new identity follows from this patch proposal. If another owned
implementation already supersedes it, publish that source/receipt instead.

## Validation and next action

Full local checks: 109 B60 inference, 31 runner/recovery, 14 Adaptive answer,
eight routing, five clock-join and three ASGI observation tests: 170 total.
Also imported the prior `b819787d` atomic status-write fix into the now-writable
full checkout, eliminating the previous checkout divergence for those two files.
Handoff tests are rerun with exact clock dependencies; counts differ because
the focused branch excludes unrelated local implementation history.

No real model call, live benchmark, lease, service/timer change, mount, download,
production configuration, credential or main push occurred. Old evening runner
must remain disabled. Next safe work consumes actual owner review/interfaces;
candidate staging/live comparison cannot be marked READY from fake tests.
