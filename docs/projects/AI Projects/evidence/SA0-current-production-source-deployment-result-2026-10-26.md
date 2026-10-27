# SA0 current production/source deployment result — 2026-10-26

## Result

**PASS; SA0 IS COMPLETE.** The reviewed current gateway composition was
installed in LXC104 and only `aster-agent.service` was restarted. The deployed
`aster_agent.py` now matches repository commit `f3e479a1` at SHA-256
`e29e9cd3d50bc117f63698cebca60f2f9c2a3ae788430c7bb6ae31890cc18116`.
The accepted llama.cpp/SYCL model service was not restarted or changed.

## Bounded effect and rollback

The installer required the exact previous production source, unchanged
knowledge module and unchanged systemd unit before making an effect. It saved
the previous source at
`/var/lib/aster/sa0-pre-current-composite-20261027/aster_agent.py` before the
atomic replacement. That file retains SHA-256
`7edc7ff9776357d62f6eff45de2093aab5749bb38317251b404df88012c6b50c`
under a root-owned mode-0700 parent.

The transient packet was removed. No model, model settings, credential,
OpenBao state, broker policy, capability, firewall rule, schedule, Companion
bundle or other service was changed.

## Independent postchecks

- `aster-agent.service` is `active/running`, PID `16480`, with `NRestarts=0`.
- The production health endpoint returned exactly
  `{"status":"ok","service":"aster-agent"}`.
- An unauthenticated `/v1/models` request returned HTTP `401`.
- `aster-llama.service` remained `active/running`, PID `48161`, with
  `NRestarts=0`; its PID did not change across the Aster restart.
- The live source, knowledge module and unit hashes match the reviewed pins.
- The exact rollback source hash, owner and modes were independently checked.

The installer's bounded health loop emitted JSON parse diagnostics while the
new process was still starting, then accepted the correct production health
response and exited zero. The later independent endpoint check passed. This is
startup retry noise rather than a false health result.

## Runtime manifest and explained differences

The machine-readable
[runtime manifest](SA0-production-runtime-manifest-2026-10-26.json) records the
core release files, deployed hashes, service state and rollback. Eight runtime
files plus the systemd unit match the reviewed repository bytes. Four modules
intentionally remain at their known deployed predecessors:

- the incident store, incident stream and investigation modules have later
  source-only SA1/D4 validation, custody and presentation hardening;
- `lab_operations.py` differs only by an operator-only interrupted-Doctor
  reconciliation method that is absent from HTTP and model paths.

Those differences are forward candidates, not unexplained production drift.
Their installation remains subject to their own integration and effect gates.
SA0 therefore closes production/source reconciliation without silently
releasing SA1, D4, repair authority or automatic routing.
