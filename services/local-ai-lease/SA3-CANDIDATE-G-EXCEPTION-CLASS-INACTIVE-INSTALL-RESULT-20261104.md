# SA3 candidate-g exception-class inactive install result — 2026-11-04

## Result

**PASS — installed inactive.** The exact one-file correction came from mirrored
platform commit `fb32f402bc5e448ed47f3823d58aa53c78a2f3d5`. Its deterministic
bundle SHA-256 was
`6aec85a19b69c102cf4304abf91006db17923102934b50e5a81080d95e5cb2cb`.

LXC110 `aster_llama_sa3_evidence_envelope_wrapper.py` now matches
`626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe`,
root:root mode 0644, one regular link. The predecessor is retained root:root
mode 0600 under root:root mode-0700 checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-exception-class-r1-20261104`.

## Independent proof

- A synthetic otherwise-unhandled `KeyError` produced exactly
  `candidate-g guest exception-class:KeyError`.
- Its private message was absent from the output.
- Whole-host lease returned exactly ready.
- No drain/shared lock or port-11436 listener remained.
- Aggregate Doctor returned healthy with no codes.
- Aster Agent, accepted llama, Speech, News, EPUB, Lab Hours Doctor,
  `pvescheduler`, and `pvestatd` were healthy.
- Aster Agent, accepted llama and Speech restart counts remained zero.

No booking, workload/model call, or service restart occurred. Exact host and
local staging artifacts were removed; the rollback checkpoint was retained.

## Boundary

This installation does not recover or score r4. A future attempt requires a
new authoritative conflict-free booking and all fresh gates. It authorizes no
automatic retry, model/backend change, restart, blind review, route, tool grant
or promotion.
