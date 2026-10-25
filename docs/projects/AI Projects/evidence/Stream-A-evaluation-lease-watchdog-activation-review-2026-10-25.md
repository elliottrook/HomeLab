# Stream A evaluation-lease watchdog activation review — 2026-10-25

> Decision: **F6 NO-GO; implementation packet required**

## Reviewed boundary

- platform commit:
  `5d4735c166776a73e81aacb903930a00cdcc6ad6`;
- watchdog/recovery boundary SHA-256:
  `abeb57f7c9c2fc6e9da88687d8c7cef230a527e0b64c74d3e63c7bca1e29bc1b`;
- installed watchdog source SHA-256:
  `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725`;
- installed adapter source SHA-256:
  `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1`.

The card correctly separates read-only F5 preflight from an explicitly
approved F6 activation and prohibits lease acquisition, consumer changes and
model calls. It does not yet contain the implementation needed to satisfy its
own activation checks.

## Open implementation dependencies

1. No evaluation-watchdog service/timer or owner-heartbeat service/timer exists
   in the reviewed source tree or on Proxmox.
2. No watchdog or owner-heartbeat executable wrapper exists.
3. No root-custodied identity/intent format supplies the expected lease ID and
   generation to the independent process.
4. `evaluation_lease_watchdog.py` exposes the bound recovery function as a
   Python API, but its CLI accepts only `--once` and `--effect-authorized` and
   always prints `source-only`. It cannot read the fixed durable state or call
   recovery.
5. No constrained recovery callback/executor binds the watchdog decision to
   exact four-consumer restoration through the installed adapter/entrypoint.

Read-only target inspection confirmed all six expected service, timer and
wrapper paths are absent. Therefore there is nothing safe to stage or arm and
no activation approval should be requested yet.

## Required next packet

The platform owner has been asked for a source-only inactive packet containing
the exact units and wrappers, fixed state/lock/heartbeat paths, strict
root-owned identity schema, constrained restore callback and fail-closed owner
liveness. It must test missing, stale, foreign and malformed state; lost owner;
heartbeat and deadline recovery; callback failure; restart; and exact
four-consumer restoration. The install card must pin every byte and leave all
units disabled and inactive.

F5/F6 remain open. The successful inactive effect entrypoint is unchanged and
effect-disabled. The October 26 F2 run remains independently scheduled and
conditional; watchdog implementation work must not alter its timers or fresh
runtime gates.

## First implementation packet review

Platform implementation `8fa6d36fe841e5758013ad393aafdee624d91a33`
and metadata/card commit `9992271073a79cb5fd56f8ce12d465c8add0fdd2`
add the previously missing Python entrypoints, wrappers and four systemd
units. The inactive-install card is SHA-256
`a2d274c533e5db91d651fe05f26acda5762ced3237685ab30db376c1efddb9af`.
The packet is **rejected before installation** for four effect-boundary gaps:

1. The owner-heartbeat timer renews the heartbeat unconditionally from its own
   process. It does not prove that the evaluation owner remains alive, so loss
   of the owner can remain invisible while both timers continue running.
2. Only a missing heartbeat becomes `owner_present=False`. An exact-identity
   heartbeat that naturally expires raises an exception and produces
   `failed-closed`, so the expected owner-loss condition does not invoke
   recovery.
3. A recovery callback failure returns `effects=uncertain`, but the watchdog
   CLI exits zero for that result. Systemd could therefore record an uncertain
   restore as a successful service invocation.
4. Recovery trusts a prewritten restore-observation file without a writer,
   lease/generation binding or freshness field. It cannot prove that backend,
   endpoint and GPU observations are current when restoration is attempted.

The card also names a watchdog status file that the implementation never
writes. The platform owner received exact owner-PID/PID-reuse, stale-heartbeat,
uncertain-exit and fresh-observation regression requirements. No packet file or
unit was installed; F6 remains NO-GO.

## Second implementation packet review

Platform implementation `2360218042ff3bccc7a2ae2dc12642fd69bcdbbb`
and metadata/card commit `f823cd940c489a741bc7ca7bb66589c2d8930b00`
add PID/boot/start-time/process identity, nonzero uncertain exits and a fixed
live observer. The revised card is SHA-256
`1d4a90d87d86571764479dd2ac1034d3a0771424177adbe922a13ffaa54bb065`.
It is also **rejected before installation**:

1. Target read-only inspection proved that the fixed authentication probe
   exists in LXC110, but the fixed idle and GPU-holder probes do not. The live
   observer cannot succeed on the actual target.
2. The claimed expired-heartbeat transition is absent. The loader no longer
   rejects expiry, `run_watchdog_once` treats the existing expired record as an
   alive owner, and the new test explicitly accepts `expires_epoch == now`.
3. No persistent evaluation-owner runner or service exists to supply the PID,
   boot ID, start time, command and unit identity. The activation card cannot
   construct a meaningful owner identity from the current system.
4. `STATUS_PATH` remains declared and card-listed but unwritten. The observer
   output also omits the requested lease ID and generation binding.

The platform owner received the exact target-probe, expired-heartbeat,
owner-runner, status and observation-binding corrections. Nothing was staged,
enabled or armed.
