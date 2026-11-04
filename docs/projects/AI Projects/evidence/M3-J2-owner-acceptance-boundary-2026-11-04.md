# M3 J2 owner-acceptance boundary — 2026-11-04

## Result

The exact candidate-v4 owner decision is now machine-checkable without
broadening it into training or production authority.

`nlu_j2_owner_acceptance_v1.py` binds an acceptance to all four owner-review
identities:

- corpus `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`;
- normalized set
  `a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0`;
- label review
  `896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028`;
- quality review
  `f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f`.

It accepts only decision `accept` with scope `corpus-release-only`, a nonempty
owner identity, training authorization false, sealed-evaluation access false,
authority `not-granted`, automatic routing `off` and an exact self-hash.
Duplicate JSON keys, a stale self-hash, any artifact substitution or any
attempt to broaden the scope fails closed.

The expanded J2 source suite passes 53/53. No acceptance artifact has been
created because Jason has not yet made the exact owner decision on these four
hashes. A later valid record will capture that decision; it will not
authenticate external custody or authorize training. The separately controlled
custody signer and sealed evaluation custodian remain independent gates.

