# Operate and recover the knowledge wiki

> Authority: reviewed-wiki-runbook
> Reviewed: 2026-09-12

## Add equipment or a source

Sign in at `https://wiki.elliottrook.com`. Enter an equipment title and stable
source ID, then enroll its bounded URL, Git document or manual upload. The
accepted complete source is its human equipment page. Review the normalized
preview, provenance and licence decision before accepting. Acceptance queues
work; it does not bypass validation or directly replace the live corpus.

## Review quarantine

Open the source dashboard and read the bounded failure reason and preview.
Check hostname, path scope, media type, size, licence and provenance. Correct
the candidate or authoritative source and retry it. Do not edit accepted locks,
disable secret checks or move quarantined bytes into the corpus.

## Correct source material

Correct the complete human source, not a generated mirror entry. Allow the
daily collector to retain the new original, validate it and atomically publish
the new accepted hash. Rebuild the mirror only from that accepted state. Aster
must continue linking every derived claim to the complete source and locator.

## Resume a run

Use the source dashboard to identify interrupted work. Confirm no newer run has
already accepted the same source, then resume the recorded run ID through the
collector CLI. Verify the accepted corpus afterward. Never delete staging to
make an interrupted state disappear.

## Restore service

Restore the private human repository plus protected collector state and
retained originals first. Run accepted-corpus verification. Rebuild and verify
the non-authoritative mirror from those inputs, then rebuild Aster's validated
snapshot. Start the intake, daily collector timer and monthly corpus-health
timer only after their checks pass. Authentik, private DNS, NPM and the narrow
NPM-to-backend firewall path remain independent prerequisites for browser use.

## Roll back bad input or derived output

For a bad upstream acceptance, invoke the collector's last-good rollback and
verify before resuming collection. For a bad generated summary, reactivate the
retained mirror last-good tree, verify every claim against its source, rebuild
the Aster snapshot and confirm retrieval plus health. Retain the rejected state
for diagnosis; never promote generated content to authority.
