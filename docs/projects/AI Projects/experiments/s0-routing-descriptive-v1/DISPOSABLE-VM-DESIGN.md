# Disposable S0 VM — read-only feasibility design

Date: 2026-09-26
Status: design only; VM creation and corpus execution are not authorized

## Recommendation

**GO TO A CONCRETE BUILD PLAN, NOT TO VM CREATION.** A small dedicated QEMU VM
with no virtual NIC is a credible replacement for LXC100. It separates the S0
runner from household services and avoids relying on namespace creation inside an
LXC. The first VM activity must still use invented fixtures only.

## Verified current evidence

Read-only Proxmox queries reported:

- one Xeon E5-2698 v4 host, 20 cores / 40 CPUs;
- 84,241,424,384 bytes total memory and 49,421,041,664 bytes available at the
  observation instant;
- 17 running guests with 78,383,153,152 bytes of configured memory maxima and
  28,701,118,464 bytes of observed use;
- near-zero host swap use at that instant;
- `local-lvm` active with 665,394,887 KiB available and `local` with 68,658,460
  KiB available;
- VMID 118 returned as the next ID at that instant; it is not reserved;
- VLAN-aware `vmbr0` exposes VLANs 20, 50 and 70, but the proposed test VM does
  not require a vNIC;
- local Debian ISO `debian-13.6.0-amd64-netinst.iso` hashes to
  `65273beed27b2df543b68b65630ba525cfbad8df2b12035732b2dff87d6664e7`,
  matching Debian's archived official
  [13.6.0 SHA256SUMS](https://cdimage.debian.org/mirror/cdimage/archive/13.6.0/amd64/iso-cd/SHA256SUMS).

These are snapshots. Available memory is not a reservation, configured maxima are
not simultaneous demand, and observed use is not a safe long-term capacity bound.

## Proposed minimum VM envelope

| Property | Proposed bound | Reason |
|---|---:|---|
| vCPU | 1 | Runner is deterministic and latency is descriptive |
| RAM | 1 GiB fixed | Leaves room for a minimal OS around the 256 MiB runner budget |
| Disk | 8 GiB thin-provisioned | OS, pinned inputs, bounded scratch and retained fixture evidence |
| Network | No vNIC | Enforces no LAN/Internet path structurally |
| GPU/passthrough | None | S0 does not need inference or accelerators |
| Credentials/secrets | None | Synthetic routing data and public code only |
| Host integration | Console plus a reviewed bounded artifact channel | Avoids SSH and network management inside the guest |
| Lifetime | Disposable/rebuildable | No service role or long-lived state |

The no-vNIC property is the primary network control. Guest systemd restrictions
still enforce process, filesystem, privilege and resource limits. Host-side wall
timeout and VM shutdown remain independent controls. The VM must not receive host
directories, Docker sockets, credential mounts, management VLAN access or GPU
devices.

## Artifact and result channel

Do not add temporary network access merely for convenience. Build input should be
a read-only ISO containing a pinned unattended-install description plus reviewed
runner/fixture artifacts. Results should use a small dedicated bounded data device
or a reviewed serial protocol, retrieved only after clean shutdown. Select one
method after proving exact size limits, atomic completion and safe host parsing.

QEMU Guest Agent may be evaluated as a control channel only if its package is
available from the pinned offline installation source and its host/guest authority
is explicitly documented. It is not assumed present or required by this design.

## Remaining unknowns and gates

1. Whether the Debian netinst ISO supports the complete offline minimal package set
   needed for unattended installation and the selected result channel.
2. Exact storage pool, firmware, machine type and discard settings.
3. Whether 1 GiB installation/runtime memory passes an invented-fixture build test.
4. The artifact channel and its failure/recovery semantics.
5. Host monitoring and deterministic teardown evidence.
6. Capacity at the actual creation window.

Before creation, freeze the VM configuration, ISO checksum, unattended input,
runner fixtures, network absence checks, teardown steps and rollback. Obtain a
specific infrastructure-change approval. VM creation does not authorize accepted
corpus access; that remains a later, separately reviewed one-shot decision.

## Rejected shortcuts

- Do not reuse stopped VM105; it remains the inference rollback guest.
- Do not clone a service VM or attach a household VLAN.
- Do not weaken the LXC100 policy and call it equivalent isolation.
- Do not depend on the future second node for this programme's next proof.
- Do not download a replacement image merely because 13.7 is current; the existing
  13.6 artifact is verifiable and must first be assessed for the offline build.
