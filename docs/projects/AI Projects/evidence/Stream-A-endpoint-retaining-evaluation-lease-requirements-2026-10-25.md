# Stream A endpoint-retaining evaluation lease requirements — 2026-10-25

> State: **CONSUMER REQUIREMENTS FROZEN; PLATFORM IMPLEMENTATION REQUESTED**
>
> This is a coordination contract, not a lease implementation or run approval.

## Problem measured

Two already prepared Stream A evaluations need the accepted production-local
Qwen3.5-9B Q4_K_M, llama.cpp b11429, SYCL/Level Zero endpoint to remain active:

1. D4 candidate-G: 12 tool-free sessions, at most 36 calls, at most 180 seconds
   per case and no replay after uncertainty.
2. M3 NLU calibration: 60 tool-free classification calls, concurrency one,
   90 seconds per request and a strict 1,200-second wall deadline.

The legacy light/full-stop lease drains the endpoint. The application-only
lease retains it but is bound to the A1 sidecar, test key, ingress and
application-specific receipt. Neither is a valid authority envelope for these
two direct, authenticated, tool-free evaluations.

## Required platform contract

The platform owner should provide the smallest distinct evaluation lease that:

- retains the exact accepted `aster-llama.service` and authenticated endpoint;
- claims the B60 inference slot exclusively for one exact Stream A bundle;
- quiesces ordinary Aster, Speech, News and any other registered inference
  consumer before admission, without changing their configuration;
- creates no A1 sidecar, temporary test key, ingress or firewall path;
- binds a source-derived backup/recovery receipt, exact model/runtime/unit
  identity, lease ID, generation, owner and hard deadlines;
- runs an independent deadline watchdog outside the stopped consumers;
- restores the exact consumer and schedule baseline and proves endpoint health,
  authentication and idleness before releasing the lease; and
- retains state and the exclusion lock on any uncertain recovery.

The lease must reject whole-host/full-stop, application-sidecar and generic
`ready` status as substitutes for its own exact receipt.

## One-lease sequence and budget

Jason has accepted a maximum 90-minute supervised outage for the first lab-
hours pilot. Reserve the final 15 minutes for restoration, leaving at most 75
minutes before forced recovery. The two preregistered maxima are 36 minutes
for D4 and 20 minutes for M3, totaling 56 minutes. Allow at most 10 additional
minutes for fresh preflight and custody transitions, leaving nine minutes of
execution contingency before mandatory restoration.

Run order:

1. acquire the exact evaluation lease and verify both packets/journal paths;
2. run D4 candidate-G once and retain its distinct owner-only journal;
3. if D4 completes or fails only its semantic/structural admission while the
   endpoint and lease remain healthy and unambiguous, run M3 once;
4. if D4 has transport uncertainty, endpoint drift, lease loss or evidence-
   custody failure, skip M3 and restore immediately;
5. if M3 begins, its own journal prevents replay of any uncertain case;
6. restore and independently verify production before either result is scored
   or reviewed.

The lease controller must not merge the two journals, treat one result as the
other's admission, or allow unused time to extend the hard restore deadline.

## Fresh admission inputs

Immediately before acquisition, require:

- the platform's exact installed controller/watchdog/recovery hashes;
- a source-bound backup receipt acceptable to this evaluation lease;
- no F2/F3 activity, backup, pull, maintenance, News run or competing lease;
- the accepted llama runtime active, authenticated, idle and pinned;
- D4 digest `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`;
- M3 stage-manifest digest
  `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`;
- sufficient time for the fixed sequence plus the full restoration reserve;
  and
- an independent operator/recovery path able to act if this task disappears.

## Result boundaries

A completed D4 run may proceed to its approved blind review only after 12/12
structural admission. A completed M3 run may be scored against its private
calibration labels only after exact journal agreement. Neither result grants a
tool, opens the holdout, enables shadowing/routing, promotes a model or changes
production. Each workload retains its existing no-retry and separate approval
boundary.

The platform owner has been asked to return an exact branch commit, changed
paths, tests, remaining live gates and a decision on whether successful F2/F3
evidence is required. No live platform state changed while recording these
requirements.
