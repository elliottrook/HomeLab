# SA3 single-operator custody activation

Date: 2026-10-03  
Status: **ACTIVE EMPTY CUSTODY; COLLECTION AND EVALUATION BLOCKED**

Jason approved a private local answer-key location outside Git for the
single-operator SA3 path. The directory is owned by the local user, has mode
`0700`, and contains an empty answer-key placeholder with mode `0600`.

The location is deliberately not recorded in Git. Its empty file SHA-256 is
`932b7fa29f29a1ed1e3e21ca2d5b6465cdf1370c8a757c3fffcfd52b12523a0e`.
It is a custody boundary only: no incident, answer, reviewer label, model
output, credential, raw log, production command, or evaluation result exists.

Jason is the sole custodian. Holdout cases and answer keys, if later collected,
must be authored before development tuning, digested before that tuning, and
kept out of retrieval and implementation-tuning paths until frozen evaluation.
Any result must be described as single-operator within-lab comparative evidence,
not independent evaluation or generalized model quality.

Before collection, a separate plan must define sanitization, the initial
development/holdout assignment, retention/withdrawal handling, and the exact
freeze procedure. Before evaluation, separate approval remains required.
