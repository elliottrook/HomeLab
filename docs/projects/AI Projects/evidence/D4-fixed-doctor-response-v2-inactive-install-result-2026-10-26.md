# D4 fixed Doctor response v2 inactive install result — 2026-10-26

## Result

The complete production response candidate is installed only in the additive
LXC104 directory
`/opt/aster-agent/candidates/fixed-doctor-response-v2-add484b0`.
It is root-owned mode `0700`; all candidate files are root-owned mode `0600`.
The installed manifest matches SHA-256
`fa8dbeb6379b24e6615e8dabe70684185e0d03824026108ff62ae79de9aaf06f`.

The isolated target-Linux caller/response suite passed `7/7` under the
installed Aster Python environment. The live caller remained at SHA-256
`aba9b11adda00e51d555aff5ec1af8d4fb94a2fa547f9435aa696121ebb9628a`.
Both `aster-fixed-doctor-caller.service` and `aster-agent.service` remained
active with zero restarts.

## Corrected staging failures

Two inactive attempts failed safely before any live change:

1. unlisted macOS AppleDouble members caused exact-member validation to reject
   the first archive;
2. the first metadata-free packet omitted two transitive imports, so its
   isolated test failed before cutover.

Both failed staging directories were removed. The final packet added only
`doctor_incident_adapter.py` and `sysadmin_investigation.py`, revalidated every
member and passed on target Linux. No service consumed either failed packet.

## Remaining gate

The source and target-Linux gates are complete. Making the deterministic answer
live requires replacing the one caller file, adding the response module and
restarting only `aster-fixed-doctor-caller.service`. That bounded restart needs
explicit approval. `aster-agent.service`, the inference service, Speech, News,
the broker database and the fixed Doctor gateway do not need a restart.
