# Full-Aster first-screen — October 27 exact-cycle effect card

Status: **APPROVAL-READY / NOT AUTHORIZED / ONE INVOCATION / NO RETRY**

Installed source: `b6dc186eef865924294b4e5cb1ef72d73c149733`.
Inactive-install result: `16a6cd27`. The eleven installed hashes/custody and
95 target-Linux tests pass.

## Start gate

The one invocation may start no earlier than 03:10 and no later than 03:30
America/Vancouver on October 27. Before invoking it, independently require:

- the October 27 F2 reconciliation accepted exactly three exit-zero archive
  rows and removed its spent date timers;
- the October 27 F3 converter wrote and independently verified the retained
  receipt, with no retry or uncertain receipt;
- the fixed 03:00 TrueNAS Mac pull completed successfully after those inputs;
- all eleven first-screen installed hashes/custody and all fixed full-drain
  dependency pins still match;
- staged Qwen3.6-35B artifact root:root 0400/0700 custody, exact size and SHA;
- whole-host lease exactly ready with no state/lock/operation lock;
- LXC104/110/116, Aster Agent, accepted 9B/SYCL/auth, Speech, News schedules,
  `pvescheduler` and `pvestatd` healthy;
- no backup, pull, lease, maintenance, F2/F3 process or other benchmark; and
- enough measured time to finish the 30-minute effect window and 15-minute
  restoration reserve before the next fixed News ingest.

Any failed, stale, changed or uncertain gate is terminal NO-GO. Do not invoke
the wrapper and do not retry in this cycle.

## Exact effect

Invoke once as root:

```sh
/usr/local/sbin/full-aster-first-screen --effect-authorized
```

The launcher must arm its independent guardian before the owner scope. The
controller creates fresh F4/F5 plus workload-specific admission bound to the
same full-drain lease, stops the registered consumers, temporarily maps the
staged artifact to unprivileged guest `ollama`, restarts LXC110 with only the
fixed read-only backup-excluded mount, starts the transient reasoning-on
Qwen3.6-35B unit, and sends exactly two fixed synthetic requests with 60-second
timeouts and zero retries. It retains only status, timing, content length,
finish reason and reasoning-field presence; no answer or hidden reasoning.

On success or failure, the same-process recovery stops the transient unit,
removes only `mp0`, restores exact root artifact custody, restarts LXC110,
verifies the accepted 9B/SYCL/auth baseline and restores all consumers before
releasing the lease. At 30 minutes the independent guardian fences a surviving
owner and runs the same mount-aware recovery; 45 minutes is the hard deadline.
Uncertain recovery retains state and the lease for reconciliation.

## Acceptance and exclusions

Accept only an exact two-row complete result plus absent candidate/mount,
restored root custody, exact accepted baseline, healthy consumers/schedules,
ready lease and no remaining guardian/owner process. Record content-free
timings and postchecks.

This card authorizes no model replacement or promotion, persistent unit/timer,
automatic routing, Candidate-H/M3 evaluation, full matched benchmark, F2/F3
retry, backup/schedule change, tool grant or Git push.
