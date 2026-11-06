# SA4 final effect-admission boundary — 2026-11-05

The first-repair release review found and closed a critical missing boundary.
The atomic owner previously validated the shape and digest bindings of a final
effect-admission record, but no production component authenticated the fresh
owner approval and AI-PAM grant that create that record. A syntactically valid
approval digest therefore could not yet be treated as a release candidate.

`sa4_effect_admission_v1.py` now invokes the exact compiled two-party authority
verifier and cross-binds its fresh signatures to the zero-effect source
preflight, exclusive checkpoint, already claimed durable one-use grant,
compiled target registration and exact candidate bytes. It emits one
short-lived admission only inside the intersection of the claim, grant and
owner-approval deadlines. The result authorizes exactly one effect, keeps retry
false and routing off, and carries the authenticated owner approval digest.

Three focused tests cover exact admission, source/claim/candidate drift and the
requirement to run the real authority verifier. The joined disposable success
and rollback rehearsal now uses this admission component rather than a
hand-built record. The full SA4 suite passes **132/132**.

This is source only. It has not been installed, no fresh signer was invoked and
no admission, checkpoint, claim, repair or rollback occurred. Next is the
single root transaction owner that invokes the frozen chain and always reaches
signed observation plus terminal ledger burn. The first live repair remains a
separate exact immediate approval gate.
