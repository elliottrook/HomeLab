# D4 Candidate-J quality materialization and registration — 2026-11-05

## Result

The strengthened untouched Candidate-J packet and its answer keys are now
materialized as separate canonical JSON artifacts. Their bytes reproduce the
frozen builder exactly:

- packet: 26,833 bytes,
  `53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132`;
- answer keys: 3,513 bytes,
  `cab2790dbb6e84b0bbe269c876dee8c4b116abfb4fa6fc2a119782e4b7fcd526`.

A new regression test compares both materialized byte streams to the builder's
canonical output. The complete Candidate-J source suite passes 40/40.

Platform commit `77abd40c5e5205c6c3d0d88151e6503d9ed5c2d8` registers the distinct inert
workload `sa3-evidence-matrix-candidate-j-quality-v1`. It pins only the packet,
shared deterministic contract, bounded selection runner and key-free quality
runtime. The answer keys, key-bearing source freeze, scorer, blind-review code
and decision code are excluded. Platform registry tests pass 10/10.

## Inert boundary

The new runner kind is deliberately absent from the reserved-runner admission
set. Nothing has been installed on Proxmox or LXC110, no Lab Hours window was
queried or reserved, and no model call, service stop, restart, route, authority
or promotion occurred. Registration cannot execute the workload.

Platform commit `20490b65e85a9afd35b0673f7018c72278051668` now completes
the fixed transaction, bounded host listener, key-free guest wrapper and
reserved-runner integration source. Release v16 pins the joined path and 57/57
focused platform tests pass. Nothing is installed.

Platform commit `cae82a0cfb0bcfc54fc05e71e47c5a753b489c5f` now adds the
deterministic reversible inactive installer. Its joined suite passes 61/61.
The independently built 14-file bundle is
`e72a7a4558969e242eb9f4d3ba7ae921c9eea5c5bcbd86a87133f2b7b4adb956`;
inspection confirms it contains the packet and only the three key-free guest
Python dependencies plus the fixed wrapper. No keys or review/scorer code are
present.

The next gate is applying that exact inactive installer and validating target
custody without starting a unit or model. A live attempt remains downstream of installation proof, an
authoritative conflict-free Lab Hours booking and fresh lease/lock admission.

## First install attempt and concurrent release correction

The first approved application was a pre-mutation NO-GO at
`CUSTODY:lab_hours_workloads.py`. No checkpoint or target file was created.
The live platform had legitimately advanced after the original baseline read
to a 43-pin TTS/EPUB release. The installer correctly refused to overwrite it.

Platform commit `25af3942f6808e4332797369d030348aedb4ae1c` rebases Candidate-J
onto every exact live pin and preserves the EPUB word-alignment and TTS
CPU-screen workloads. The corrected combined release has 46 pins and its
joined suite passes 61/61. Applying it is a new deployment gate because the
prior approval was spent on the safely failed, materially different bundle.

The second approved attempt also failed before mutation, at guest preflight
`TARGET_PRESENT:sa3_evidence_matrix_candidate_j_contract.py`. Readback proved
that contract and the runner are exact accepted shared dependencies from the
public Candidate-J runtime. Quality-specific host and guest targets remain
absent; only a host preflight checkpoint was retained. Platform commit
`c0e55f62c0e04a36f642056037acff5aaad7fc7` changes R2 to verify those two
files in place and add only three quality-specific guest files. The 61/61 suite
passes; applying R2 is a fresh deployment gate.

R2 bundle `5a1424b5…fd6e` subsequently installed successfully. Platform result
commit `676be2394bc5beb17619b62d982f4854ce72969b` records 46/46 pins,
three added guest files, two exact shared dependencies, retained checkpoints,
no units, no service restart and no workload effect. The lease is ready,
shared state/locks are absent, production services are healthy and the fresh
Doctor result is healthy with no codes. The next gate is one exact ledger-booked
untouched quality transaction.
