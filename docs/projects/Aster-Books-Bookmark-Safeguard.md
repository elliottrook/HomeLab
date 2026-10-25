# Aster Books — shared bookmark safeguard

Owner: Jason. Started2026-10-25. Status: local candidate ready; activation gated.
Stream A for local design/build/synthetic tests; shared-server activation is a
separate deployment gate. Parent: [Aster v2](Aster-Home-Version-2.md).

## Purpose and authority

Make Aster bookmark creation truly refuse an existing book/time without editing
it, including concurrent clients. Audiobookshelf remains the bookmark authority;
HP remains the lab. Jason requested “then create the safeguard please”. This
authorizes building/testing it, not an unreviewed shared-server restart or
database migration. HP is currently in Jason's visual testing: do not navigate,
restart, deploy or start playback there while that check is underway.

## Baseline and failure

Read-only2026-10-25: TrueNAS `unified-audiobookshelf-shadow`, image
`ghcr.io/advplyr/audiobookshelf:2.36.0`, working directory `/app`, Node20.20.2,
Sequelize6.35.2, sqlite3 driver5.1.7. Actual model `User.js` create method changes
an existing timestamp's title. Current API bookmarks are stored together in a
user JSON column. A client preflight GET and matching read-back cannot certify
that POST created rather than renamed a concurrent record. Prior disposable
trial passed and is consumed; do not repeat it.

## Scope and exclusions

Build a source-hash-pinned overlay for the existing image, not a new public
service. Dedicated authenticated create-only and conditional-delete routes must
fail404 rather than silently invoke upsert after rollback. Retain existing
client routes and their deliberate edit semantics. All ordinary bookmark model
mutations must use the same fresh database transaction, not cached JSON state,
to avoid lost updates. No database schema migration, new account, exported
credential, library/download change, progress repair, public ingress, firmware,
production Kodi promotion or Git push. No speech or new visual identity.

## Design and data flow

Guarded creation requires authenticated access to a book, integer whole-book
seconds and a bounded title. Inside a SQLite IMMEDIATE transaction, reread the
user bookmark array and reject an existing book/time with409 before changing
anything. Persist only the bookmark column. New records get a fresh random
guard generation in addition to normal ABS fields; an opaque strong ETag binds
account/item/time/title/creation/generation. Conditional cleanup requires that
exact current ETag inside the same transaction; mismatch412 is not permission
to delete. Normal Aster code will use only create; conditional delete serves
the separately approved disposable test, not an automatic rollback feature.

Legacy POST/PATCH/DELETE continue their existing intended semantics, but read
fresh state inside the same database serialization boundary. Update/delete
invalidate a guard generation so edit-away/edit-back or delete/recreate cannot
resurrect an old cleanup token. No claim against a privileged out-of-band DB
editor; ordinary authenticated API writers are the tested concurrency scope.

## Pre-start risk assessment

Primary risk is corrupting or losing the shared JSON bookmark array, or causing
SQLite lock contention that delays listening progress. Controls: no real DB in
tests, exact source/image hashes, bounded per-process queue, SQLite write lock,
fresh read, field-only persistence, no automatic retry on uncertain writes,
explicit error mapping and rollback of all code together. A one-line client or
server timestamp check is insufficient. Use synthetic stale model instances,
same/different timestamp writes, legacy interactions, conditional-token replay,
forced rollback, denied access and lock failure tests. Server policy/header
authentication and item-access checks must remain on every added route.

Unknown source drift, failed checkpoint, unsupported dialect or failed safety
test stops activation. New source must never silently fall back to upsert.

## Milestones and evidence

- [x] Baseline image/runtime/routes and deployed upsert inspected read-only.
- [x] Pure mutation/ETag guard and transaction adapter implemented and tested locally.
- [x] Exact-source overlay builder and controller/router integration verified locally.
- [x] Synthetic SQLite concurrency and legacy-client compatibility proven locally.
- [x] Local package/removal proof and gated shared deployment proposal ready.
- [x] Approved isolated Linux / deployed-image runtime check: all20 synthetic tests pass.
- [x] Separately approved shared-server activation, backup/isolated restore and read validation.
- [ ] New guarded create-only UI and separately authorized disposable real-write trial.
- [ ] HP create-only UI integration, user handover and accepted operation.

## Recovery and resumability

