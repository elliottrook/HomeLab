# Stream A D4/M3 workload execution bindings

**Date:** 2026-10-25  
**State:** M3 execution binding frozen; D4 candidate frozen but execution binding **NO-GO**

This correction distinguishes an exact candidate from an executable workload.
It does not supply same-cycle F2–F5 evidence, arm recovery, acquire a lease,
stop a consumer, read a credential or call the model.

## D4 candidate-G: exact and unspent, execution boundary open

The Mac packet is `/private/tmp/aster-d4-candidate-g-packet.tar`, owner-only
mode `0600`, exactly 11 members, SHA-256
`d5a36cd02be6fdd3d0935e6ca1b23c1d0cad1329d72b04bb4048505fec7e3d47`.
Every member length and SHA-256 matches source manifest
`defaf6039e01c7ac0cc16b3c2a28568336335bc949ea8992ec288819d33c23b8`.
The approved and unspent run digest is
`03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`.
The runner in that frozen packet has SHA-256
`10889d30becdb613debf034a2766fd1313cd25c51a2cea26a7511e0e70776936`.

There is no installed or staged D4 production runner or journal. The platform
owner's proposed boundary is `/var/lib/aster/d4-candidate-g/`, root-owned mode
`0700`, with root-owned mode-`0600` files and future `run.json` and
`attempt-journal.jsonl` outputs. That proposal is not installed or approved.

The frozen runner reads `ASTER_LLAMA_API_KEY` from its environment. The
platform-owned F6 boundary instead requires credential delivery by the
approved secret broker as a protected inherited file descriptor or standard
input, never through argv, environment, JSON, journal or logs. No reviewed
adapter currently connects those two interfaces. Therefore:

- do not source `/etc/aster/aster.env`;
- do not stage or execute candidate-G;
- do not create either output file; and
- retain the candidate as exact and unspent while this interface is resolved.

Changing the frozen runner to accept a descriptor or standard input would
change its manifest and run digest. That would be a new candidate and would
need fresh candidate authorization after independent review. If the existing
environment interface is instead retained, the platform owner must first name
and review the exact secret-broker population command, execution identity,
custody and clearing behavior without exposing the key.

The already approved workload limits remain descriptive only: at most 12
sessions, 36 calls, 60 seconds per request and 180 seconds per session, with a
strict 12/12 terminal structural requirement and a valid owner-only
hash-chained journal. They grant no execution authority while the credential
bridge is absent.

## M3 NLU calibration: executable binding frozen

The packet is staged inactive in LXC110 at
`/var/lib/aster-nlu-calibration/nlu-calibration-v1`, root-owned mode `0700`,
with exactly 11 root-owned mode-`0600` inputs. Its staging-manifest SHA-256 is
`69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
The installed runner is
`/var/lib/aster-nlu-calibration/nlu-calibration-v1/nlu_calibration_runner.py`,
SHA-256
`b8ada869ff939255ba62618180a720cf5f6ebe60e1ee7e2250ee00a1f34e5e11`.
The source, release and development inputs match their frozen hashes;
`run.json` and `attempt-journal.jsonl` are absent.

The F6 card must pin the absolute Python interpreter path and its target,
version and hash before execution. It must also bind the invoking identity to
root in LXC110 and preflight that `/etc/aster-llama-api-keys` has the reviewed
owner/group/mode and is readable only by that executor. Subject to those live
pins, the invocation shape is:

```sh
cd /var/lib/aster-nlu-calibration/nlu-calibration-v1
exec timeout --signal=TERM --kill-after=10s 1230s \
  /usr/bin/python3 nlu_calibration_runner.py \
  --source cases.json \
  --release release.json \
  --development nlu-development-v1.json \
  --output run.json \
  --journal attempt-journal.jsonl \
  --key-file /etc/aster-llama-api-keys
```

The key remains inside LXC110 and is read only by the runner; it must never be
copied to argv, logs, evidence, the model prompt or either output. Terminal
acceptance requires exit zero, exactly 60 journaled attempts and 60 run
records, valid journal-to-run agreement, the accepted
candidate/engine/policy digests, and a healthy idle endpoint postcheck.
Invalid model responses remain in the denominator. Transport uncertainty,
deadline exhaustion, lease loss, evidence-write failure or a shorter result
forbids replay. Scoring and threshold selection remain later Mac-side steps
under their frozen custody rules.

## Shared ordering and remaining platform gates

D4 remains first, so its credential bridge blocks both live workloads even
though M3's runner packet is ready. M3 can start only after D4 reaches a
reconciled terminal state and the lease/restoration reserve still covers M3
plus recovery. Neither command is a lease phase: the F6 owner must record a
`start` phase before invoking it and an `outcome` phase only after validating
terminal evidence.

The controller acquire schema accepts only backup, F2 and F3 receipts. There
is no accepted durable F4 artifact/schema/digest and no durable F5 observation
artifact/digest. These must be created and reviewed in the required fresh
cycle; no extra acquire fields or substitute receipts may be invented.

Consequently the effectful F6 transaction remains **NO-GO** pending all of:

1. a reviewed D4 secret-delivery bridge compatible with the frozen candidate,
   or a separately authorized replacement candidate;
2. absolute M3 interpreter and execution-identity/custody pins;
3. fresh same-cycle F2, F3, F4 and F5 evidence; and
4. an exact platform transaction/recovery card and its separate live approval.
