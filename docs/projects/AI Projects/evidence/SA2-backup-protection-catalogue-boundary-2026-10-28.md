# SA2 backup-protection catalogue boundary — 2026-10-28

## Result

**SOURCE-ONLY PASS; NOT DEPLOYED.** The existing Doctor catalogue can now
publish one digest-bound `backup.protection` state derived from the complete
Doctor backup category. A fixed producer can consume only that named state as
`backup-catalog/backup` evidence.

## Publisher boundary

The Doctor collector records warning and failure counters immediately before
the existing backup checks and compares them after the category finishes. It
emits exactly one same-run state:

- `fail` when any backup check failed;
- otherwise `warn` when any backup check warned or was unavailable;
- otherwise `pass`.

The state is included in schema-3 beside the existing Aster Agent and Speech
states and remains bound to the exact sanitized aggregate report digest. The
catalogue contains no check summaries, paths, archive names, host output or
credentials. Ordinary Doctor runs without the private inherited catalogue
descriptor emit no typed events.

## Consumer boundary

The adapter opens only the fixed owner-controlled aggregate and catalogue
paths, rejects links, extra links, unsafe modes, oversize input, stale/future
times, digest mismatch, missing/duplicate checks and state contradictions. It
exposes only:

- check ID `backup.protection`;
- state `ok`, `warn`, `fail` or content-free `unavailable`;
- a 24-character aggregate report digest.

It does not run Doctor, trigger or inspect a backup, contact Proxmox or TrueNAS,
or reveal the human-readable backup lines.

## Validation and live limit

- Publisher, catalogue, adapter, producer and proposal-path tests pass
  **74/74** locally; `doctor.sh` also passes shell syntax validation.
- The service-side candidate passes **61/61** under LXC104's application Python
  and installed dependencies.
- All temporary target files were removed. No report, service, model, route,
  backup or schedule changed.
- The currently deployed catalogue still contains only
  `aster.agent_inference` and `aster.speech`. Until a reviewed publisher release
  adds `backup.protection`, the new backup adapter correctly remains
  unavailable and is not a live evidence source.

This closes the source design for backup evidence. The next release should
combine the publisher change with the held NetBox, gateway-config and backup
adapters, followed by a fresh typed catalogue and one Aster Agent restart.
Representative log evidence remains open.
