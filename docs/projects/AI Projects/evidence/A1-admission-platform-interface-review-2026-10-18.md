# A1 admission/platform interface review — 2026-10-18

**Decision: A1 live admission remains BLOCKED.** This is a read-only source
comparison, not a host observation, installation, lease or benchmark result.
The Stream A checker is an offline consistency check; a passing result cannot
authenticate platform evidence or authorize a model call.

## Pinned comparison

- Stream A source: `codex/aster-stream-a-handoff` at `ede3c268`,
  `scripts/aster-adaptive/full_path_admission.py` SHA-256
  `d849f395af73d906428c7f3c4b4bb303e7ad14d019c80b0bfc907099404c65f7`.
  It was introduced on the Stream A lineage at `d5510733`; absence from the
  platform branch is not evidence that it was intentionally retired.
- Platform source read from `codex/release-registry-stream-a` at `74645f0d`:
  `scripts/local-ai/application_b60_lease.py` SHA-256
  `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d`;
  `application_b60_lease_recovery.py` SHA-256
  `b70779a816915ec0fa8cfb66d122ea47e96a607a68bf056d26cda75e237b9311`;
  `application_b60_watchdog.py` SHA-256
  `3447d490ec396dee45191a5294537f2132deac6578e3e30376f6f6980a98e8d2`.
  The platform checkout has unrelated uncommitted work; this review did not
  modify or include it. Recheck exact source pins before integration.

## Contract mapping and missing proof

| Stream A preflight needs | Platform source currently represents | Integration decision |
|---|---|---|
| Application-only mode, lease ID/generation, accepted backend, isolated consumers, sidecar source/identity | `ApplicationLeaseReceipt` and `validate()` represent these observations; the controller's host receipt binds an active state and short watchdog status | Reuse the platform's authenticated, fixed-path callback. Do not synthesize the Stream A `observed` booleans from a caller-supplied JSON object. |
| Same-cycle source-bound backup and mirror proof | `ApplicationPreLease.backup_receipt` and the application receipt carry a reference. The platform live-drill gate explicitly says the trusted pre-lease producer is still missing | Root-owned producer must obtain and validate the source receipts itself. Mere file presence or an arbitrary digest cannot satisfy this gate. |
| Held host lock and no new starts | Platform controller creates an application state and lock under common host exclusion; active callback checks lock custody and state identity | Observe the *current* lock, state and competing jobs at the host. A cached lease receipt is insufficient. |
| Independent recovery trigger and completed restoration by 04:15 | Persisted state has `restore_start_epoch` and `restore_deadline_epoch`. The recovery CLI waits until `restore_start_epoch`; `restore_deadline_epoch` is the hard completion deadline. Platform `ApplicationReceipt.watchdog_deadline_epoch` is populated from `restore_deadline_epoch` | **Do not map** the receipt's `watchdog_deadline_epoch` to Stream A's `watchdog.deadline_at`, which its checker treats as a recovery *trigger*. That would grant the whole restore interval to the batch. A future source-bound projection must use `restore_start_epoch` for the trigger and separately prove the hard deadline, measured worst-case restore duration and timer/observer lag. The current v2 snapshot cannot express all of that proof. |
| Test gateway, disabled tools, pinned profile, owner-only journal and headless display | Platform receipt pins sidecar identity and endpoint; Stream A guard/request/capture fixtures are separate | Keep the gateway and owner-only client observations as distinct verified sources. Platform lease validity does not prove the gateway cannot invoke tools or that a response displayed. |

The ambiguity above is a release blocker even if both source suites pass.
The Stream A checker's 15-minute recovery and one-minute lag floors are
necessary refusals, not measured operational budgets. The host controller's
15-minute interval check is likewise a configured minimum, not observed
restoration performance. Neither source proves an independently active timer
or a completed exact SYCL/auth/schedule recovery on the installed host.

## Smallest next reviewable integration

1. Platform owner publishes a source-bound pre-lease producer and a fixed,
   authenticated, content-free projection that keeps *both*
   `restore_start_epoch` and `restore_deadline_epoch`. It must reject a stale,
   mismatched or caller-fabricated backup/lease/watchdog record.
2. In offline cross-contract tests, use one pinned synthetic host receipt and
   prove the Stream A side refuses: full-stop mode; wrong lease generation;
   missing host lock/current watchdog; inactive backend; a trigger at 04:05;
   hard restoration deadline after 04:15; and an unmeasured or insufficient
   recovery/lag budget. The test must not start a lease or call a model.
3. After target-Linux review, independently demonstrate the watchdog timer
   and exact restoration in a separately approved bounded application-only
   drill. Retain its measured duration, lag and failure evidence. Only then
   revise the admission schema and ask for the separate 20-call A1 release.

Stream A owns the workload, offline checker, private answer evidence and
scoring. The platform owner owns host observations, source authentication,
lease/recovery effects and production restoration. No source-only bridge should
promote itself to an authority boundary.

## Review of the first platform correction

The platform owner added distinct receipt fields in local commit `e26b2bc3`.
That resolves the ambiguous *field names* offline, but a synthetic direct
call to its `active_admission_payload()` still returned
`aster-a1-admission.v1` at `now_epoch` 250, 251 and 299 for a state with
`restore_start_epoch=250` and `restore_deadline_epoch=300`. The active
boundary checked only that the hard deadline was still in the future. This
is a **source-level denial gap**: admission must stop no later than the
recovery trigger, not merely by the completion deadline. The same boundary
also feeds watchdog-status renewal and needs a separate boundary review.
This reproduction used the platform test module's fictional receipt/state;
it did not inspect a host, acquire a lease or call a model. Stream A sent the
exact result to the platform owner for correction and boundary tests. No
live A1 gate is advanced by `e26b2bc3`.
