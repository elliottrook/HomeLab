# SA3 candidate-i scope inactive install result — PASS — 2026-11-04

The exact deterministic archive
`8508bd336b18d05dc1f84efc3322f20a55e4460645ccc6ae0b1dcc6d8a63ab40`
from platform source commit `5e2190f6` passed predecessor, custody, lease and
shared-state preflight. It installed only:

- `sa3_candidate_i_evidence_envelope_listener_adapter.py` at
  `80e7491b3d9bd3c457bf362baae97ba3377ac260dde1169933ddbdbc97cc1ee6`;
- `lab_hours_release_manifest.json` at
  `05e41525f08f52597128b6523b92c1ed7de3316cee09e3e79f95d347d31eb65d`.

Both installed files are root:root regular one-link mode 0644 files. The exact
predecessors are retained under root:root mode-0700 checkpoint
`sa3-candidate-i-scope-r1-20261104` as mode-0600 one-link files with their
original hashes `e16a2512…8c6` and `c2812b75…a5e`.

The installed reserved runner accepts all 36 manifest pins. For fixed identity
`lease-1` / generation `2`, the host adapter's scope function, the scope passed
in its guest command and the guest wrapper independently return the identical
`aster-llama-sa3-i-c3696795d255baad.scope`. This is the exact path that R1
failed to bind.

Postcheck found the lease ready, no drain state/lock or operation lock,
LXC104/110/116 running, Aster Agent, accepted `aster-llama.service`, Speech,
pvescheduler, pvestatd, Lab Hours dispatcher and Doctor active. Temporary
staging was removed. No service restart, model/backend change, workload,
booking, route, repair authority or promotion occurred.

The next eligible effect is one distinct R2 reservation only after the
authoritative ledger reports the complete proposed window and recovery reserve
clear. R1 remains spent and may not be retried.
