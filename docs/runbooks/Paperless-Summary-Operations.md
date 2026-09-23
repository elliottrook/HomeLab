# Paperless summaries: operation and recovery

Status: deployed 2026-09-23; timer enabled in all-document mode. User acceptance follow-ups remain in the archived project record.

## Architecture and access

LXC 115 hosts Paperless (`paperless-ngx-webserver-1`, private port 8000), a local
Unix-socket broker, and an unprivileged five-minute summary worker. The model
runs on LXC 110 at `192.168.70.12:11435`. There is no new network listener.

The worker has no Docker access, Paperless token, database credentials or general
write capability. The root-owned broker exposes only page/read/publish operations.
It uses a fixed Docker exec command and trusted source code; callers cannot supply
paths, commands, token values, field identifiers, or arbitrary Paperless updates.
The socket checks the peer UID and is restricted to root/the worker.

The broker is privileged infrastructure. Compromise of its root-owned code or
host root is outside the worker permission boundary. Review changes to the broker
like any administrative service. Central AI-PAM is not deployed in this project's
recorded baseline; this local capability bridge is the interim integration.

The `ai-paperless-reader` identity has only `documents.view_document` and explicit
object grants. Its token stays in Paperless's database and broker process memory.
A Document Added workflow adds view permission while preserving ownership and
other grants. Existing documents require separate explicit onboarding.

`ai-paperless-summary-writer` is a non-admin identity with only add/change
custom-field-instance permissions. It has no password or API token. Its active
state and exact permissions gate the source-local writer. The writer touches
only the named long-text `AI summary` field, requires current read permission and
a matching source digest, and bypasses file-moving model signals. Other metadata,
originals, OCR text, ownership, tags and retention are untouched.

The dedicated inference key is separately revocable. It is root-only in
`/etc/paperless-summary/llama-api-key`, passed to the worker through systemd
LoadCredential. Keys never belong in Git, shell output or incident reports.
Root-controlled code/config are under `/opt/paperless-summary` and
`/etc/paperless-summary`; derived state is under `/var/lib/paperless-summary`.

## Use and quality limits

Read `AI summary` on the document's normal Paperless details page. No separate
summary website or authentication surface is required. Treat generated text as
an aid and consult the original before acting on dates, amounts or obligations.

The approved production configuration processes all visible documents. Reconstruction
starts with the supplied synthetic-only example and requires validation before
promotion. One labelled warranty fixture remains as a demonstration; the corpus
contained no real documents when deployed.

OCR up to 96,000 characters is processed in bounded sections, then reduced into
one summary. Larger or empty OCR fails visibly with retry; nothing is silently
truncated. Numeric-ID redaction is incomplete for arbitrary identifiers. Model
quality has synthetic evidence only; Jason owns first real-document acceptance.

A complete scan precedes local-state reconciliation. Removed/inaccessible records
are purged from the derived store. Changed OCR/metadata invalidates the summary;
stale-source publication is refused. Failed inference publishes an unavailable
status only to the dedicated field; partial summaries are not published. One due
document is processed per cycle, with bounded backoff and a single-worker lock.
The local delivery ledger makes successful write-back idempotent.

## Monitoring

Run the source-local `scripts/paperless/check_summary.py` on LXC 115. It returns
non-secret service/HTTP/status freshness and backlog information. No OCR, summaries
or credentials appear in its output. Worker status is an atomic JSON file; a failed
cycle or a status older than 15 minutes requires attention. The gateway journal
records only action, caller UID and success, never request/response bodies.

The repository Doctor hook calls this checker through Proxmox and retains its
existing reporting channel. Installation into the separate operational checkout
is awaiting path-specific approval after an automatic approval-review rejection. A simulated inference failure and its recovery verified unhealthy/healthy
status without exposing document content.

## Stop and recover

With approval, stop/disable `paperless-summary.timer`, let any current oneshot
finish or stop it, then stop the broker. Paperless continues to operate independently.
To prevent future reader grants, disable only `AI summary reader access` workflow.
To revoke read access, deactivate `ai-paperless-reader` and delete only its token.
To revoke write-back, deactivate `ai-paperless-summary-writer`. Do not delete
human users, documents, custom fields, or backups as incidental rollback.

Preserve code/config and the derived SQLite file before changing versions. Restore
those files with their original ownership/modes while the worker is stopped.
Already-written summaries are derived data: leave them in place when rolling back
unless a separately reviewed correction explicitly targets that field. Source
hash checks must pass before any regeneration replaces a summary.

The whole LXC backup covers code, root-owned keys, state and Paperless volumes.
The 2026-09-23 post-deployment restore verified both SQLite databases, service
release hashes, key permissions, timer/broker state and two successful login
checks from the TrueNAS archive. Recovered guests must remain disconnected
from production networks until their identity and services have been inspected.

## Deployment validation and remaining acceptance

Native API/one-field broker tests, end-to-end OCR and summaries, denied access,
revocation, inference failure/recovery, restart, long-document unit tests and
post-deployment isolated recovery passed. HTTPS, private DNS, Authentik,
Homepage and NetBox are deployed. See the archived project for exact evidence.

Personal passkey SSO acceptance and first real-document quality
review remain operator acceptance tasks. Do not describe these as tested.

## Service-only offsite policy

LXC 115 whole-guest archives stay local and on TrueNAS. The relay explicitly
excludes them; seven historical offsite archive versions were removed. The
reviewed exporter accepts only an exact hash manifest and filename allowlist of
service code/units and non-secret reconstruction templates. Refresh that export
following a service release, place it under TrueNAS backup/paperless-service and
verify the encrypted relay's decrypted SHA-256. Never include database, originals,
OCR, summaries, credentials, runtime state or raw environment files.
