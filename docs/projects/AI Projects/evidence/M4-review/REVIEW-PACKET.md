# M4 independent review packet — prepared, not approved

The existing candidate `af2cc4f988ca9ed1a69e0d425c2bb7991ffa7f71` is reconciled
locally onto published `7133f3fc43add7a52be1643496598b0cf13f7d9a`. No production
mutation, new collection, identity, custody store, schedule or remote write is
part of this packet. The earlier verifier/source manifest still matches exactly.

## Concrete review object

- Design: [storage and review lifecycle](../../M4-Storage-and-Review-Design.md).
- Measurement artifact: [164-event paired proof](../M4-paired/measurement-001.json).
- Artifact SHA256: `9a3e0447adbf27f24bf5d9ab777ebbd5565bbce7873f554034304a4ce88fea38`.
- Ledger head: `sha256:59fa02fe1a196ba123c447d4e773bd9404290970f4446113c8dd61b1b12cc7c9`.
- Verifier SHA256: `9b04d938a79c6c2c61a2b4328b77d2f3b4292fee066cca1b5c7500071f8b8af7`.
- [Source/record manifest](manifest.json) pins dependencies and the original report.
- Reconciliation validation: 56 harness/evidence tests and 29 separate selector-probe
  tests passed. A network-blocked replay reconstructed all164 events; historical
  hashes match. It reports review approval `not-granted`.

These hashes were checked in the same developer workspace. Their presence here is
reproducibility evidence, **not independent checkpoint custody**. A human reviewer
must obtain and retain an accepted commit/artifact/head through a path the
experiment writer cannot replace, then compare that independently held record.
Do not copy a head from a candidate and claim this alone authenticates it.

## Proposed decision and explicit limits

The reviewable decision is whether to accept the **synthetic-only offline review
procedure** and retain the current assistant/rules after these limited experiments.
It is not permission to deploy a collector, preserve real prompts, trust a learned
router, change access policy, create a new account or promote a model/harness.
Synthetic provenance, sample limitations and negative results remain part of the
accepted record. Verifier success establishes structure/lineage/arithmetic; it
cannot establish the truth of measurements or independence of authored labels.

The smallest custody arrangement needs no new infrastructure: Jason retains the
accepted commit, artifact digest and ledger head in a human-controlled record
outside the experiment writer's accessible storage. That could be an existing
independently controlled device/account or a physical record. This is a proposal,
not a claim that any such store has been selected, configured or protected.
Do not put credentials or signing keys in this packet. A new service or account
would require a separate exact identity/recovery proposal.

## Reviewer procedure

1. Inspect the pinned code, plan, synthetic inputs and acceptance criteria. Check
   family independence and limitations; do not equate repeated variants with
   independent examples or adopt an LLM's qualitative recommendation as evidence.
2. Obtain the exact accepted artifact and checkpoint independently of a later
   writer-supplied replacement. Compare artifact and verifier hashes first.
3. In a clean offline checkout using reviewed dependencies, run:

   ```sh
   /private/tmp/aster-lab-ops-venv/bin/python scripts/aster-adaptive/verify_evidence.py 'docs/projects/AI Projects/evidence/M4-paired/measurement-001.json' --expected-head '<independently-held-sha256-head>'
   ```

   The local interpreter path is an existing test environment, not a portable
   installation guarantee. Validate an equivalent environment before use elsewhere.
   The verifier does not run the measurement code or contact a model/service.
4. Keep the original artifact unchanged. Failure means reject/quarantine the
   candidate and retain prior accepted evidence, not repair the candidate's digest.
5. Record retain/reject/request-more-evidence, reviewer identity, accepted commit,
   artifact digest, external checkpoint, method of custody, limits and date in the
   reviewer-controlled record. Jason's scoped approval remains distinct from a
   software check or another agent's code review.

## Gate status

- Complete locally: candidate reuse/reconciliation, pinned verifier, bounded input,
  synthetic replay, tamper/ambiguity tests, restored lineage, no-egress check.
- Pending human/external evidence: reviewer identity and judgment, independently
  controlled accepted checkpoint, decision on the synthetic-only storage design.
- Excluded: operational private-data retention. Numeric retention, consent,
  independent permissions, backups, deletion verification and service budgets are
  required before a future real-data collection proposal; none are inferred here.

M4 remains open. M1 Stage2 real-session assurance remains separately open. Do not
replace these human/trust gates with additional synthetic throughput measurements.
