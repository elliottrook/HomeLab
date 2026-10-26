# D4 candidate-H inactive staging card — 2026-10-25

**State:** completed on second approved attempt; inactive target validation passed

## Purpose

This card prepares the corrected candidate-H launcher for target-Linux custody
tests without opening the real credential, starting the service or calling a
model. It is a replacement for the rejected root-child launcher. The source
boundary is commit `0966af2d`; the machine-readable bundle is
`services/aster-agent/deploy/d4-candidate-h-bundle-manifest.json`.

The bundle validator reports one inactive candidate, eleven packet files,
three persistent control files and one temporary target validator. It binds the
candidate-H run digest
`423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4`.

## Preconditions

1. LXC104 is running and healthy; no other maintenance owns it.
2. UID and GID 977, user/group `aster-d4-eval`, both candidate directories,
   all three control targets and the candidate service are absent.
3. `/etc/aster/aster.env` remains root:aster mode 0640. Its contents are not
   read, hashed, copied or printed during staging.
4. The source commit, bundle manifest, source manifest and all fifteen source
   hashes match the validator.
5. A root-only rollback directory is created before the first target mutation,
   containing the preflight identities and the exact rollback sequence. There
   are no predecessor file bytes because every target must be absent.

Any mismatch is NO-GO. Do not reuse an existing UID/GID or overwrite an
existing target.

## Bounded inactive installation

1. Copy the fifteen hash-pinned source files to a root-only temporary staging
   directory in LXC104 and revalidate every byte there.
2. Install only `/usr/lib/sysusers.d/aster-d4-eval.conf`, then invoke
   `systemd-sysusers` for that exact fragment.
3. Verify `aster-d4-eval` is UID/GID 977, has `/usr/sbin/nologin` and has exactly
   its primary group. It must not be a member of `aster`, `hlabroker-clients`,
   `hlabroker-approvers`, `ollama`, `render` or `video`.
4. Create the source directory root:aster-d4-eval mode 0750 and install the
   exact eleven packet files root:aster-d4-eval mode 0640.
5. Create the empty output directory aster-d4-eval:aster-d4-eval mode 0700.
6. Install the root:root mode-0755 launcher and root:root mode-0644 oneshot
   unit, then run `systemctl daemon-reload`. Do not enable or start it.
7. Recompute all hashes from LXC104 and verify the unit is disabled and
   inactive with no invocation ID, process or output.

## Content-free target-Linux validation

Run the pinned temporary validator
`/run/aster-d4-candidate-h-target-validation`, SHA-256
`e38952b4495326b12e37b0b23f17bc8c061d03ccefda1af71ad390d34186e7a5`.
It runs only synthetic, fictional probes that cannot reach the model endpoint:

- import and compile the launcher and candidate Python files with bytecode
  writes disabled;
- prove the dedicated identity can read every source packet file but cannot
  write, replace, rename or unlink any of them;
- prove it can create and remove one fictional mode-0600 file in the output
  directory, leaving the directory empty afterward;
- prove it cannot read `/etc/aster/aster.env` and cannot traverse `/etc/aster`;
- invoke a fictional pipe child through the launcher helper and record only
  its UID, GID, supplementary-group count, environment-key absence and whether
  the fictional bytes arrived; and
- verify the real credential was never opened, no D4 journal exists and no
  request reached Aster or llama.cpp.

The target probe must report UID/GID 977, zero supplementary groups beyond the
primary group, no environment key and successful fictional descriptor delivery.
Any other result is NO-GO and triggers rollback. Remove the temporary validator
after capturing its content-free result.

## Rollback

Confirm the service is inactive and no process uses either candidate directory.
Remove the unit, launcher, packet directory, empty output directory and sysusers
fragment; daemon-reload; remove the dedicated user and group only after proving
they own no other files. Confirm all targets and the identity are absent and
that Aster Agent, the accepted llama.cpp/SYCL service and ordinary schedules
remain unchanged.

## Explicit exclusions

This card does not authorize opening the real credential, starting or enabling
the candidate service, creating a journal, calling a model, stopping a B60
consumer, acquiring a lab lease, changing a schedule, granting a supplementary
group, activating F6 or promoting candidate-H. Those remain separate gates.

## First attempt correction

The first approved inactive attempt rolled back before any fictional probe
because `spec_from_file_location` did not recognize the extensionless installed
launcher. All created targets and UID/GID 977 were removed; Aster Agent stayed
active and `/etc/aster/aster.env` remained root:aster mode 0640. The corrected
validator uses `SourceFileLoader`, has an explicit extensionless-path regression
test, and has the replacement SHA-256 recorded above. A retry is a new exact
host change and requires its own approval.

The separately approved retry passed. Its measured result is recorded in
[attempt 2](D4-candidate-H-inactive-staging-attempt-2-result-2026-10-25.md).
