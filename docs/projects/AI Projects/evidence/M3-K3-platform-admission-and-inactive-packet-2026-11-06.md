# M3 K3 platform admission and inactive packet — 2026-11-06

## Result

The distinct K3 platform path is source-complete on local platform commits
`05cb6910` and `25e0a809`. It registers only
`m3-k3-hierarchical-safety-development-v1`, uses a separate runner kind and
scope identity, and fixes 192 cases, 384 model requests, zero retries, a
1,800-second workload deadline, a 3,600-second minimum booking and a
900-second recovery reserve.

The guest and host validators require the accepted engine SHA-256
`cd76ec20…f2a13` in the retained run. The host transaction accepts only the
complete K3 result shape, writes a root-custodied create-only result, restores
production through the existing full-drain controller and emits an exact
content-free receipt. Pass and reject are both bounded development outcomes;
neither grants authority or enables routing.

## Live-baseline preservation

Read-only comparison against Proxmox found newer B60 fixed-card, entry-rescue
and OpenVINO controls than the original K2 platform branch. The K3 candidate
therefore preserves their exact live sources and registrations instead of
overwriting them with the older branch baseline. The currently measured host
baseline is bound by exact SHA-256 values for the workload registry, reserved
runner, full-drain runtime and release manifest. Any drift fails the installer
before mutation.

The LXC110 preflight also binds the existing K2 wrapper and shared K2 sources,
including mode-0600 corpus and shortlist custody. K3 adds only six absent guest
files: its wrapper, runner, scorer, hierarchical preregistration, safety veto
and runtime manifest. The inherited K2 wrapper is now an explicit runtime pin,
closing the dependency omission found during platform composition.

## Verification

- focused platform/admission and regression suite: 64/64 passed;
- inactive-packet, K3 transaction, admission and release suite: 11/11 passed;
- deterministic bundle files: 15;
- deterministic bundle SHA-256:
  `3df8038bdf26bcf737a73bbd9efa7fbcf09fac12dcbe2d48ee058a760fefcc20`;
- live baseline recheck: exact four host hashes, existing guest dependency
  hashes, lease `ready`, and no drain/operation locks; and
- effects: `not-attempted`.

## Boundary and next action

No platform file was installed, no workload was booked or run, no service was
stopped or restarted, no model request occurred, sealed evaluation remained
closed and automatic routing remained off.

The next effect is one reversible inactive installation from the deterministic
bundle. It must retain its rollback checkpoint and be followed by the required
independent read-only audit of the new runner kind. Only a passing inactive
audit permits an authoritative complete-window ledger check and a later K3
booking proposal.
