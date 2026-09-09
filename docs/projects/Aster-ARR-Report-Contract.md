# Aster ARR Sanitized Report Contract

This is the only input for Aster ARR live-state reading. It is
not an ARR API client and must never contain credentials, endpoints, paths,
titles, raw errors, request history or raw service responses.

## Producer boundary

The producer runs outside Aster with private, bounded service
access. It writes an atomically replaced, regular JSON file owned by the
operator and not writable by group or other users. Aster gets read-only access
to that one directory; it receives no credential, network route or arbitrary
report path. Symlinks are rejected.

## Version 1 payload

```json
{
  "schema_version": 1,
  "generated_at": "2026-09-09T12:00:00Z",
  "services": {
    "radarr": {
      "status": "warning",
      "coverage": ["health", "queue"],
      "queue_pending": 2,
      "queue_errors": 1,
      "import_pending": null,
      "import_errors": null
    }
  },
  "repair_candidates": []
}
```

Only `sonarr`, `radarr`, `lidarr`, `prowlarr`, `sabnzbd` and
`jellyfin` are valid service names. Status is one of `healthy`, `warning`,
`failed` or `unknown`. `coverage` declares exactly which state is measured:
`health`, `queue` and/or `import`. Counters for a scope outside coverage must
be `null`, so a missing measurement can never look like an empty queue or a
clean import. Unknown keys invalidate the report rather than being silently
passed to Aster.

`repair_candidates` is an exact list containing zero or one item. The sole
allowed item has `operation`, `service`, `candidate_ref` and `expires_at`.
Operation is exactly `dismiss_stale_radarr_queue_record`, service is exactly
`radarr`, and the reference matches `radarr-q-` plus 16 base32 characters. It
expires no more than five minutes after report generation. The candidate
contains no queue ID, title, path, endpoint or credential. Zero or multiple
eligible private records result in an empty list.

The current freshness window is 15 minutes. The reader returns
an explicit unavailable/stale result rather than attempting a refresh or any
network request.

Before mounting a producer output, validate it offline with
`scripts/validate-aster-arr-report.py /path/to/candidate.json`. The validator
contacts no ARR service and prints only the safe projected values.

## Acceptance tests

- Fresh valid aggregate report is returned unchanged except for its fixed safe
  projection.
- Stale, future, malformed, oversized and unsupported-version reports are
  unavailable.
- Unknown fields, unknown services, strings in counters and private detail
  fields are rejected.
- Group- or world-writable files and symlinks are rejected.
- Candidate state is regular, non-writable by group/other, exact-schema,
  short-lived and reduced to at most one opaque reference.
- The report reader has no HTTP client, service key, endpoint or filesystem
  traversal input.
