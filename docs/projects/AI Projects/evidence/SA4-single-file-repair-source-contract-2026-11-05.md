# SA4 single-file repair source contract — 2026-11-05

## Result — schema prototype only

The first generic SA4 schema prototype is retained without selecting or touching
a production target. It describes one deliberately narrow repair class:
single-file configuration drift on a regular file that can be replaced
atomically without following links and without a service restart.

The plan requires the exact candidate-release digest, host, absolute normalized
path, expected bytes, owner/group/mode, desired artifact digest, immutable
checkpoint, fixed registered postchecks and unconditional rollback on any
failed or uncertain postcheck. It excludes credentials, firewall, network,
models, service restarts and shared infrastructure. Arbitrary commands and
unknown fields fail closed.

An independent audit found that the first version treated JSON approval,
AI-PAM and checkpoint fields as authenticated evidence when they were only
assertions, and accepted any syntactically valid absolute path. That version is
not effect-ready. The corrected prototype registers only a synthetic fixture
target under `/synthetic`; `/etc/shadow`, unknown target IDs and all real hosts
fail closed. Its output explicitly says authenticated authority is absent,
preflight is ineligible, the grant is unconsumed and maximum effects are zero.

Four focused synthetic plan/admission tests pass. Their output is schema evidence only;
the fixture names no real host or file and performs no repair. No production
target, checkpoint, approval, grant, mutation, restart, deployment, authority
or routing change exists.

The terminal schema prototype now accepts only a zero-effect preflight NO-GO.
It rejects every claimed complete, rolled-back or uncertain effect because the
current source has no independently measured filesystem/postcheck receipts.
The combined SA4 prototype suite passes 9/9 without claiming an effect result.

## Remaining gate

Candidate-J is now the owner-accepted D4 release candidate. The next source
increment closes three earlier design gaps without selecting a real target:

- dependency-free RSA-2048 detached-proof validation requires distinct owner
  and AI-PAM signers from compiled trust registries. Those real registries are
  deliberately empty, so runtime callers cannot nominate their own keys;
- a root-custodied atomic one-use ledger burns the grant at claim and permits
  only `ready -> claimed -> consumed|failed|uncertain`. It has no reset,
  reclaim or retry path, fences abandoned claims as uncertain and rejects late
  success;
- exact synthetic filesystem evidence binds `O_NOFOLLOW` descriptor/lstat/fstat
  agreement, one-link root custody, bytes and metadata, distinct immutable
  same-bytes checkpoint, same-filesystem temporary path, shared lock,
  emergency stop and three registered-not-run postchecks.

The composition gate calls all three validators and cross-binds plan, grant,
target, expiry, ledger and checkpoint identities. Even its complete synthetic
chain returns `maximum_effects=0`, `preflight_eligible=false`, requires a later
owner effect decision and performs no open, lock, checkpoint, write, rename,
postcheck or rollback. The expanded SA4 suite passes 30/30.
The source identities are `c126541a…c9e5a3` (authority),
`929f1427…372223` (ledger), `216f7d83…3fe447` (filesystem evidence) and
`b3441233…b0743f` (composition).

## Remaining real-world gate

No production target or real key is registered. The filesystem measurements
are synthetic assertions, not an authenticated capture. SA4 still requires an
owner-reviewed low-criticality target registration, separately controlled
owner and AI-PAM keys compiled through review, a root-installed inactive
measurement/owner implementation, independent postcheck and rollback
receipts, and one exact effect proposal. Jason's specific approval remains
mandatory immediately before the first repair effect; model/backend changes,
service restart, credentials, network, firewall and shared infrastructure stay
excluded.
