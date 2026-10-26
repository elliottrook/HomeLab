# Stream A D4/M3 workload execution bindings

**Date:** 2026-10-25  
**State:** exact workload bindings frozen; no execution or staging authorized

This packet closes the workload-runner portion of the effectful F6 review. It
does not supply same-cycle F2–F5 evidence, arm recovery, acquire a lease, stop a
consumer or call the model.

## D4 candidate-G

The Mac packet is `/private/tmp/aster-d4-candidate-g-packet.tar`, owner-only
mode `0600`, exactly 11 members, SHA-256
`d5a36cd02be6fdd3d0935e6ca1b23c1d0cad1329d72b04bb4048505fec7e3d47`.
Every member length and SHA-256 matches source manifest
`defaf6039e01c7ac0cc16b3c2a28568336335bc949ea8992ec288819d33c23b8`.
The run digest is
`03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`.

Future guest staging is fixed at
`/var/lib/aster-d4-candidate-g/attempt-10` in LXC104, root-owned mode `0700`,
with each of the 11 files root-owned mode `0600`. Staging must refuse an
existing directory or any symlink and revalidate every manifest length/hash
after extraction. The journal path is
`/var/lib/aster-d4-candidate-g/attempt-10/attempt-10-journal.jsonl`; it must be
absent before the run. The exact runner is
`/var/lib/aster-d4-candidate-g/attempt-10/sa3_development_execute.py`, SHA-256
`10889d30becdb613debf034a2766fd1313cd25c51a2cea26a7511e0e70776936`.

The fixed invocation inside LXC104 is:

```sh
set -a
. /etc/aster/aster.env
set +a
cd /var/lib/aster-d4-candidate-g/attempt-10
exec timeout --signal=TERM --kill-after=10s 2200s \
  /opt/aster-agent/venv/bin/python sa3_development_execute.py \
  --fixtures sysadmin-sa3-development-fixtures-draft-v1.json \
  --source-corpus sysadmin-incident-development-extension-draft-v1.json \
  --source-plan sysadmin-incident-development-plan-v1.json \
  --expected-run-digest 03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153 \
  --ledger /var/lib/aster-d4-candidate-g/attempt-10/attempt-10-journal.jsonl \
  --execute
```

The existing local API key crosses only from root-readable
`/etc/aster/aster.env` into the runner environment; it is never an argument,
output or evidence field. The command permits at most 12 sessions, 36 calls,
60 seconds per request and 180 seconds per session. Terminal acceptance requires
exit zero, a healthy/idle postcheck, 12 accepted terminal sessions and a valid
owner-only hash-chained journal at the approved run digest. Any started but
unrecorded attempt, timeout, transport uncertainty or nonzero exit makes the
candidate spent/uncertain and forbids replay. The already-approved conditional
blind review runs only after 12/12 structural admission.

## M3 NLU calibration

The packet is already staged inactive in LXC110 at
`/var/lib/aster-nlu-calibration/nlu-calibration-v1`, root-owned mode `0700`,
with exactly 11 root-owned mode-`0600` inputs. Its staging-manifest SHA-256 is
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
The installed runner path is
`/var/lib/aster-nlu-calibration/nlu-calibration-v1/nlu_calibration_runner.py`,
SHA-256
`b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11`.
The source, release and development inputs currently match their frozen hashes;
`run.json` and `attempt-journal.jsonl` are absent.

The fixed invocation inside LXC110 is:

```sh
cd /var/lib/aster-nlu-calibration/nlu-calibration-v1
exec timeout --signal=TERM --kill-after=10s 1230s \
  python3 nlu_calibration_runner.py \
  --source cases.json \
  --release release.json \
  --development nlu-development-v1.json \
  --output run.json \
  --journal attempt-journal.jsonl \
  --key-file /etc/aster-llama-api-keys
```

The key remains inside LXC110 and is never printed or copied. Terminal
acceptance requires exit zero, exactly 60 journaled attempts and 60 run records,
valid journal-to-run agreement, the accepted candidate/engine/policy digests,
and a healthy/idle endpoint postcheck. Invalid model responses remain in the
denominator; transport uncertainty, deadline exhaustion, lease loss, evidence
write failure or a shorter result forbids replay. Scoring and threshold
selection remain later Mac-side steps under their frozen custody rules.

## Shared ordering and remaining platform gap

D4 runs first. M3 can start only after D4 reaches a reconciled terminal state
and the lease/restoration reserve still covers M3 plus recovery. Neither command
is a lease phase: the F6 owner must record a `start` phase before invoking it
and an `outcome` phase only after validating its terminal evidence.

The controller acquire schema accepts only backup, F2 and F3 receipts. F4/F5
therefore require a separately reviewed durable admission artifact checked by
the effect owner before arm/acquire/quiescence; no extra acquire fields may be
invented. Exact same-cycle digests and platform phase commands remain pending
in the platform-owned F6 card.
