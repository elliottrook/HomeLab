# SA4 inactive read-only measurement owner — 2026-11-05

## Result

SA4 now has a source-only, inactive target measurement owner. Its public API
accepts only exact plan bytes and a measurement time. It resolves the target
solely from the compiled production registry; callers cannot supply a path,
host, registry, key, postcheck or command.

The committed production registry is empty and the compiled local host is
unconfigured, so the source cannot open a live target. Under a temporary
synthetic test registration it opens only `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`,
requires path/descriptor device and inode agreement, regular-file/one-link
custody, exact owner/group/mode, a fixed size ceiling and the plan's expected
digest. It rereads descriptor and path metadata after hashing and rejects any
identity or timestamp change.

The output is metadata-only and explicitly records no checkpoint, grant claim
or repair effect, no preflight eligibility, no authority and no retry. It never
creates a checkpoint or temporary replacement, writes the target, claims a
grant, runs a postcheck, restarts a service or performs a repair.

The expanded SA4 suite passes **47/47**, including empty-production-registry,
symlink, hardlink, mode, digest and API-override failures. No live measurement,
target, checkpoint, key, deployment or effect occurred.

## Source identities

- inactive measurement owner:
  `edddae56bc3d5c740354beb27f45f7a24e42457a903e6aa497668c65f5a9adc0`
- adversarial tests:
  `6a3fea451453448c433f92f4985db8354859d104d0e5110ddc7e0777d64c433f`

## Remaining gate

The next source increment is an inactive, exclusive checkpoint owner plus a
new reconciliation contract that binds measurement, claim, independent
postcheck and rollback receipts. A genuine target and separately controlled
real keys still require owner review; installation and the first repair effect
remain separate gates.
