# D4 typed Aster Speech diagnostic — frozen bundle and Linux staging

**Date:** 2026-10-26  
**State:** source bundle frozen and isolated Linux validation passed  
**Production effect:** none

## Frozen target shape

`scripts/deploy/typed-diagnostic-v3-manifest.json` pins source commit
`7e24b762e022a2fc3da4abd84957ecb19a781ff1` and exactly three Mac checkout
paths:

| Action | Target | Required predecessor | Candidate |
|---|---|---|---|
| replace | `scripts/build-aster-health-report.py` | `8ec44150…` | `56fb918a…` |
| replace | `scripts/doctor.sh` | `c3f4d961…` | `507ee434…` |
| add | `services/aster-agent/diagnostic_catalogue_v3.py` | absent | `3a2db118…` |

The two replacements retain `jelliott:staff` mode 0755. The added Python
module is `jelliott:staff` mode 0644. Rollback restores both predecessor files
and removes only the new module after confirming its exact candidate hash.

The manifest explicitly excludes LaunchAgent or schedule changes, a Doctor
run, catalogue publication, service restart, identity or grant changes, model
calls, automatic routing and Git push. Its validator rejects source drift,
target broadening, changed custody/modes, missing predecessor pins, weakened
rollback or missing exclusions. The focused manifest suite passes **4/4**.

## Isolated target-Linux validation

The first two test archives were incomplete: one omitted the existing
structured adapter and the second omitted that adapter's existing
`sysadmin_investigation.py` dependency. Both stopped at import, and their
remote archive and root-only staging directory were removed by the cleanup
trap. Neither failure exercised or rejected the candidate.

The complete 37,827-byte archive had SHA-256
`19c7fcadc8dfcde288a877f49ff4ffe87b096793ed7c83e8d9a3b41f55e66ad9`.
In a new root-only Proxmox staging directory under Python 3.13.5:

- the transfer hash matched;
- the structured producer plus catalogue suites passed **13/13**;
- the frozen manifest validator passed;
- `bash -n scripts/doctor.sh` passed; and
- the archive and staging directory were removed afterward.

An independent read-only postcheck reported `TARGET_STAGING_CLEAN` for all
three attempt paths.

## Result and next gate

**PASS for the frozen inactive bundle.** No final path, LaunchAgent, schedule,
service, identity, grant, report, model route or B60 state changed.

The next operational step is one bounded Mac checkout installation with a
fresh mode-0700 rollback checkpoint. It must recheck the exact two predecessor
hashes and the new-module absence, replace/add only the three frozen files,
run local syntax and fixture tests, and leave the 08:15 LaunchAgent idle and
unchanged. A later catalogue canary is a separate effect because it runs
Doctor and publishes a new production file.
