# M1/D4 fixed Doctor producer — cutover and bounded canary card

**Date:** 2026-10-25  
**Status:** approval-ready; no Mac source replacement, Doctor invocation or report publication has occurred under this card  
**Candidate manifest:** `scripts/deploy/fixed-doctor-producer-manifest.json`, SHA-256 `47850a5b3d12d560839a34609c2e25b738d111e5668ecb6d982997a83c8012d1`

## Purpose

Promote the reviewed single-run Doctor producer into the Mac source checkout,
then verify it once without running the full scheduled-report wrapper. The
canary invokes Doctor exactly once and publishes the existing schema-1
aggregate plus the new digest-bound schema-2 fixed-check sidecar. It does not
activate the installed caller/gateway services or create an AI-PAM identity,
capability or grant.

## Frozen change

The manifest permits exactly two atomic file replacements:

| Target | Required predecessor | Candidate |
|---|---|---|
| `/Users/jelliott/lab/homelab/scripts/build-aster-health-report.py` | `cb05a3bc3cfafc4f69ce12c033c36aa8d6bab41ebdace5a55e1a9392715127b8` | `8ec44150b11e362896ad9662fed9cb0b26798c28a56ec6d447208d5cf67e23d7` |
| `/Users/jelliott/lab/homelab/scripts/scheduled-report.sh` | `32a52808739cfac0bff260cdc1cba78ad1f7f785101de559eb29b0dcca96b3e0` | `76611cdef24340ec13dd8275c7237cb8d8f8b61d38a97a6ed09afebb500b544e` |

Both targets remain `jelliott:staff` mode `0755`. The existing
`ca.yampy.homelab-report` LaunchAgent remains loaded, idle and scheduled at
08:15. Its plist, schedule and launch state are not changed.

The cutover first creates a new mode-0700 rollback directory under
`~/lab/private-backups/aster-stream-a/`. It retains the two exact predecessor
files, the four local report-path states (including explicit absence), and an
LXC104 root-only checkpoint of the two final remote report-path states. The two
fixed remote staging paths, `/var/lib/aster/health/latest.json.new` and
`/var/lib/aster/health/aster-inference.json.new`, must be absent before the
canary. A failed precondition stops before replacement.

## Bounded canary

After exact installed-hash verification, run only the manifest's builder
command with a 930-second outer deadline. It:

- invokes `doctor.sh` once;
- retains the private transcript locally at mode `0600`;
- writes the local schema-1 report, schema-2 sidecar and content-free result;
- publishes only `/var/lib/aster/health/latest.json` and
  `/var/lib/aster/health/aster-inference.json` through the existing fixed
  SSH/`pct exec 104` path; and
- performs no inference or model request.

Do not invoke `scheduled-report.sh` for this canary. That wrapper also runs
drift/certificate checks and may call `backup-alert`; its latest launchd exit
is already `1` after a Mail AppleEvent timeout. Bypassing that wrapper makes
the producer result independent of the known notification fault. The next
ordinary 08:15 run remains the observation point for the integrated scheduler
and alert path.

## Pass conditions

1. The validator and focused producer suite pass before replacement.
2. The LaunchAgent is idle and its label, command and 08:15 schedule match the
   manifest.
3. Both predecessor hashes, custody and modes match.
4. The two candidate hashes match after atomic replacement.
5. The canary finishes inside 930 seconds and writes a content-free
   `doctor_exit` result. A non-zero Doctor result is allowed only as observed
   health state; builder/publication failure is not.
6. Local and remote schema-1/schema-2 pairs have equal timestamps and an exact
   schema-1 digest binding. The schema-2 object contains only its allowlisted
   fields and fixed `aster.agent_inference` state.
7. Remote files remain root:`aster` mode `0640`; local files remain mode
   `0600`. Both remote `.new` staging paths are absent after success.
8. Aster Agent and the normal broker remain healthy. Both fixed-Doctor services
   remain disabled/inactive, their sockets remain absent and the broker retains
   zero fixed-Doctor rows.
9. F2/F6 timers, leases, locks and B60 services are unchanged.

## Rollback

On replacement, validation or publication failure:

1. restore the two exact Mac predecessor files atomically from the new
   checkpoint and verify their hashes, custody and modes;
2. restore each local and final remote report path to its checkpointed bytes or
   prior absence;
3. remove only the two fixed remote `.new` staging paths, then verify both are
   absent;
4. verify the LaunchAgent remains idle with the unchanged 08:15 schedule;
5. verify Aster/broker health and absence of fixed-Doctor runtime state; and
6. retain a content-free failure phase and the checkpoint for review.

Do not relaunch the scheduled report to prove rollback. The rollback does not
repair the pre-existing Mail notification fault.

## Explicit exclusions

This card does not authorize a broker source replacement or restart, service
activation, AI-PAM enrollment/grant, model route/call, Companion change,
schedule modification, alert repair, B60/F2/F6 work, Git push or deletion of a
rollback checkpoint.

## Offline validation

- frozen-manifest tests: **4/4 pass**;
- live read-only predecessor/schedule validation: **pass**;
- focused producer/scheduler tests: **7/7 pass**;
- candidate and predecessor hashes: exact as tabulated above.

The canary is a production read and report publication, so execution remains a
separate explicit change decision.
