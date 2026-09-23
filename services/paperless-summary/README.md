# Paperless local summary service

Deployed on LXC 115 on 2026-09-23. Paperless performs OCR; the unprivileged
worker polls its local capability broker every five minutes and publishes only
the `AI summary` custom field. Inference runs locally on LXC 110. The production
configuration enables all visible documents; the example remains synthetic-only
for safe reconstruction. No document data is sent to an external AI service.

Run `python3 -m unittest -v` here for the synthetic unit tests. Native API and
broker permission tests use `scripts/paperless/test_api_isolated.py` inside the
installed Paperless image with a disposable database and disabled networking.
See `docs/runbooks/Paperless-Summary-Operations.md` for deployment, monitoring,
identity custody, backup, revocation and recovery.

## Limits

One due document is processed per cycle. OCR up to 96,000 characters is processed
in bounded sections with reduction; empty or larger input fails visibly without
truncation. Partial summaries remain in memory and never publish on failure.
Numeric identifier redaction is incomplete for arbitrary identifiers. Generated
summaries require checking against originals; only synthetic quality has been
evaluated because the service had no real corpus at deployment.

The root-owned broker is a privileged boundary. It uses native Paperless read
permissions and a fixed source-hash-checked custom-field writer, not a general
API mutation token. The model cannot invoke tools. A complete scan reconciles
source removal and permission changes; delivery is idempotent. Errors use bounded
retry, status is atomic, and a single-worker lock prevents overlap.

## Service-only offsite backup

The strict exporter accepts only reviewed release hashes and an exact allowlist
of code, units, pinned reconstruction templates and non-secret example config.
Database, documents, OCR, summaries, credentials and runtime state are excluded.
Whole-guest recovery remains local and on TrueNAS. Refresh the export manifest
and service archive after deploying a changed release; verify its offsite hash.
