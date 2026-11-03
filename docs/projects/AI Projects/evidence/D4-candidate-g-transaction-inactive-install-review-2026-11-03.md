# D4 candidate-g transaction inactive-install review — 2026-11-03

Status: **PASS AFTER CORRECTION; INSTALLATION NOT PERFORMED**

The review matched platform commits through `ccb6b9ee` to the already installed
candidate-g registration and five-file runtime. The transaction keeps outcome,
checks, effects, authority and routing deterministic; the model supplies only
bounded prose on 14 of 20 cases. Any error, count drift, effect, authority or
routing drift fails the transaction. Listener scope, ephemeral key, bounded
capture and production restoration all have unconditional cleanup paths.

The first install bundle omitted
`sa3_evidence_envelope_inactive_install.py`, which the new installer imports.
That bundle was rejected before host use. Platform commit `ccb6b9ee` adds the
dependency and a regression test. The corrected combined suite passes 58/58.
Two deterministic seven-file builds match at SHA-256
`b486609b1468d05b70a3dab107398bf56db49c22dda818aa6da18e8468177d54`.

Read-only live validation matched the current release-manifest baseline
`36e20242…d84d`, found both new host modules and the guest wrapper absent,
found both fresh checkpoint identities absent, and found no candidate-g unit.
The effectful registered runner is unchanged and will continue to reject the
new runner kind.

The exact installation is therefore approval-ready. It changes only two
dormant host modules, one dormant guest wrapper and the release manifest, with
root-only rollback checkpoints. It creates no booking, schedule, lease, lock,
model call, service stop, restart, route, repair or promotion.
