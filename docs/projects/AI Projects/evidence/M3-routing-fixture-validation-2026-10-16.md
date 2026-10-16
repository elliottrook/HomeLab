# M3 routing fixture validation — offline

The synthetic routing comparison previously checked duplicate IDs/text and
capability names, but accepted an unknown decision status, a plan with no
capabilities, duplicate labels, extra family fields and duplicate presentation
prefixes. That could contaminate a future regression score without changing
the router itself.

The local candidate rejects those malformed corpus shapes and prevents the
router's proposal helper from emitting an unknown status. Five focused tests
pass, including malformed-fixture cases. Re-evaluating the unchanged 30-family
fixture gives the same test-family results: lexical rules 10/10 and TF-IDF
nearest 1/10; the result remains `no-production-adoption`.

This is fixture hygiene for a **developer-authored synthetic** comparison.
It provides no human-labelled holdout, calibrated confidence, privacy proof,
latency result or authority for automatic handover.
