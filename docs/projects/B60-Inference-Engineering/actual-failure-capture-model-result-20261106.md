# Actual 35B failure-capture trial — 2026-11-06

Booking `b60-exclusive-20261106-day-r4` ran the unchanged Qwen3.6-35B-A3B Q4_K_M diagnostic with reasoning enabled under accepted SYCL. The production failure-capture integration retained both request records before `MODEL_REQUEST_FAILED`.

| Fixed request | Actual result | Elapsed including reasoning | Completion tokens | Final characters |
| --- | --- | --- | --- | --- |
|1|`stop`; exact arithmetic predicate passed|11.333s|514|2|
|2|`length`;1,024-token cap; no final answer|18.711s|1,024|0|

The second request is incomplete. Its elapsed time is not usable-answer latency, and this diagnostic establishes neither grounded-capability improvement nor fresh9B p50/p95 parity. No request was retried. Reasoning token counts were unavailable and remain null; hidden reasoning and answer text were not exported.

Actual residency proved41/41 layers offloaded,20,065,232KiB VRAM,65,512KiB GTT and725,624KiB process RSS. Model SHA256 `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7` and accepted runtime/settings were unchanged.

Exact bounded result-packet SHA256: `fa4d32085cbd1cca2a2b5208ee7c1cf3e441e06d0030844a576fb8796a57a57e`. The subsequent model-failure record SHA256 is `164ff86bba33ef21212ca2532a636a83ba280c0ed430749084338e252921779c`.

## Restoration reconciliation

The owner exited during restoration, followed by the independent guardian. The accepted backend had started18:17:07 and stopped cleanly18:19:31; fresh accepted binary/unit/model hashes matched and no new device/OOM fault occurred. The first failure coincided with a normal seven-second Paperless future job, consistent with a strict transient-state verification race. The guardian's structured exit was RuntimeError; the source and clean-stop evidence are consistent with the once-only start latch refusing its restart after re-fencing. These are evidence-supported causes; raw logs do not establish every internal call.

One independently reviewed, exact-binding **assisted recovery** restored and released the entry18:34:44, before18:55. It retained the old start/failure evidence, allowed one separately bounded accepted-backend recovery start after the proven successful stop, retried no model request and accepted only the unchanged strict restoration predicates. This is **not an unattended restoration pass**.

The parent full postcheck SHA256 is `748b95ec3601a093dd72a7ba633f9afed7eed8949d8dcfa3aad18a3b1e5123f1`. The independent full postcheck SHA256 is `fdf1609bb89a75de361cf3c5b767f3ec32946022f6220e313bf6c3f5fb2fbb52`. Both verify all five checkpoints,15 service/timer states, finite future schedules, empty client/candidate scopes, restored namespace/target/custody, preserved News mount, sole accepted GPU holder and metadata auth probe, clean kernel through restoration and released shared exclusion. Exact assisted terminal SHA256: `d7efe9aa1a9be1d14a79ee079d9a4179eb8d14bfb6073fa4f216191952ed7779`.

## Necessary correction and next actual gate

The new correction retains the one-start limit. During guardian rescue it may preserve an already-restored backend only after proving exact private files/artifacts/active process, unit state, sole GPU holder, metadata health and clean kernel; it fences every other declared consumer and proves unchanged PID/start identity afterward. Strict unit verification gains only a bounded read-only wait for natural scheduled-job completion. Unknown or failed prior starts still refuse.

A distinct fixed restore-only qualification is being prepared for owner loss **after** the first healthy accepted-backend restart. It makes no model-generation request and does not imply all crash windows are qualified. Capacity19:00–19:30/recovery19:45 is reserved but unarmed; fresh archive integrity and final independent installed review remain mandatory. The first archive preparation refused its insufficient outer budget before scanning; a separate evidence attempt now retains the full declared scan bounds. No stale proof, reduced scan bound or missed clock may be accepted to meet the target time.
