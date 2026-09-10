# Aster ARR First Repair Decision

> Status: graduated through the production-shaped disposable execution fixture;
> live Radarr unchanged; broker stopped/boot-disabled and network path removed

## Selected candidate

The initial candidate is **dismiss one stale, completed Radarr queue record**.
It is deliberately narrower than retrying a download or reprocessing an
import. It preserves media and downloader data, does not blocklist, does not
initiate a search or acquisition, and does not alter any ARR setting.

This selection is not permission to execute it. The private producer maps a
five-minute opaque candidate reference to exactly one independently reviewed
Radarr queue record. If zero or more than one record qualifies, it emits no
candidate. Aster receives only the reference, operation, service and expiry;
it never receives the queue ID, Radarr endpoint or credential.

## Implemented broker contract

The sole request has these fields and no others:

| Field | Rule |
|---|---|
| `operation` | Exactly `dismiss_stale_radarr_queue_record` |
| `service` | Exactly `radarr` |
| `candidate_ref` | One-time broker-issued opaque reference (`radarr-q-…`) |
| `report_generated_at` | Fresh, timezone-aware report timestamp (at most 15 minutes old) |

Before an operation, the broker confirms that the mapped record is still
present, belongs to Radarr, is completed/stale rather than downloading or
importing, and has not been consumed or superseded. It rejects a stale or
future report, a future or expired candidate, a replay, a cross-service
reference, unknown fields and every bulk selector.

The adapter is limited to Radarr's single queue-record delete route. It always
sends `removeFromClient=false`, `blocklist=false`, `skipRedownload=true` and
`changeCategory=false`. The request cannot supply an origin, route, method,
queue ID or query parameter, and the adapter has no search or acquisition
operation.

The production boundary exposes only authenticated `POST /v1/dry-run` and,
when an exact server-side enable flag is set, `POST /v1/execute`. Approval
creation is intentionally absent from HTTP. The shipped service definition
binds to loopback, denies non-loopback IP traffic and sets execution false, so
installing or starting the reviewed unit does not enable a live action.

Aster exposes a separate authenticated structured endpoint,
`POST /v1/arr-repair/execute`, which accepts only `candidate_ref`. It is not an
LLM tool and cannot be selected from chat or model output. It rebuilds the
broker request only from the fresh validated report and returns a bounded
status/audit object.

## Approval, audit and non-reversibility

Execution requires a fresh, task-specific human approval after the exact
candidate, preconditions and effect are shown. A natural-language question,
past approval or an Aster response is not sufficient.

The operator-only `approve.py` command requires
`--accept-nonreversible`. It writes a two-minute approval into private broker
state and never prints or sends its internal approval reference. Approval is
consumed durably before the first Radarr inspection. Inspection failure,
precondition drift, timeout, uncertain deletion, process failure or replay can
therefore never turn one approval into a second attempt.

The broker writes an `attempt_started` record before network access and then a
bounded outcome containing only the opaque candidate reference, decision,
report age, result class and timestamp — never a title, path, queue ID,
credential or service response. The operation is intentionally non-reversible
because it removes a Radarr queue record. It stops before the request unless
that non-reversibility was explicitly accepted at the approval point.

Success requires a post-action reinspection that confirms the record is
absent. A timeout after deletion or failed verification is reported as
`outcome_unknown` or `postcondition_failed`; it is never retried under the same
approval.

## Graduation evidence and remaining gate

The final broker suite passes 61/61, including real loopback HTTP tests against
a disposable Radarr implementation. The Aster suite passes 42/42, including a
full authenticated Aster → broker → disposable Radarr path. The path proves:

- missing authorization, missing approval, unknown fields and replay cause no
  Radarr call;
- the approved attempt makes only fixed queue GET, fixed single-record DELETE,
  and verification GET requests;
- the DELETE always preserves downloader data, disables blocklisting and
  redownload, and makes no category change;
- approval state and audit output omit the queue ID, credential and fixture
  response details; and
- chat cannot select the structured execution path.

On 2026-09-09 the reviewed build was staged on TrueNAS and LXC 104 with
pre-change rollback copies. The broker ran as its dedicated unprivileged
account with execution false and remained boot-disabled. A temporary OPNsense
rule allowed only `192.168.70.10` to `192.168.20.40:9421/TCP`; the service
sandbox independently allowed only Aster beyond loopback. Missing
authorization returned `401`, and the execution route remained absent with
`404`.

The one authorized private live queue scan returned `status=none`, meaning
zero records met the exact stale/completed/imported-or-ignored eligibility
predicate. It issued no opaque candidate. Consequently no approval was
created, no execution request or Radarr DELETE was sent, and no audit attempt
exists. The empty sanitized candidate state was pushed to Aster.

Cleanup stopped and boot-disabled the broker, confirmed no listener, removed
the temporary OPNsense rule and reconfirmed the blocked Aster-to-broker path.
Aster remained healthy on the staged source.

Jason directed that the missing eligible record be handled like the prior
graduation fixture rather than by manufacturing a failure in live Radarr. A
locked-down disposable endpoint on TrueNAS supplied one synthetic stale,
completed record. The normal sanitized transport published one opaque
candidate, Aster's authenticated dry-run passed, and the operator-only
two-minute approval authorized exactly one structured Aster execution. The
bounded result was `dismissed`.

The disposable endpoint recorded exactly collection GET, fixed single-record
DELETE and verification GET for the execution. The DELETE preserved downloader
data, did not blocklist or request a redownload, and made no category change.
A replay returned `409` without another target call. The bounded fixture audit
was retained outside the broker's restored production state.

Cleanup restored the original broker environment and state, republished the
empty live candidate report, stopped the disposable endpoint, removed the
transient execution switch, left the broker stopped/boot-disabled and removed
the exact temporary firewall rule. Live Radarr was never the execution target
and was not changed. This graduates the first bounded operation against the
production-shaped disposable target required by the acceptance gate; any
future live Radarr attempt still requires a naturally eligible single record,
independent review and fresh explicit permission.
