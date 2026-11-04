# D4 candidate-g terminal reconciliation boundary — 2026-11-04

## Result

The candidate-g post-run path no longer depends on manually inferring success
from a booking state or model result. The source-only
`sa3_evidence_envelope_reconciliation_v1.py` accepts only an exact complete Lab
Hours terminal transaction for the named booking with:

- workload `sa3-evidence-envelope-quality-v1`;
- 20 retained cases and 14 model requests;
- zero retries and an error-free exact result envelope;
- `production_restored=true`; and
- no authority or automatic routing.

Only after those gates pass does it produce the already frozen model-identity-
blind review packet. Its content-free reconciliation summary binds the exact
result and review-packet hashes while leaving `quality_decision` at
`pending-independent-review`. It never converts structural completion into a
semantic pass.

NO-GO state, failed restoration, booking substitution, request-count drift or
any result error fails before a review packet is produced. The combined D4
evidence-envelope suite passes 34/34.

The follow-on CLI closure reads the exact booking terminal, frozen packet and
root-custodied result, then writes the model-blind packet with exclusive-create
mode 0600 and prints only the content-free reconciliation summary. It refuses
to overwrite an existing packet. The focused reconciliation, blind-review,
candidate and workload-proposal suite passes 15/15. This removes manual JSON
assembly from the terminal-to-review handoff without changing any acceptance
gate or making a quality decision.

This is preparation for the scheduled r3 transaction only. It does not read a
future result, pre-score the candidate, authorize a retry or promote a route.

