# SA4 inactive exclusive checkpoint owner — 2026-11-05

## Result

SA4 now has a source-only checkpoint owner that can copy only a freshly
measured, unchanged compiled target. Its public API accepts exact plan and
measurement bytes plus the checkpoint time; callers cannot nominate a host,
path, registry, checkpoint destination, command or grant.

The owner requires an exact production registration and compiled local host,
a root-owned mode-0700 checkpoint directory, and a root-owned one-link
mode-0600 exclusive owner lock. It reopens the target with
`O_RDONLY|O_NOFOLLOW|O_CLOEXEC`, requires the full path/descriptor identity to
match the prior measurement, and rejects measurements older than five minutes.
It writes a mode-0600 same-filesystem temporary copy, fsyncs it, publishes the
final checkpoint without replacing an existing path, fsyncs the directory,
reopens the checkpoint without following links, and verifies exact bytes and
custody while proving the target remained unchanged.

The committed production registry remains empty and the compiled local host is
`unconfigured`, so this source cannot create a live checkpoint. Synthetic
tests use a disposable registered file and prove exclusive creation,
unchanged target bytes, stale/changed measurement rejection, directory custody
failure, existing-checkpoint refusal and an API with no override surface. A
failed synthetic operation removes only its incomplete temporary/checkpoint
copy. It never claims a grant, changes the target, starts a service, performs a
repair or permits retry.

The expanded SA4 suite passes **52/52**. No production target, checkpoint,
grant, key, deployment, repair effect or route was created.

## Source identities

- inactive checkpoint owner:
  `57000e3d692478657f9f55fd0b37e5364cb769b74f23acda60e29155e66b9b07`
- adversarial tests:
  `3357e4d4349bd664cee960a96f6e0e4c256d28ef3c62d755142240d0b7773dfc`

## Remaining gate

Next is a source-only receipt/ledger reconciler that cross-binds the claimed
one-use grant, checkpoint owner result, operation terminal, independently
authenticated postcheck and any rollback receipt. It must burn every claimed
grant terminally, accept no effect while real registries are empty, and never
permit automatic retry. A genuine target and separately controlled real keys
remain later owner-review gates; the first repair effect still requires its
own exact approval.
