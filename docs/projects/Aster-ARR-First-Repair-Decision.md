# Aster ARR First Repair Decision

> Status: proposal rehearsal only — no broker, credential or live action is
> enabled

## Selected candidate

The initial candidate is **dismiss one stale, completed Radarr queue record**.
It is deliberately narrower than retrying a download or reprocessing an
import. It must preserve media and downloader data, must not blocklist, must
not initiate a search or acquisition, and must not alter any ARR setting.

This is a planning selection, not permission to execute it. Aster's existing
read capability cannot reveal a queue ID. A future private producer/broker may
map a short-lived opaque candidate reference to exactly one reviewed Radarr
queue record; Aster receives only that reference, never an ID, endpoint or
credential.

## Future broker contract

The sole future request has these fields and no others:

| Field | Rule |
|---|---|
| `operation` | Exactly `dismiss_stale_radarr_queue_record` |
| `service` | Exactly `radarr` |
| `candidate_ref` | One-time broker-issued opaque reference (`radarr-q-…`) |
| `report_generated_at` | Fresh, timezone-aware report timestamp (at most 15 minutes old) |

Before a real operation, the broker must confirm that the mapped record is
still present, belongs to Radarr, is completed/stale rather than downloading or
importing, and has not been consumed or superseded. It must reject a stale or
future report, a replay, a cross-service reference, unknown fields and every
bulk selector.

The future operation is limited to Radarr's documented single queue-record
delete route. Its adapter must explicitly send all of these fixed flags:
`removeFromClient=false`, `blocklist=false`, `skipRedownload=true` and
`changeCategory=false`. That preserves downloader data, declines to blocklist,
prevents a redownload and makes no category change; it must not call a
grab/search endpoint. The locally implemented proposal module contains **no
HTTP client or execution code**; it exists only to rehearse this contract.

## Approval, audit and rollback

Execution requires a fresh, task-specific human approval after the exact
candidate, preconditions and effect are shown. A natural-language question,
past approval or an Aster response is not sufficient.

The broker must write a bounded audit record containing the opaque candidate
reference, decision, report age, result class and timestamp — never a title,
path, queue ID, credential or service response. The operation is intentionally
non-reversible because it removes a Radarr queue record. It must stop before
the request if that non-reversibility is not explicitly accepted at the
approval point.

## Rehearsal tests

`services/aster-arr-broker/test_proposal.py` proves that the proposal is dry
run only and rejects stale/future reports, arbitrary URLs, unknown fields,
wrong service/operation and non-opaque references. No target system is called.
