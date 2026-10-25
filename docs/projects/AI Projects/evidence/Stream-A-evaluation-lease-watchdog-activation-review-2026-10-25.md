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

## Third implementation packet review

Platform implementation `3e843a8e839b08758314346fb73fd4827c438dbe`
and metadata/card commit `a37b83113ec27b42029d8692f6a5a79fbcd39028`
add a persistent session-owner process, correct expired-heartbeat handling,
persist bounded status and bind fresh observer output to lease identity. The
card is SHA-256
`9b20bb454cdb9c2da74735dc2c4e7655d4384ee527f4e14694f4fb34e02a6ef1`.
It is **rejected before installation** for one material observation flaw and
two transaction inconsistencies:

1. The observer tests only whether `/dev/dri/renderD128` exists inside LXC110,
   then reports `lxc110:aster-llama.service` as the sole holder. Device
   presence proves neither that a process holds the GPU nor that no foreign
   process holds it. The existing bounded host `/proc/[pid]/fd` scan must bind
   every holder to PID, start time, cgroup and executable and require exactly
   the accepted llama service.
2. The card's table lists 13 artifacts, while its install step says 12.
3. The card says to invoke “both wrappers” although it lists four. The restore
   observer is not inert and its authentication probe makes a one-token model
   request; inactive verification must never invoke it accidentally. It needs
   an explicit observe-authorization flag with inert default behavior.

The owner process is a session sentinel; the card must state that lease-state
heartbeat, rather than sentinel liveness, is the D4/M3 controller-liveness
signal. The exact GPU-holder, inert-observer and card corrections are with the
platform owner. Nothing was installed or invoked.

## Fourth implementation packet review

Platform implementation `021cab2f4683ca5224c3f6dc1930072d63489ef8`
and metadata/card commit `be96196a778481bc9d8e81dd8ee8e7ddbf07f927`
replace the false device-presence check with the bounded host process scan,
correct the artifact count and add an explicit observer gate. The revised card
is SHA-256
`3bd76773c4bd6d00c3ea8ad9ea70201fa8ea524ea337b8189765c0cf22731b9c`.

Read-only execution of the already installed full-inference holder scan found
exactly one live render-node holder with the expected llama-server executable
and LXC110 service cgroup, so the revised GPU identity contract matches the
target. The packet is nevertheless **rejected before installation** because
the observer wrapper does not forward `"$@"`. The watchdog supplies lease ID,
generation and `--observe-authorized`, but the wrapper discards them; the
observer therefore exits during argument parsing and every recovery
observation fails. Module-level tests did not exercise the deployed wrapper.

The platform owner received the one-line wrapper fix plus real inert and
authorized wrapper-invocation regressions. Nothing was installed or invoked.

## Fifth implementation packet review

Platform implementation `780c33e2471536ff0f3eb699a9dba93274808919`
and metadata/card commit `75b423d43c00611681c5e68ed07e3535c171ceb2`
correct the deployed-wrapper boundary. The reviewed inactive-install card is
SHA-256
`78fd2388168c464877c20b7abab3f99f042bb553de38f7f56d46227ef8d99210`.

Independent clean-archive validation passed all 51 focused evaluation tests.
The wrapper regression proves the restore observer is inert without
`--observe-authorized` and forwards the exact lease ID, generation and
authorization arguments when invoked by the watchdog. All thirteen source
artifacts match the card's SHA-256 pins, and the clean run left no Python
bytecode.

Read-only target preflight found all thirteen destination paths absent and
re-read the six installed evaluation-entrypoint baseline hashes exactly:

- contract `675ebb566de298334f7c612cae9af2637067930f40c0ad2c23a22e1b7e248f1b`;
- entrypoint `e4efd62036b8d26b0eb972a03f53f2cfdf6fbb6fa8a00f1c652b5803c23b5ce7`;
- adapter `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1`;
- recovery library `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725`;
- host exclusion `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61`; and
- disabled wrapper `15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af`.

The source-only packet is therefore **accepted for one inactive installation**.
That installation must create only the thirteen pinned artifacts, run the
target-Linux suite and static unit checks, invoke only the three documented
inert wrappers, and finish with every candidate service/timer disabled and
inactive and no runtime state. It must not invoke the restore observer, create
an identity, arm a timer, acquire a lease, stop a consumer or call a model.
F6 remains NO-GO until installation passes and a later activation receives its
own review and approval. The October 26 F2 exact-cycle test remains independent.
