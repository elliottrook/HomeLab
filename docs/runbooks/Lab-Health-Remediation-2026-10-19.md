# HomeLab Health Remediation — 2026-10-19

## Trigger

The 08:15 scheduled report identified four failures: Jellyfin Integrity
authentication, Bazarr direct health, Audiobookshelf health, and the protected
TrueNAS configuration export. The email repeated each failure because its
alert builder collected red lines from both Doctor's primary checks and its
summary sections.

## Root causes and repairs

- The `jellyfin-integrity` API key still existed and matched Jellyfin's
  registry. Its mode-0600 `config.json` ended with a literal `\n` sequence,
  so JSON loading failed before authentication. The malformed file is retained
  as `config.json.before-health-20261019`; the invalid suffix was removed
  without rotating or exposing the credential.
- Bazarr was running, Docker-healthy, policy-compliant, and reachable on its
  deliberate `192.168.20.40:6767` binding. Doctor incorrectly probed
  `127.0.0.1:6767`; the probe now uses the actual direct-service address.
- `unified-audiobookshelf-shadow` had exited cleanly during the October 18
  Docker restart because both its compose and container policies were
  `restart: no`. The live compose file is backed up as
  `compose.yaml.before-health-20261019`; the service now uses
  `unless-stopped`, is running, and returns HTTP 200 from `/healthcheck`.
- The configuration export's Audiobookshelf online-copy step consequently
  could not execute in the stopped container. After service recovery, a fresh
  export completed with 19 applications, 4,151 verified files, 22 verified
  SQLite databases, a 1,437,662,943-byte archive, and no media content.
- Scheduled alert extraction now removes Doctor's aggregate final-status rows
  and de-duplicates identical red findings, so one failure produces one email
  line.

## Validation

A complete post-repair Doctor run reported 87 passed, two existing warnings,
and zero failures. Jellyfin Integrity authenticated against its existing key;
Bazarr passed container, HTTP and policy checks; unified-media passed its
Audiobookshelf/CWA checks; and the new TrueNAS export reported age 0.0 hours.
The remaining warnings are the separately tracked Aster Wiki quarantine and
the pre-existing dirty workspace.