2026-10-25: Jason approved the Linux check only. Ran all20 Node/SQLite/HTTP
tests in a disposable container from the exact pinned image
`sha256:66b24f73e543959d5df7e57bc0edbeab5e759730ec356656198b5da123468c15`.
Candidate manifest SHA256
`a489b3b041ef7652467952774a80082f3c4abd8721cd575adc184dc04792fdcb`.
The container had no network, no ports, read-only root/code, a128MiB private
tmpfs,512MiB memory, one CPU,128 PIDs, no capabilities and no-new-privileges.
Only synthetic fixtures were mounted under `/test`; no production config,
database, media or Docker socket mounts. All20 tests passed under the image's
Node20/Sequelize/sqlite3 runtime, including independent-process races, stale
instances, conditional deletion, busy/no-replay, legacy behavior and concurrent
progress writes in DELETE/WAL modes. The expected forced-busy test invalidated
only its synthetic SQLite connection. `--rm` removed the exact test container;
a read-only follow-up confirmed it is absent. Private code staging remains at
`/mnt/Media/appdata/aster-bookmark-linuxcheck-20261025` for reproducibility.
Shared Audiobookshelf remains unchanged and was not restarted. Activation,
consistent backup/restore proof and the real guarded UI trial remain gated.

Before any deployment: preserve the live Compose definition privately, exact
image digest, code files, SQLite-consistent private config backup and mounts;
never copy credentials into Git or restore a live old DB to undo test state.
Validate an isolated restore, then use a read-only code overlay with explicit
source hashes and health/version/guard checks. A brief restart/recreation of
only Audiobookshelf needs its own owner approval and an idle-listener check.
Rollback removes the known code overlay and restarts the same pinned image;
retains all legitimate new bookmarks/progress and unused inert fields. Dedicated
routes disappear404, so Aster must disable writes rather than use legacy POST.
No recovery promise until the exact package/removal procedure is tested.

## Integration and efficiency checks

No new host/IP/service/identity/firewall/NetBox record. Existing service-native
health remains the test target; before actual shared-service graduation,
reconcile current NetBox/Beszel/Doctor/backup coverage and record evidence or
an explicit existing-owner handoff. No synthetic metric service. Wiki/operator
and derived Aster mirror updates follow accepted live behavior, not a proposal.
Source and tests are local; raw user responses/keys/config do not enter them.
Measure transaction wait/hold time and unchanged non-bookmark columns; fail
closed on busy rather than blind request replay. No GUI is added in this slice;
later HP controls retain the approved floating-icon Aster skin language.

## Handover / current next step

Shared bookmark buttons remain disabled until this safeguard and the separately
approved HP create-only pilot pass. User choices/credentials do not change in
local tests. Read-only deployed model/controller/router sources may be copied
to private local build inputs; never copy the live user DB for convenience.
Implement and test locally while Jason uses HP. Do not operate HP during that
visual test. Ask before changing the shared Audiobookshelf runtime.

## 2026-10-25 local gate evidence

Read-only source export from the existing container matches these hashes:

| File | SHA256 |
|---|---|
| `server/models/User.js` | `92630399232fe603d05e00aafa1ddbd2bf2d8c00f52d02ab124777560b497171` |
| `server/controllers/MeController.js` | `12d7dc5763f26a60f0d58509be5a2506453e1204e251ced94884ec87dc0972f4` |
| `server/routers/ApiRouter.js` | `64802e101319d0b01123d5c4e564f96b787b9475d916467eaae1c4682deec15c` |

Actual base image ID is
`sha256:66b24f73e543959d5df7e57bc0edbeab5e759730ec356656198b5da123468c15`.
Local static inputs: `/tmp/aster-bookmark-guard-PZgbGP/source/`. Candidate4:
`/tmp/aster-bookmark-guard-PZgbGP/candidate4/`, manifest SHA
`a489b3b041ef7652467952774a80082f3c4abd8721cd575adc184dc04792fdcb`.
Complete five-member artifact verifies; candidate1/2/3 remain superseded local
builds, not deployed versions. No source credential/config/user DB was copied.

Twenty Node tests pass against actual Sequelize6.35.2/sqlite3 driver5.1.7
installed in the private temporary test prefix. Local runtime Node24.19.0;
target image Node20.20.2 **not yet smoke-tested** with the overlay. Two child
processes hold stale instances and race for one book/time: exactly one201,
one409, original winner unchanged. Separate-connection distinct writes both
survive. Legacy create/rename/edit/delete semantics, error/rollback, cross-user
isolation, strong conditional cleanup, same-millisecond delete/recreate and
edit-away/back invalidation pass. HTTP harness exercises actual patched
controller code with synthetic auth/item boundaries, not production auth.

