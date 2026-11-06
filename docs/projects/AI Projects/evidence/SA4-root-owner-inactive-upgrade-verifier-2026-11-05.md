# SA4 root-owner inactive-upgrade verifier — 2026-11-05

The independent source verifier accepts only the exact four-row inactive
upgrade result, fixed plan digest, exact before/after hashes, root:root 0644
single-link regular files, retained predecessors for both replacements, all
four isolated imports, unchanged unconfigured effect-owner bindings, complete
production health and rollback readiness.

It rejects any key/signature, authority, ledger, checkpoint, target,
root-owner or service action. It also rejects health drift, a changed rollback
claim, an unexpected row or any hash/metadata mismatch.

Verifier tests pass 3/3 and the complete SA4 suite passes 143/143. No live
change occurred. The next step remains the separately approved inactive
installation followed by validation with this verifier.
