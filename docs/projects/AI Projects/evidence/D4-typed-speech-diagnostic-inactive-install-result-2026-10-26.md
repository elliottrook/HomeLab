# D4 typed Aster Speech diagnostic — inactive source install result

**Date:** 2026-10-26  
**Result:** PASS  
**Restart:** none

## Applied change

The frozen three-file source bundle was installed in the primary Mac checkout
without running Doctor or publishing a catalogue:

| Path | SHA-256 | Custody |
|---|---|---|
| `scripts/build-aster-health-report.py` | `56fb918a6deee8273321fa811199fabaf5a0b6963ea2d9221da944ca401686fd` | `jelliott:staff` 0755 |
| `scripts/doctor.sh` | `507ee43484f7814358c870b34e8e7e77e11cc2eba513fcdac8b78d3e7dc8c40e` | `jelliott:staff` 0755 |
| `services/aster-agent/diagnostic_catalogue_v3.py` | `3a2db11871a5500fc47411007c119b210491e2c1f645f075cf84e9d490e6d69c` | `jelliott:staff` 0644 |

The installer itself had SHA-256
`140d475f4986dc8b5219cfd649ec2221a6913978fa08b37e1fbdd8b13702949f`.
It created a mode-0700 private rollback checkpoint at:

`~/lab/private-backups/aster-stream-a/typed-diagnostic-v3-preinstall-20261026-131558`

That checkpoint contains both exact predecessor files and an absence marker
for the added module.

## Validation

- both predecessor hashes and the module's prior absence matched before change;
- all three installed hashes, modes and owners match the frozen manifest;
- `bash -n` and Python compilation passed;
- a synthetic one-run fixture produced digest-bound schema-2 and schema-3
  output containing only `aster.agent_inference` and `aster.speech` states;
- private fixture words were absent from the schema-3 file;
- the scheduled LaunchAgent remained `not running`, with the same recorded
  run count and pre-existing exit 1;
- `/var/lib/aster/health/diagnostic-catalogue.json` remains absent; and
- Aster Agent is active with `NRestarts=0`.

## Boundary

This is an inactive source installation. It did not invoke Doctor, change the
08:15 schedule, publish or read a catalogue, restart a service, create an
identity or grant, call a model, change routing or touch B60.

The next step is a separately bounded one-run canary that checkpoints the
current local and LXC104 report files, invokes the installed builder once with
schema 3 explicitly selected, validates the two fixed named states and rolls
all report paths back on any failure. A speech reader/capability remains later.
