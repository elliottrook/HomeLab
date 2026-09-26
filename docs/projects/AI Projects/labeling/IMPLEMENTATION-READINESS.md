# M3 S0 pilot implementation readiness proposal

Status: **proposal only**. The [protocol design](approvals/2026-09-25-protocol-design.md)
was accepted; intake implementation and case collection remain unapproved.
Owner: Jason. Scope: at most 30 sanitized, authored S0 train/dev families.
No real interactions, private facts, cloud/model calls or tool execution.

## Recommended scope and alternatives

**R — repository-native S0 pilot** is recommended. Reuse local Markdown/JSON forms,
a stdlib validator and Git. No service, new account, database, network listener or
additional machine. Jason authors or explicitly approves each case and supplies
its labels through a local review step. Reviewed S0 cases, labels, corrections,
effort metadata and negative results can be versioned in Git. Git history is
durable and mirrored; it is unsuitable for secrets or private facts. Unreviewed
or rejected drafts stay outside Git and are discarded after human review.

Paper-only remains an optional personal preference, not a privacy requirement for
sanitized S0 data. It cannot support machine evaluation without later import.
A separate human-only OS workspace is relevant to the later hidden test corpus,
not necessary for this exposed train/dev pilot. A branch alone provides neither
confidentiality nor independent custody. M4 checkpoint custody remains separate.

## Proposed exact records

These schemas describe future implementation; no populated record or helper is
created by this proposal. Unknown fields/types reject rather than default.

Common fields: `schema_version` (exact literal), `record_id` (unique opaque lower-case
ASCII ID, 1–64 characters), `protocol_ref` (approved commit plus SHA256), `pilot_id`,
`case_id`, `family_id`, `created_at` (ISO8601 with offset), `actor_ref`,
`supersedes_id` (same-type ID or null), `retention_class=s0-reviewed-git-v1`.
No identifying data in IDs. Pilot-level records may use null case/family IDs.

| Type | Required fields and constraints |
|---|---|
| `s0.case.v1` | `revision` integer ≥1; `stratum` from approved ten classes; `request_text` ≤512 characters; `context_text` ≤1,024 characters; `origin=human-authored-s0` or `human-approved-s0`; `split=train|dev`; no actual or disguised personal facts, logs, secrets or identifiers |
| `s0.content-review.v1` | Exact case revision/hash; reviewer reference; explicit booleans for no copied real context, no identifying details, no secrets, wholly authored synthetic content; `decision=accept|reject|uncertain`; four true plus accept required |
| `s0.label.v1` | Exact case/content-review references; labeler; `pass=A|B`; disjoint required/optional/prohibited sets; acceptable statuses; sensitivity; cloud eligibility; uncertainty code; integer labeling seconds ≥0 |
| `s0.adjudication.v1` | A/B references (B nullable); adjudicator; `decision=accept-personalized|accept-dual-reviewed|unresolved|exclude`; final label reference or null; disagreement codes; preserve original accepted labels |
| `s0.freeze.v1` | Case revision/hash, final label hash, family ID, train/dev assignment, protocol hash, acceptance reference; family cannot cross splits |
| `s0.audit.v1` | Sequential event ID; actor; timestamp; prior event; affected references; transition and reason code; append corrections, never erase a negative result |

Capabilities and allowed outcomes use the approved protocol taxonomy verbatim.
Calendar/private context/local join imply personal/local-only **routing labels**
even though the example content itself must be sanitized S0. Lab/sysadmin labels
remain at least internal/local-only. Mandatory prohibited capabilities remain
shell, credentials, automatic approval and cloud private export. Optional sensitive
capabilities inherit the same privacy restrictions as required ones.

Uncertainty codes: missing-context, ambiguous-intent, capability-boundary,
privacy-class, unavailable-capability, factual-dispute, label-conflict, effort-limit,
other-unresolved. Raw private explanations are forbidden, including audit notes.

## Human identity, authority and provenance

Jason is the pilot owner, reviewer and labeler. His explicit local review decision
must bind the exact displayed content and label revision; a typed actor field or
an AI-generated `human_verified` flag cannot substitute. Proposed receipt fields:
artifact SHA256, decision, review channel, date, source-message/reference and
`evidence_class=personalized-human-review`. Actual receipt handling must be reviewed
and tested when implementation is authorized. No cryptographic authentication or
independent reviewer identity is claimed from chat text, Git authorship or file UID.

The agent may prepare approved tooling, but cannot accept its own examples as human
labels. Single-human pilot labels measure personalized intent, not independent
correctness. B stays null unless another consenting human actually reviews blindly.
Every later main-study test family still requires the approved independent review.
No new identity, signing key, token or credential is required for R.

## State machine

1. **DESIGN_ACCEPTED** — current state; no implementation or collection authority.
2. **IMPLEMENTATION_APPROVED** — bounded forms/validator implementation and tests only;
   no case creation or collection from this approval alone.
3. **COLLECTION_APPROVED** — separately authorized cap of 30 sanitized train/dev
   families, named human reviewer, dates and explicit durable Git retention acceptance.
