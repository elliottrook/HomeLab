# Aster Lab Hours M3 35B inactive installation result — 2026-10-29

## Result

**PASS — installed and inactive.** Platform source commit `4670bb34` was
installed without creating a booking, unit or timer and without acquiring a
lease, stopping a service, mounting a model, restarting LXC110 or calling a
model.

The installer retained the exact predecessors at
`/var/lib/local-ai-lab/checkpoints/m3-35b-inactive-4670bb34`. It replaced the
four current Lab Hours entry files and three older first-screen recovery files,
installed eleven new M3/NLU files on Proxmox, and installed the fixed guest
workload plus eight dependencies in LXC110.

## Target validation

- the installed release manifest SHA-256 is
  `007d1561fed7d0e7bdfdadcde67841d0faa5d5c76c941e2354538320a8836665`;
- all **32/32** installed release-manifest pins match;
- the target registry accepts only the exact
  `m3-joint-semantic-35b-public-v1` identity with 24 requests, a 3,600-second
  deadline, a 4,500-second minimum booking, 900-second recovery reserve and 14
  pinned runtime files;
- LXC110 imports the fixed guest workload and joint-semantic candidate under
  target Python with bytecode disabled;
- invoking the guest workload without its effect flag returned only
  `state=disabled`, `effects=not-attempted`;
- the whole-host lease is `ready`, shared state and locks are absent, no `mp0`
  candidate mount exists, and no M3/35B process remains;
- the Lab Hours Doctor unit completed with `Result=success` and exit zero;
- LXC104/110/116 are running; Aster Agent, accepted 9B/SYCL, Speech, the Lab
  Hours dispatcher, `pvescheduler` and `pvestatd` are active.

The shell observation wrapper ended before the installer printed its final
line, but the root installer continued to completion. Success is based on the
independent target hash, import, disabled-entrypoint and production postchecks,
not on the wrapper timeout.

## Remaining effect gate

The platform is ready to reserve and run the exact M3 public-gate workload.
That live action deliberately remains gated because it mounts the staged 35B
artifact, restarts LXC110 and makes 24 model requests. It must have a
conflict-free authoritative Lab Hours booking and the user's exact retained
restart/model authorization. It cannot promote a model or enable routing.

