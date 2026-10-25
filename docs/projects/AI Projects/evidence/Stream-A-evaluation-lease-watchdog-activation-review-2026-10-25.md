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
