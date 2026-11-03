# D4 candidate-g EPUB admission inactive install — 2026-11-03

## Decision

**PASS; INSTALLED INACTIVE.**

Jason approved the exact two-file correction frozen at platform commit
`03ed07fc`. The installer changed only the candidate-g full-inference source
and validator, retained both predecessor files in the root-only checkpoint,
and did not create a booking, run candidate-g, restart a service or interrupt
EPUB transcription.

## Installed proof

- source digest: `6103da31…13ad`
- validator digest: `094d588b…f31`
- custody: `root:root 0644`
- checkpoint: `/var/lib/local-ai-lab/checkpoints/sa3-epub-admission-20261103`,
  `root:root 0700`
- focused target tests: 15/15
- lease after install: `ready`
- shared drain state/lock and operation lock: absent
- LXC 104/110/116: running
- Aster Agent, accepted llama and Aster Speech inside their containers: active
- service restart: none
- candidate-g effect: not attempted

The correction now admits either a healthy active EPUB timer or a healthy
active/activating worker, so the legitimate long-running transcription state
does not fail candidate-g preflight or restoration. A fresh booking remains a
separate later effect; the spent booking must not be retried.
