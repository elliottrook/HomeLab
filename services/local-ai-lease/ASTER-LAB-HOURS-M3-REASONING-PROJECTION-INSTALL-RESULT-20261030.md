# M3 reasoning projection installation result — 2026-10-30

Status: **INSTALLED INACTIVE; TARGET PROOF PASSED**

Platform commit `8747d6ad` was installed from deterministic archive SHA-256
`fe6626952a9832bf78c32667e99e9f4e6c676a6c391d265c6fa58e31fe8e2797`.
The former files are retained at root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/m3-reasoning-8747d6ad`.

The five changed host pilot files and the one corresponding LXC110 runner were
replaced inactive. Host target tests pass 14/14, guest projection tests pass
2/2 and all 32 release pins match. The lease is ready, no drain state or lock
remains, all three guests and core production services are healthy, and no
model, mount, restart or workload effect occurred during installation.

The spent 12:16 booking was not retried. A later run requires a fresh booking
and all live lease/shared-lock gates. Automatic routing and model promotion
remain off.
