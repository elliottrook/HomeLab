# A1 review handoff and Aster response-clock feasibility

**State:** Offline development checkpoint, 2026-10-12. No production gateway,
native Companion, B60 model, route, tool, credential, lease or policy changed.

## Private six-case review handoff

`scripts/aster-adaptive/prepare_answer_review_packet.py` validates that the
content-free capture reproduces the original synthetic attempts exactly,
then writes a reviewer packet and blank score template outside Git. The
packet contains the public fictional request/context/rubric and the private
synthetic answer. It omits backend identity. The blank template is tied to
the exact capture SHA-256 and contains `null` labels, so the scorer cannot
mistake it for a completed review. The script refuses to overwrite an output
directory and refuses an output inside this repository.

The first run created `/private/tmp/a1-review-packet-20261012` with directory
mode 0700 and two files mode 0600. Packet SHA-256 is
`caae334ced71d0d7b9e064271508559b6574109e6a747fb0cd31d81739e53c69`;
blank template SHA-256 is
`58f77b5bcc458008d23cf30336bfe758eef2e1fa62271566bf214af44732b862`.
It contains all six development cases and no real personal context. Raw
answers and reviewer labels are **not** in Git. Three offline tests pass for
capture binding, omission of explicit backend identity, private modes and
no-overwrite behavior.

This packet was preparation for a separate AI reviewer. The case author had
already seen the answers and the six cases were exposed. Backend-blind
presentation alone cannot convert this into a qualifying holdout. Retain the
nonblind calendar finding as a development regression lead only.

**Separate AI reviewer exercise:** A fresh-history sub-agent in this same
Codex window saw only the packet and blank template, not the backend identity
or prior result analysis. It wrote six item-by-item judgments privately at
`/private/tmp/a1-review-judgment-20261012/judgment.json` (mode 0600), SHA-256
`933b55fb4fd95a595e457a37b0c0c1d62832d832a24e795303ef60cf7c1af304`.
The scorer accepted the digest-bound labels and reports 2/6 all-rubric
development passes: fictional fact and ambiguous-control pass; calendar,
mixed public/private and both HomeLab-status cases fail at least one item.
No prohibited-claim flag was marked. The reviewer reported no unresolved
uncertainty. Private rationale remains outside Git. This is **AI review, not
human adjudication**, and the cases were already exposed. It cannot supply a
qualification success rate, per-class reliability estimate, or promotion
floor. The scorer's `human_review` field remains an unverified provenance
claim, not a fact established by the JSON shape.

## Aster accepted-request clock feasibility

`scripts/aster-adaptive/aster_asgi_clock.py` wraps only Aster's
`/v1/chat/completions` ASGI path. It records monotonic app-entry-to-first-body
and app-entry-to-final-body times, HTTP status and whether a terminal body
was observed. It records no request, response, token, header or exception
text. In-process tests use the repository Aster gateway with a fake delayed
backend and a test-only authentication dependency override; they exercise a
normal response, a 502 failure, the Companion streaming branch and an
interrupted stream. All four pass. The 30 ms fake wait appears in the
terminal measure, including the HTTP failure; streaming completion is not
mistaken for its first body. The interrupted stream retains first-body time
but has `terminal_ms: null` and `terminal_observed: false`.

This is a **clock wiring test**, not a measured baseline. ASGI entry is later
than native-app input and earlier than network delivery; the wrapper does not
include native UI, TLS, authentication gateway, LAN, actual retrieval, real
inference or human usefulness review. It is not installed in production.
The next full-path design must join an Aster request ID, client-side accepted
and displayed times, sanitized gateway route/context/inference phases and a
reviewed useful-result label without logging prompt/answer text. Missing
phases remain `null`. An interrupted stream has no terminal completion and
is censored, not assigned a fabricated latency.

**Offline correlation extension, 2026-10-12:** the uninstalled ASGI wrapper
now assigns a random opaque 32-hex observation ID, replaces any same-named
response header with that ID, and records it beside content-free first/final
body timing. A pure [clock join](../../../../scripts/aster-adaptive/join_aster_clock.py)
accepts only matching allowlisted client and gateway records. It preserves
each side's observed duration without subtracting clocks from different
processes, keeps an interrupted response censored, and leaves useful-answer
time `null` until a separate review label exists. Three dependency-free ASGI
tests and five join tests pass. The FastAPI/httpx integration test source
compiles, but it could not run on this Mac because `httpx` is not installed;
no dependency was installed for this checkpoint. A real client clock producer
and live Aster/Companion test remain absent, so this is correlation wiring,
not an end-to-end latency baseline.

## Admission and ownership for subsequent live measurements

| Lane | Present state | Entry gate |
|---|---|---|
| Offline capture/review/clock tests | Done on synthetic input. | Local tests and source pins. |
| Accepted 9B shared-service development probe | One six-case direct inference run done; platform's separate holdout is currently active. | Verify no host lease, backup or other model run; bound requests; use only fictional input; postcheck service. Do not contend with the active holdout. |
| Aster-path current-control baseline | Not yet run. | First freeze an isolated test-only admission or a small shared-service card that does not drain/restart LXC104, preserves ordinary consumers, binds the actual runtime, and specifies request/response custody. A local fake-backend clock test is insufficient. |
| Exclusive candidate comparison | Not ready. | Platform owner verifies receipt-bound whole-host lease, News/backup exclusion, independent deadline restore and exact production postcheck. B60 owns stack staging and candidate pins; Aster owns cases, labels and route decision. Clock time alone grants no slot. |

The platform project is separately preparing a 20-case **sysadmin** holdout.
It must not be treated as this assistant-answer corpus or copied into Aster's
development prompts. Its custody and scoring roles belong to that project.
