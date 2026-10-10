# S0 pilot batch 1 — manual acceptance

Jason replied **“Approve”** directly to the ten-item review packet asking for a
content and proposed-label decision for each item. All ten revision-1 families
are accepted as personalized human-reviewed S0 train/dev examples. Six train,
four dev; no test or calibration examples. Authorship remains AI-proposed.

`reviewed-proposal.json` preserves the exact reviewed bytes, including historical
pending flags. `acceptance.json` records the later decision separately and binds
both the whole artifact and each case revision by SHA256. Pending flags in the
original do not override the later acceptance receipt. The receipt is an agent
record of the direct user message, not a cryptographic human signature or proof
of independent correctness. No cases were edited after approval.

All ten content/label decisions accepted; zero unresolved review decisions out
of ten. The intentionally ambiguous tenth request is accepted with a clarify
label; that is not an unresolved annotation. No user timing was reported, so
median labeling time is UNKNOWN and the two-minute effort gate has not passed.
Pause the next batch pending effort information; do not infer time from messages.

No router/model evaluation, execution, deployment or permission change occurred.
This manual record is not passed through the fixture-only validator and is not
represented as authenticated by it. That validator and its authority-false outputs
remain unchanged. Future machine consumption needs separately reviewed validation
and an authorized experiment; this file is a manual evidence artifact only.

Accepted sanitized records have durable Git retention under the approved pilot;
withdrawal stops use but cannot promise removal from history, mirrors or backups.
No push is authorized. No real calendar, preferences, hosts or public pages were
queried. The next step is checking reported effort before batch 2 preparation.

## Subsequent effort report

Jason answered “5” to the question asking for approximate active review minutes
for all ten cases. The separate `effort.json` records five minutes total and an
approximate derived 30-second average. Individual durations and actual median
remain unmeasured. Conditional on a 300-second nonnegative total, the ten-case
median cannot exceed 50 seconds (six equal 50-second observations maximize it).
This clears the two-minute stop threshold on self-reported aggregate evidence,
not instrumented timing. Zero unresolved review decisions also clears that gate.
Batch 2 may be proposed; no approval of its content or labels is inferred.
