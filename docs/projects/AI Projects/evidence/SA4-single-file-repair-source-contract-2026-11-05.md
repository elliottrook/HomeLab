# SA4 single-file repair source contract — 2026-11-05

## Result

The first generic SA4 source boundary is complete without selecting or touching
a production target. It defines one deliberately narrow repair class:
single-file configuration drift on a regular file that can be replaced
atomically without following links and without a service restart.

The plan requires the exact candidate-release digest, host, absolute normalized
path, expected bytes, owner/group/mode, desired artifact digest, immutable
checkpoint, fixed registered postchecks and unconditional rollback on any
failed or uncertain postcheck. It excludes credentials, firewall, network,
models, service restarts and shared infrastructure. Arbitrary commands and
unknown fields fail closed.

The pre-effect admission cross-binds the exact plan to a time-bounded owner
approval, one-use AI-PAM grant and single-link regular-file checkpoint. The
grant is bound to the observed target digest and permits at most one atomic
replacement. Expiry, reuse, target drift, checkpoint drift, symlink following,
unsafe paths and automatic retry all fail closed.

Four focused synthetic tests pass. Their output is preflight eligibility only;
the fixture names no real host or file and performs no repair. No production
target, checkpoint, approval, grant, mutation, restart, deployment, authority
or routing change exists.

## Remaining gate

Candidate-J must first produce an accepted D4 release candidate. Stream A may
then inventory and propose one low-criticality real target using this contract.
Jason's exact owner approval and a real one-use grant remain mandatory before
the first repair effect. The source contract does not pre-authorize that effect.
