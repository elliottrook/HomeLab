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

Candidate-J must first produce an accepted D4 release candidate. Before a real
target can even reach preflight, SA4 still needs a hash-pinned target registry,
authenticated owner approval and AI-PAM receipt, durable atomic one-use
consumption, fd/no-follow live filesystem and checkpoint evidence, shared lock
and emergency stop, and independent bytes/metadata/consumer/rollback receipts.
Only then may Stream A propose one low-criticality target. Jason's exact owner
approval remains mandatory before the first repair effect.
