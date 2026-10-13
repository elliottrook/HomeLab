# Aster assistant-answer holdout admission v0

**Status:** Preparation standard, 2026-10-12. It does not authorize model
calls, connected tools, a lab lease or routing promotion. The separate
platform project's 20-case sysadmin holdout has different scope and custody;
its labels must not be copied into this assistant-answer corpus.

## Purpose and separation

The exposed six-case A1 set is a development regression. A fresh set must
test assistant answer quality across household, knowledge, calendar, web,
personal-context and diagnostic requests without revealing labels to a
candidate backend. The case author/custodian, content reviewer, execution
operator and adjudicator/scorer should be distinct roles where practical.
An AI-only role separation is useful for contamination control but is not
human validation; preserve that limitation in every score and promotion
packet. No one with candidate-tuning access may see the hidden labels before
the candidate profile and run plan are frozen.

## Required case fields and checks

Every synthetic case needs an opaque ID, request family, fictional user
request, frozen evaluation clock, permitted synthetic source records with
source IDs and observation times, explicit privacy/locality class, permitted
capabilities, maximum tool scope, correct outcome category and itemized
observable rubric/prohibited claims. Answer keys and reviewer notes live in a
separate restricted artifact from label-free execution input. A case must
have enough evidence to make its expected outcome falsifiable; insufficient-
evidence cases must explicitly expect clarification or abstention, not a
guessed answer. Calendar cases need normalized time/zone facts; frozen web
cases need dated source text; HomeLab cases must distinguish a saved report
from current live state. No real calendar, address, credential, host secret,
raw log, or repair command belongs in the corpus.

Before release, validate unique IDs, class counts, outcome-category counts,
source time bounds, answer-key alignment, privacy review and material
non-overlap with exposed development cases. Record a content-free digest of
the exact label-free bundle and separate label bundle, reviewer receipt,
schema/scorer source revisions, and a release decision. Freeze case order
and random seed before a backend is selected. Any correction after release
creates a new version and invalidates comparisons that used the old bundle.

## Run boundary and storage

An owner-only `/private/tmp` bundle can support initial offline validation,
but it is **ephemeral**. A qualifying run needs a durable protected storage
location and a recoverable, access-limited custody plan before invocation.
Do not put answer text, hidden labels, real interactions or secret-bearing
hashes in Git. Git may hold only content-free manifest, schema, reviewer
receipt and outcome summary. If the protected bundle disappears or its digest
changes, the run is not reproducible and cannot qualify a route.

The first development invocation, if admitted, uses one frozen accepted-9B
profile, one attempt per case, no connected tools, bounded tokens/time and
source-local authentication; it does not use the candidate's own self-grade.
Run only after any other B60 experiment/SA3 holdout has finished and the
shared-service or exclusive lease gate is rechecked live. A direct inference
API run tests a narrower path than the native Aster assistant. A full-path
comparison requires isolated test-only Aster admission and clock/custody
binding; do not relabel direct-backend latency as a user-facing budget.

After execution, seal the raw response digest before labels are released to
the scorer. Preserve failures, abstentions, timeouts and retries as separate
outcomes. Report by class with uncertainty; a 20-case corpus is useful for
finding errors, not estimating rare-event safety or stable p95. A second
fresh set or later real opt-in interactions would be needed for stronger
release evidence. No score automatically grants tools or bypasses policy.

## Current admission state

The fictional assistant-answer v1 bundle now has 20 cases, two in each of ten
request families. It has ten useful-answer, eight justified-abstention and
two correct-denial labels; eight cases impose private-context locality
constraints. The case custodian and a separate AI content reviewer worked in
this Codex window. The reviewer accepted 20/20 and found zero material
request/context overlaps against the six exposed development cases across
120 comparisons. This is **AI-authored and AI-reviewed**, not human-labelled
qualification. A later reviewer must still examine the actual run outputs.

The bundle and review receipts were copied from owner-only `/private/tmp` to
an owner-only local Application Support directory, with files mode 0600 and
directories mode 0700. `validate_answer_holdout.py` confirmed the copied
case/key order, counts, permissions and manifest digests. The content-free
[release record](answer-holdout-release-v1-2026-10-12.md) pins each exact file
without publishing hidden questions or labels. **Recoverable backup is
UNKNOWN**; the local copy improves durability but does not establish backup
or independence from this Mac. The candidate must receive only `cases.jsonl`,
never `answer-key.jsonl` or reviewer receipts.

The v1 bundle was sent once to accepted 9B, but the local write failed after
the remote response. No score is available and v1 must not be replayed as a
fresh holdout. The [failure record](../experiments/a1-answer-holdout-v1/RESULT-FAILED-2026-10-12.md)
keeps that evidence-custody error explicit. A new v2 bundle is required.
The [fresh v2 bundle](answer-holdout-release-v2-2026-10-12.md) is now sealed
and separately AI-reviewed, with case-specific privacy constraints. Its
exact 9B profile, source pins and [bounded run card](../experiments/a1-answer-holdout-v2/RUN-CARD-2026-10-12.md)
are prepared. It is **BLOCKED for a model call** until a fresh host
occupancy/lease, backup and reservation check admits a safe slot. Independent
output adjudication is still pending because no v2 output exists. A direct
backend development run cannot qualify native Aster-path latency. This gate
remains separate from SA3 sysadmin evaluation.
