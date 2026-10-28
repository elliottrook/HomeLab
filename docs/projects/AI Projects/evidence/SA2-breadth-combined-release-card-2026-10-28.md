# SA2 combined breadth release card — 2026-10-28

## Decision

**READY FOR ONE REVIEWED LIVE RELEASE; NOT YET INSTALLED.** This transaction
connects the completed NetBox, gateway-configuration, backup-protection and
sanitized gateway-log evidence paths. It makes no model, routing or repair
change. It needs one Aster Agent restart and enables one root publisher timer.

The exact source is bound by
`services/aster-agent/deploy/sa2-breadth-release-manifest.json`, whose SHA-256
is `431b71ed93b94ad0d252fcb3dde1f3b925139855e60576ed7a8c3f80fb3c4763`.
Its validator passes and rejects source, target, predecessor, file-count or
runtime-boundary drift.

## Exact scope

Four Mac publisher files are installed into the existing live HomeLab checkout:

| Target | Before | After |
|---|---|---|
| `services/aster-agent/diagnostic_catalogue_v3.py` | absent | `a8e81354…88dc` |
| `scripts/doctor.sh` | `f501dfca…c96` | `6dee983d…f0be` |
| `scripts/build-aster-health-report.py` | `2ba81349…0b5` | `cbfd5415…4947` |
| `scripts/scheduled-report.sh` | `f5e87254…bf6` | `6595bd5e…fb7` |

Nine LXC104 files are installed:

| Target | Before | After |
|---|---|---|
| `netbox_incident_adapter.py` | absent | `0b9b7be0…fc99` |
| `gateway_config_incident_adapter.py` | absent | `ebeeccaf…a6a3` |
| `backup_catalogue_incident_adapter.py` | absent | `64bbda06…bb28` |
| `gateway_log_incident_adapter.py` | absent | `cde0b928…6c1` |
| `sysadmin_investigation.py` | `1f903f4a…81ed` | `0720d6b2…1182` |
| `sysadmin_registered_producer.py` | `27175ab0…1c96` | `dd89e1d5…342a` |
| `/usr/local/libexec/produce-aster-agent-log-report.py` | absent | `ebc8221b…e9cf` |
| `aster-agent-log-report.service` | absent | `ce21f141…3e01` |
| `aster-agent-log-report.timer` | absent | `057e99fd…3cb` |

The installed LXC dependencies `diagnostic_catalogue_v3.py` and
`source_reports.py` already match the reviewed source hashes `a8e81354…88dc`
and `7a85c52a…add2`. The fixed NetBox and Forgejo reports are present with
root/Aster custody. The sanitized log report is correctly absent before its
first root publication.

## Transaction

1. Recheck every predecessor hash, absence assertion, owner/mode, Aster health,
   zero restart count, accepted llama health/PID and whole-host lease readiness.
2. Create separate owner-only Mac and LXC checkpoints before the first
   replacement. Record absence markers for every addition.
3. Stage all candidate files with their final owner/mode and recheck every
   digest before atomic replacement.
4. Reload systemd, run the sanitized log publisher once, validate its fixed
   root:Aster `0640` report, then enable and start only its five-minute timer.
5. Run the new health builder once against the new Doctor source, producing and
   publishing the aggregate, schema-2 sidecar and three-check schema-3
   catalogue. A warning or failure reported by Doctor is valid evidence; a
   publisher/schema/custody failure is a transaction failure.
6. Restart only `aster-agent.service` once. Do not restart or alter llama.cpp,
   Speech, News, the Companion or any model.
7. Validate exact installed hashes, Aster health and zero service restart
   failures; unchanged llama PID/health; active log timer; fresh log report;
   fresh digest-bound backup state; live NetBox/config/log adapters; and the
   existing Forgejo/Doctor/gateway/inference paths.
8. Run one bounded no-effect investigation across representative evidence.
   Every decision must retain `authority=none` and `effect=none`; no automatic
   route, repair or generic tool authority is permitted.

## Preflight evidence

- All focused publisher/evidence tests, the seven builder tests, the isolated
  scheduler integration and the three manifest-validator tests pass, with
  shell syntax validation.
- The service-side candidate passed 68/68 under LXC104's application Python.
- A temporary target-Linux publisher/consumer check passed under the real root
  and unprivileged Aster identities.
- The inactive service/timer pair passes `systemd-analyze verify` on LXC104.
  The first preflight transport attempt stopped before verification because
  the temporary LXC directory was absent; after explicitly creating that
  directory, the same files verified with no diagnostic. All temporary files
  were removed and no unit was installed or enabled.
- The live Mac checkout is clean for all four target paths. The missing
  `diagnostic_catalogue_v3.py` dependency was found during preflight and is now
  explicitly included in this release.

## Stop and rollback

Any predecessor drift, unsafe custody, failed import, schema failure, publisher
failure, timer failure, restart failure, unhealthy production postcheck or
uncertain result is NO-GO. Disable and remove the new timer/service, restore
the two LXC replacements and three Mac replacements, remove only the manifest's
eight additions, reload systemd and restart only Aster Agent if it had reached
the new source. Preserve checkpoints and uncertain evidence for diagnosis.

The fresh typed catalogue and sanitized aggregate may be retained after a
rollback because the previous Aster source cannot consume the new registered
paths; they contain no credentials or journal messages. A rollback does not
authorize a model restart, route change or repair.
