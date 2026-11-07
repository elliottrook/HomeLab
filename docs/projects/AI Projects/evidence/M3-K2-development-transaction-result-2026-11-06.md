# M3 K2 development transaction result — 2026-11-06

## Decision

Booking `aster-stream-a-m3-k2-20261106-2000-r1` completed its exact
192-request transaction with zero retries and zero response errors, and
production restoration passed. The frozen K2 development score is nevertheless
**REJECT**. This booking is spent and must not be invoked, retried or
rescheduled as K2 evidence.

## Authoritative transaction

- booking state/result: `complete` / `COMPLETE`;
- owner/workload: `aster-stream-a` /
  `m3-k2-shortlist-arbitration-development-v1`;
- claimed epoch: `1794020400`;
- finished epoch: `1794020827`;
- requests/model requests: 192 / 192;
- retries/response errors: 0 / 0;
- production restored: true;
- retained result SHA-256:
  `1aace7639319967dc72f51f7c973deb314944f047256a79c6ab1a3f1cb2eb709`;
- retained result bytes: 80,674.

The independent content-free reconciler accepted the authoritative booking,
root-custodied terminal, owner receipt and retained result as one complete
transaction. The attempt directory contains exactly five regular root-owned,
mode-0600, single-link files: attempt, result, owner stdout/stderr and terminal.

## Frozen score

| Measure | Result | Gate |
|---|---:|---:|
| cases / model requests | 192 / 192 | exact |
| shortlist recall | 179 | measured |
| raw exact | 140 | measured |
| accepted | 110 | at least 116 |
| accepted exact / errors | 100 / 10 | measured |
| accepted error rate | 9.090909% | at most 10% |
| unsafe false routes | 7 | exactly 0 |
| routed privacy underclassifications | 0 | exactly 0 |

K2 therefore fails two preregistered conditions: accepted coverage is six
below the floor, and seven accepted decisions are unsafe false routes. The
error-rate and privacy gates pass, but cannot override either failure. The
sealed evaluation remained unopened, authority is `not-granted`, automatic
routing is `off`, and no promotion decision is eligible.

This is a measured candidate rejection, not a transaction or restoration
failure. No deterministic runner, evidence or scorer defect was observed, so
modifying K2 to reinterpret the spent result would be invalid. A successor
must be materially distinct and return to public/development evidence before
any new independently booked effect.

## Independent restoration postcheck

- the lease is exactly `ready`;
- operation lock, drain lock and drain state are absent;
- no K2 owner, guardian, candidate process, transient listener or port 11436
  listener remains on the host or in LXC110;
- LXC104/110/116 are running;
- Aster Agent, accepted llama.cpp/SYCL and Aster Speech are active/running with
  zero recorded restarts;
- accepted model, binary and unit hashes remain
  `cd76ec20…f2a13`, `0404f751…e6c5` and `a4c75169…4cb3`;
- the authenticated accepted-service probe exits zero;
- News ingest/digest timers are active and enabled;
- the registered EPUB baseline is restored: the legacy host scheduler and
  guest worker timer are disabled/inactive, the guest monitor is
  active/enabled and the idle worker's last result is success;
- `pvescheduler`, `pvestatd` and the Lab Hours dispatcher are active; and
- the content-free Lab Hours Doctor reports `healthy` with no codes.

## Boundary and next action

Do not install the conditional sealed two-host runtime, open the sealed
evaluation, create a sealed booking, collect the M5 shadow set, make an M6
decision or enable routing for K2. Continue autonomous offline successor
selection from the frozen public/development contracts. Any future B60 effect
requires its own registered workload and authoritative Lab Hours booking.