Concurrent synthetic progress updates survive alongside20 bookmark writes
under both DELETE and WAL journals. These local test cases took about51ms and
23ms respectively; they are not production performance claims. A held external
write lock returns503 with no mutation/replay, and a later explicit new save
works. Sequelize emits its expected failed-BEGIN rollback warning and closes
that test connection; no source data is involved. A request queued over2s
fails503 before beginning another transaction. Unsupported dialect is refused.

Seven Python builder/verifier/removal tests pass: exact five targets, unchanged
unrelated source, source drift rejection before output, immutable builds,
payload/target tamper refusal, and restoration of all original code hashes
without reverting an independent synthetic progress sentinel. All605 existing
v2 Python tests still pass; their deliberate old-API hazard reproductions are
not mislabelled as live guard validation. Syntax/whitespace checks pass.

Read-only complete server-source audit found runtime bookmark persistence in
the three User model methods now wrapped. UserController excludes `bookmarks`
from profile updates. Old offline database migrations also mention bookmarks;
they are outside the concurrent ordinary-client guarantee. The package is
version/image/source pinned and must not be carried blindly into an upgrade.

## Original shared deployment proposal — approval/completion recorded below

First run a disposable Linux/Node20 check using the pinned image, network off,
no production mounts and bounded private tmpfs. If it fails, leave the shared
server untouched. After that gate, privately checkpoint current Compose/config
and a SQLite-consistent backup at the existing NAS; validate isolated integrity
and restore. Do not export credentials or restore old data over the live DB.

Stage the exact five code files as a versioned read-only overlay, compare
rendered Compose privately and preserve every existing mount/port/environment
and other service. Confirm no active listeners, briefly recreate only
`unified-audiobookshelf-shadow`, validate health/auth/read/stream paths and
new guarded API. Failure removes only those mounts and restarts the same base
image, with all legitimate bookmarks/progress retained. HP remains undisturbed
until Jason finishes visual checking; its create-only UI/test is a later step.
No public ingress, account/privilege change, extra daemon, DB schema migration,
media download or Git remote write. No server overlay/restart, real bookmark
mutation or HP control was performed during this local build milestone.

## Approved shared activation — 2026-10-25

Jason explicitly approved the bounded activation after the isolated Linux test.
Private checkpoint:
`/mnt/Media/appdata/aster-bookmark-guard-checkpoint-20261025`.
All17 config/backup files were copied into an isolated restore directory and
hash-compared; the consistent SQLite backup passed integrity/foreign-key checks
with28 tables. No original data was overwritten or restored over live history.
The TrueNAS host's SQLite3.40 cannot parse ABS's newer ORDER BY aggregate
triggers; its initial integrity attempt stopped before activation. Revalidated
both backup and isolated restore using the exact pinned service image's SQLite
in disposable networkless/read-only containers. This was a tool-version mismatch,
not evidence of corrupt source data. Partial checkpoints were retained.

This stack has no saved `.env`, and the retired Calibre worker has required path
variables with no live container from which to verify them. Do not invent those
paths or recreate that worker. The activation helper derives only Audiobookshelf's
non-secret path substitutions from existing mounts, validates its environment,
and renders a private one-service Compose with the existing project/network
identity. The original full Compose receives exactly the five read-only mounts;
all other service definitions are unchanged. Its new container Compose labels
reference the private focused definition; that definition and recovery source
are retained. Future operations must preserve this documented deployment path.

No established connections to30067 were present before the brief one-container
recreate. All five mounted source hashes, pinned image, original five mounts,
ports, environment, entrypoint, command, user and working directory verified.
Network names/IDs and host policy settings are unchanged; Docker serialized an
empty DNS list as null, which is the same default resolver behavior. Health/ping
passed; unauthenticated capability access returned401; the unchanged limited
TV account got audiobook capability200 and podcast400 (books-only contract).
Existing metadata/progress reads and real audiobook/podcast normal resume,
pause-save and Back/stop passed on HP after activation. No bookmark POST/DELETE
was issued, and production Kodi was not changed. Normal bookmark controls remain
disabled until the create-only client/UI milestone, not advertised as delivered.

Five additional synthetic activation-plan tests passed on TrueNAS with PyYAML:
five-only readonly mount addition, root-network preservation, missing-anchor
refusal, rejection of live-config proof mounts, and offline pinned restore proof.
The local macOS Python lacks PyYAML, so those five explicitly skip there; seven
local builder/verifier tests pass.20 isolated target-runtime tests also passed.
No Forgejo push performed.