4. **DRAFT_LOCAL** — content outside Git, staging, automated upload and indexing.
5. **CONTENT_ACCEPTED** — Jason explicitly reviews the exact revision; uncertain or
   rejected drafts cannot become retained records or be offered to a model.
6. **LABELED / ADJUDICATED** — human supplies labels; unresolved outcomes are counted.
7. **FROZEN_DEV** — exact reviewed artifacts and provenance versioned for train/dev;
   later corrections create a new revision and invalidate the previous freeze.
8. **CLOSED / EXCLUDED** — close pilot or exclude records from use without silently
   rewriting history or hiding negative results.

No evaluation, model call, production execution or policy change is authorized by
any transition above. Publication follows the separate repository push rule.
Main-study calibration/test freeze is not part of this pilot.

## Storage, permissions and retention

Proposed accepted path: `docs/projects/AI Projects/labeling/pilot-s0/` in the existing
local repository. No new privileges or service permissions. Current agent/writer
access is expected; these are exposed train/dev artifacts, not a secret holdout.
No case directory or data is created by this design.

Drafts: existing local temporary workspace, outside Git, no automated export or
collection. Proposed maximum lifetime **7 days**, or deletion immediately after
rejection/review completion; accepted copies must be content-reviewed first. Actual
scratch path, local backup/indexing behavior and discard method must be verified
before collection. Do not promise secure erasure from a filesystem unlink.

Pilot: **30 families / 30 days** from separately approved collection start. Stop
and review every ten families. Median labeling effort above two minutes or more
than 20% unresolved triggers review; report setup/content-review overhead separately.

Accepted sanitized S0 records and negative results: durable Git history, **no promised
90-day erasure**. Review continued use at pilot close (day 30) and again at day 90;
withdrawal can stop use but cannot promise removal from clones/mirrors/backups.
This retention tradeoff requires explicit collection-stage acceptance.

No private or secret data is permitted. On suspected inclusion, stop staging/export,
quarantine locally for human assessment, and use a separately reviewed incident path.
If already committed/pushed, stop further propagation where authorized and assess
all copies; neither history rewrite nor credential rotation is implicitly authorized.
Never print suspected secret content in logs or review messages.

Recovery reuses Git for accepted S0 artifacts and manifests. An isolated restore
must verify hashes, revision references and excluded/withdrawn status before reuse.
Unreviewed drafts have no promised recovery; loss is counted, never reconstructed
and represented as an original human judgment. Backup topology remains unverified;
this proposal does not claim production-ready recovery.

## Workflow, audit and export

Use local forms and explicit review of displayed content and labels; no predicted
label suggestions, browser service, Notion, cloud spreadsheet or account setup.
Future helper validates accepted record references and produces an auditable local
candidate. It cannot synthesize a human acceptance event or stage unreviewed drafts.
A schema-valid record is not automatically trusted or authorized.

Record effort, counts, unresolved/excluded outcomes and revisions. Retain negative
results. Version sanitized reviewed artifacts only. Git publication is separately
authorized; neither local custody nor content review grants permission to push.
Future router evaluation needs its own approved frozen experiment, not merely data.

M3 approval and pilot progress do not accept M4's artifact or establish independent
checkpoint custody. M4 requires its separate human judgment and custody decision.
The later main study requires hidden labels outside the experiment writer's access;
this exposed train/dev pilot cannot become that holdout by renaming its split.

## Future implementation acceptance tests (not executed)

- Design approval cannot create cases; implementation approval cannot collect them.
- Unreviewed/rejected/private content cannot enter the accepted directory or Git.
- Human decision must bind exact content/label hash; changed revision invalidates it.
- Missing/forged acceptance is rejected; schema validation is not human verification.
- Same-human A/B cannot claim independent correctness; missing B remains personalized.
- Sensitive optional capabilities preserve local-only labels; forbidden sets remain.
- Family split leakage, unknown fields, duplicate IDs and broken references reject.
- Frozen corrections preserve provenance; unresolved cases stay in metric denominators.
- Day 7 draft expiry, day 30 closure and day 90 use review are explicit and testable.
- Crash/restart cannot publish a partial record; restore verifies hashes and exclusions.
- No network/model/executor call; no bypass of M4 or hidden-test custody gates.

Resource target: offline CPU-only stdlib helper, bounded 30-family input, no GPU,
background process, listener or new dependency. Measure actual helper latency/RSS
when implemented; do not report estimates as measurements. Human effort is the
primary feasibility result. No household function depends on the pilot.

Rollback: discard unused candidate tooling before collection; after authorized
collection stop new entries and mark affected accepted records excluded from use.
Preserve accepted provenance and negative results. No production rollback needed;
no new authority, broker deployment or infrastructure mutation is proposed.

## Next concrete gate

Approve implementation of **R: local S0 forms/validator**, with fixture-based tests
and no collection. After review of that implementation, separately authorize up to
30 sanitized train/dev families with explicit durable-retention acceptance. No
case creation is inferred from design/readiness approval. Paper remains optional;
separate OS custody is reserved for a later protected study. M4 remains separate.
