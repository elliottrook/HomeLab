# Run 003 go/no-go review

Date: 2026-09-26

## Decision

**GO TO CANDIDATE PREPARATION; NO-GO FOR LIVE EXECUTION AT THIS CHECKPOINT.**

A third fixture attempt can still provide material evidence because the first two
attempts stopped before mutation and therefore never tested the intended systemd
isolation controls. The new bounded failure schema would make another preflight
failure diagnostic rather than merely inconclusive. This does not justify an
open-ended retry sequence.

## Evidence

- Run 001 failed during the guest-health command. Its immutable record proves no
  mutation.
- Run 002 completed unit-state, path, guest-health and host-resource collection,
  then failed before `preflight-verified`. Its immutable record also proves no
  mutation and no recovery requirement.
- A separate two-query DNS diagnostic succeeded after run 002. It confirms later
  reachability only and does not identify the run-002 failure.
- The lifecycle now records allowlisted failure boundary/class fields, with 210
  local tests passing and secret-bearing exception text excluded.
- Repository evidence records substantial primary-host RAM, but also warns that
  configured guest limits are not a safe spare-allocation budget. No verified,
  ready disposable clone target currently exists. Creating one would add an
  infrastructure change and test a different environment.

## Alternatives

| Option | Assessment |
|---|---|
| Stop after run 002 | Safest, but leaves the isolation feasibility question unanswered and discards the information value added by bounded failure telemetry. |
| Repeat the run-002 artifact | Rejected. Its approval is consumed, its journal is exclusive and it lacks the new failure fields. |
| Build a disposable clone first | Preferred for later corpus or destructive tests, but disproportionate for this 64 MiB, one-task, 15-second fixture and unsupported by a verified current capacity/placement plan. |
| Prepare one run-003 candidate for LXC100 | Preferred next step if it separately pins both prior evidence sets, retains all limits and obtains a fresh one-shot approval. |

## Required run-003 gates

Preparation may proceed locally only. A live candidate must have a distinct
journal, manifest and approval record; verify both prior immutable evidence chains;
retain the same fixed commands, 64 MiB memory, zero swap, one task, 10% CPU and
15-second runtime; include the bounded failure fields; pass the complete local
suite; and receive a fresh explicit approval after technical review.

No automatic retry is permitted. If run 003 fails before mutation, stop live
attempts and redesign the feasibility method or create a disposable target. If it
reaches mutation and becomes uncertain, use only the existing receipt-based manual
recovery process. A pass establishes fixture isolation feasibility only; it does
not authorize accepted-corpus evaluation or operational autonomy.

## Candidate preparation checkpoint

The local candidate uses journal
`/private/tmp/aster-s0-lxc100-attempt-3-20260926`, manifest
`lxc100-attempt-3-manifest.json` and approval record
`lxc100-attempt-3-approval.json`. It validates the complete run-001 and run-002
evidence chains before a prepared invocation. Run-002's exact reviewed and
consumed approval records are separate evidence objects; neither can satisfy the
run-003 scope.

The execution commands, unit/canary names and resource ceilings are unchanged.
The only execution-path change is bounded failure boundary/class telemetry.
Technical review passes with 213 local tests; human approval, exclusive-window and
one-shot release fields remain pending. Candidate preparation performs no SSH,
DNS, journal creation or remote action.

## Fresh one-shot authorization

Jason replied `approve` to the explicit request to approve both the reviewed
commit push and exactly one run003 fixture probe. This authorizes one invocation
after final hash/test verification. It does not authorize a retry, accepted-corpus
evaluation, package installation, unrelated infrastructure change, automatic
recovery or a later push. The external record carries this provenance and binds
the final released manifest; the distinct journal still enforces one-shot use.

## Outcome — hard stop reached

Run003 passed preflight, created the exact canary and attempted the transient unit.
The unit failed before payload readiness with `226/NAMESPACE`; the bounded record
identifies `run-readiness` / `validation`. No accepted corpus was evaluated.

Read-only recovery checks proved `MainPID=0`, the exact invocation ID, absent
cgroup/runtime probe and an unchanged canary receipt. Manual recovery reset only
that failed transient unit and removed only the matching canary. Final state is
unit `not-found`, all probe paths absent, systemd `running`, and the Docker baseline
restored. Evidence is in `run-003/`; the approval is consumed.

The configured namespace isolation cannot be treated as feasible inside LXC100.
The hard stop is active: do not attempt run004 on this shared host and do not weaken
the controls merely to obtain a pass. Any continuation must choose a different
execution boundary, such as a VM or another isolation design, and begin with a new
architecture and evidence review.
