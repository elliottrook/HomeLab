# Disposable VM V2 bootstrap canary — failed safely

Date: 2026-09-26  
VM: Proxmox VM118 `aster-s0-fixture-v0`  
Result: **FAILED / INCONCLUSIVE — no protocol result; no retry authorized**

## Outcome

V1 succeeded: the checksum-pinned Debian image was downloaded, a stopped VM was
created from the reviewed configuration, and the stopped-state gate proved that it
had no network device, guest agent, credential, passthrough or shared filesystem.

The single approved V2 boot reached cloud-init and attempted
`aster-s0-canary.service`. The unit failed before it emitted an `ASTER_S0_V1`
record. A later explicitly approved read-only forensic inspection proved why:
systemd could not attach the service's standard output to `/dev/ttyS0` while
`PrivateDevices=yes` isolated the service device namespace. It failed with
`status=209/STDOUT` and `Operation not permitted` before Python executed. The
cloud-init wrapper still issued the designed poweroff, the VM stopped
cleanly, and the host capture command returned zero after the serial session ended.
The capture is 105,115 bytes with SHA-256
`23e071c370e952d64c08b678900121ee03098ec7444b1d26f5e5661fc9027fdb`.
It contains zero protocol records, so the strict parser returns `incomplete
protocol`. This is not a successful canary.

## Verified facts

- Debian image length: 433,651,712 bytes.
- Debian image SHA-512:
  `a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c`.
- Downloaded `SHA512SUMS` SHA-256:
  `6e1f384b152ce4bc7c5f287b5559f18786de3036915e6e6c42b3fcb8dfd8709a`.
- Seed ISO: 376,832 bytes; SHA-256
  `326dd8ccdbd80aa01be0cee6dacfea3131f46bd47f11af2738ae7c63962b7a77`.
- Rock Ridge and Joliet listings contain exactly `/user-data` and `/meta-data`;
  extracted bytes match the reviewed source hashes.
- VM configuration: one core; 1,024 MiB fixed memory; q35/OVMF; 8-GiB OS disk;
  4-MiB EFI vars; read-only seed CD; serial socket; manual boot.
- No `netN`, agent, host PCI, USB, VirtioFS, GPU, credential or on-boot setting.
- Guest cloud-init reported only `lo` with loopback IPv4/IPv6.
- Cloud-init reached its final stage and invoked the canary unit at about 130 seconds.
- The unit failed before `ExecStart` at systemd's STDOUT setup step:
  `Failed to set up standard output: Operation not permitted`, status
  `209/STDOUT`.
- The generated unit, canary and payload manifest match the reviewed SHA-256
  values; `/var/lib/aster-s0/output/result.json` is absent.
- The ext4 filesystem reported `clean` before the forensic mount.
- The inspection used a read-only loop and `ro,noload` (reported by ext4 as
  `norecovery`), then verified that both mount and loop device were absent.
- The wrapper powered off the VM even after the unit failure.
- VM118 is stopped and retained with its OS disk; its one approved offline
  inspection completed read-only and detached cleanly.
- The host is `running`; available memory and storage remain above the gates.
- All pre-existing VMs/LXCs retained their preflight running/stopped states.
- Accepted corpus evaluated: **false**.

The two-minute startup delay came from `systemd-networkd-wait-online` in a VM with
no NIC. This is useful optimization evidence but is not the canary failure cause.
The image also created host SSH keys and started its SSH service despite having no
NIC or injected login credential. A future seed should mask SSH/key generation and
disable network-online waiting to reduce unnecessary software and noise.

## Evidence retained

The bounded raw serial capture remains on the Proxmox host at:

```text
/var/lib/vz/template/cache/aster-s0-20260926/run-v2/serial.capture
```

A byte-identical temporary analysis copy was read locally and is not committed
because it includes irrelevant boot noise and generated public SSH host keys. This
directory records its digest, size, bounded findings and exact VM facts instead.
The source image, checksum file, seed sources and ISO are retained in their reviewed
host paths. `evidence.json` is the structured record.

The sanitized forensic receipts and seven bounded unit-journal records are in
[`forensics/`](forensics/). Their individual remote SHA-256 values are retained in
`evidence-sha256.txt`; local retrieval revalidated every digest. The collection
script SHA-256 is
`52627d1dbb04b0d8d78a00a8202e9d04a7d371781c3a22511d939f474fe246c1`.

Two pre-access attempts stopped on receipt-format assertions and detached cleanly:
the device mapper exposed the source as `/dev/dm-27` rather than its
`/dev/pve/...` symlink, and ext4 reported `norecovery` for the requested `noload`
option. Both assertions were corrected without weakening read-only enforcement.

## Decision and next gate

V2's success gate did not pass. Do not run V3, access the accepted corpus, reboot
VM118, modify its disk, or treat poweroff as proof of confinement.

The evidence supports a narrow correction: keep `PrivateDevices=yes`, have the
unprivileged canary write a bounded protocol file in its only writable directory,
and let the outer cloud-init lifecycle copy that file to `/dev/ttyS0` only after a
successful unit exit. This separates computation from the serial device boundary.

Candidate `vm-candidate-v1` uses new run and instance identities. It remains a
local source artifact. Creating a new seed/VM or booting any candidate requires a
fresh explicit approval; VM118 must not be reused as though cloud-init were fresh.
