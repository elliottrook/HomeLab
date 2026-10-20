# F2 exact-cycle activation result — 2026-10-21

Date recorded: 2026-10-20
Status: approved one-cycle activation pending the 2026-10-21 elapses.

## Installed pins

The corrected coordinator is installed at
`/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` with
SHA-256
`fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356` and
`root:root` mode `0644`.

The previous coordinator is preserved at
`/root/aster-f2-failure-phase-rollback-20261021/f2_scheduled_release_candidate.py`
with SHA-256
`aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23` and
`root:root` mode `0600`.

The active, nonpersistent timer units are:

| Unit | SHA-256 | State | Next elapse |
|---|---|---|---|
| `f2-preflight-prepare-20261021.timer` | `184cd8b0f96644519ccf666d22dcfc7cf4799dbc8457e5f68f35dd25a98c6dab` | loaded, active, enabled | 2026-10-21 01:15 PDT |
| `f2-preflight-final-20261021.timer` | `a18f8a797c4f4148aa5450e5569545fac1b0c7a2266550ebb5b02912a793cf9d` | loaded, active, enabled | 2026-10-21 01:20 PDT |

Both units are `Persistent=no`, have zero randomized delay, and were checked
with `systemd-analyze verify` and `systemd-analyze calendar` before activation.

## Safety post-check

- The daily F2 timers and October 20 one-shot timers remain inactive/disabled.
- The F2 services were not started; their prior failed status remains unchanged.
- October 20 terminal evidence remains present and was not cleared.
- The current preflight snapshot, F2 receipt, and cooperative lease lock remain
  absent.
- No F2 coordinator, observer, zstd, or model process was started by the
  activation. The existing production llama-server remained untouched.
- No production service, backup schedule, lease, receipt, model endpoint, or
  historical state was changed.

At the one-shot outcome or 01:40 hard deadline, both date-specific timers must
be disabled and stopped, then reconciled observation-only. No automatic retry
is permitted. Rollback is limited to restoring the coordinator checkpoint and
removing these two date-specific timer units.

This result is a local record. No remote push was performed.
