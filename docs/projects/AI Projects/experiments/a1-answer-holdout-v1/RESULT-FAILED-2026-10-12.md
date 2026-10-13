# A1 fictional answer holdout v1 — capture failure

**Decision:** No answer-quality or latency score exists. Do not replay v1 as a
fresh holdout. A new sealed corpus and a storage preflight are required. No
routing, permissions, model, service or infrastructure configuration changed.

At approximately 16:58 America/Vancouver on 2026-10-12, Stream A sent the
20-case candidate-visible fictional bundle through the accepted local
reasoning-off 9B/SYCL service. The platform owner had confirmed its separate
SA3 run ended and its lease was released. Stream A's live checks found the
lease state/lock absent, service active, accepted unit/binary/model hashes,
`/health` OK, zero processing/deferred requests, no sampled active Proxmox
task and no named backup process. The [run card](RUN-CARD-DRAFT-2026-10-12.md)
pins the case, profile, runner and bounds.

The remote call returned a syntactically valid 20-row capture envelope within
26 seconds. The transport then failed at the local final write: the Mac
sandbox denied creation of
`~/Library/Application Support/Aster-Stream-A-Evidence/answer-holdout-run-20261012-001`
with `PermissionError: Operation not permitted`. The raw fictional answers
existed only transiently in the transport process and were **not retained**.
The 20 rows may include completed, failed or unattempted cases; their statuses
cannot now be recovered. No answer text, API key or hidden label was printed
or committed. The separate hidden key stayed on the Mac and was not sent to
the backend. No scorer or reviewer saw model output.

This is a failed **evidence-custody** attempt, not evidence for or against 9B
answer quality. It consumes v1's freshness for this backend: retrying the
same questions would create a contaminated comparison and violate the
one-attempt run card. The v1 case/key/review digests remain as provenance only.

Immediate postchecks found the lease state/lock absent, LXC 110's
`aster-llama.service` active with the same PID 10445 and zero restarts,
`/health` OK, and both processing/deferred queues zero. There was no service
rollback to perform.

The transport now reserves its local output directory and proves a 0600 file
write **before** any remote call; an inaccessible path fails before the model
is contacted. It also seals raw transport stdout before parsing it, including
partial output on timeout, with a private `/private/tmp` fallback if the
reserved write unexpectedly fails. Focused tests cover the preflight and
pre-parse seal. A fresh v2 corpus needs
separate content review, protected custody, new profile/case digest, and a
new live admission window. The next run must use an owner-only writable parent
under `/private/tmp`, then copy evidence into longer-lived protected custody
after the captured file is sealed. Backup remains UNKNOWN.
