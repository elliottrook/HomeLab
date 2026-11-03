# SA3 EPUB admission inactive installation — 2026-11-03

Status: **PASS; installed inactive**

Jason approved platform commit `03ed07fc`. The exact installer replaced only
`full_inference_lab_sources.py` and `full_inference_lab_validator.py`, retained
their predecessor bytes at
`/var/lib/local-ai-lab/checkpoints/sa3-epub-admission-20261103`, and made no
booking or candidate-g/model request.

- installed hashes: `6103da31…13ad`, `094d588b…f31`
- installed custody: `root:root 0644`
- checkpoint custody: `root:root 0700`
- focused target tests: 15/15
- lease: ready
- shared state/locks: absent
- LXC 104/110/116: running
- Aster Agent, accepted llama and Speech: active in their containers
- restart: none
- EPUB interruption: none

The spent candidate-g booking remains terminal and must not be retried. A fresh
booking is a separate later decision and must pass the reservation-ledger,
lease and shared-lock gates.
