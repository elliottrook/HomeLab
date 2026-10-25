# D4 development attempt 8 preregistration — 2026-10-24

Candidate-E closes the bounded terminal-field omission seen in attempt 7 by
requiring a minimum length of one in the JSON grammar for discrimination and
each verification string. The grammar applies this requirement to every
decision because the local constrained decoder does not express conditional
branches. For nonterminal check decisions, the engine still clears those
advisory strings before retention and records only the content-free
normalization flag. Terminal decisions retain the required values for blind
review.

The exact dry-run digest is
`0e6b324a5e779b00744f9258431280016116df75e1f7cccd67d0e383545104d6`.

- Exact eleven-file source manifest SHA-256:
  `3c46f8de30b871623663cda288623fc55a6bc8348ed044f7b75ac95b319ca4fe`.
- Frozen candidate-E decision rule SHA-256:
  `a41dbb8c45e9771650a39f58746e9698ec64a64aaee4dcf9301af5bb0b2f4d1c`.
- Complete offline suite: 164/164 passed.

The unchanged gate requires twelve structurally accepted sessions followed by
a fresh-history blind review with 12/12 passes in all six dimensions. A single
failure remains a NO-GO. Candidate-E has not run and grants no authority.
