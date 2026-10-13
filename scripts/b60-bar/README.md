# B60 VF BAR proof candidate

This directory contains the host-specific B60 full-BAR workaround.
The fourth approved host trial on 2026-10-10 obtained a 32 GiB physical BAR2.
Jason approved persistent deployment and a fifth attended boot reproduced it.

## Host trials and current candidate

The first boot did not run the helper: initramfs udev coldplug did not honor the
soft dependency. An explicit `init-top` script before `udev` fixed ordering.
The second boot changed the hardware VF BAR from 2 GiB to 256 MiB but left its
Linux resource reservation at 48 GiB. The third boot used `adjust_resource()`
to shrink that reservation to 6 GiB. PF BAR2 still failed with `ENOSPC` because
the bridge's 48.65 GiB aperture started 2 GiB off a 32 GiB boundary and its
sibling resources prevented release of the root-port window.

The fourth trial used a dedicated GRUB entry with `pci=realloc=on` and
`pci=resource_alignment=35@0000:04:00.0`. This reserves 32 GiB aligned regions
for both PF memory BARs during early PCI allocation. The v3 helper verifies
those reservations, programs the advertised 32 GiB physical ReBAR, restores
the GTT BAR0 resource to its actual 16 MiB size, and reduces the VF resource to
6 GiB. Linux then probes stock `xe` with the full BAR already assigned.

Observed fourth boot: physical BAR2 `0x31000000000`, size 32 GiB; BAR0
`0x30800000000`, size 16 MiB; VF BAR2 256 MiB per VF, aggregate 6 GiB;
`xe` reports CPU-accessible VRAM `0x5fa000000`, equal to its usable VRAM.
This is a successful BAR proof, not evidence of an inference speed improvement.

The tested v3 module SHA-256 is
`7d040a5d709161376a171b32258e37ac4804b051dea2e34f44730ec08a7b5894`.
Its separate `/boot/initrd.img-7.0.14-23-pve-b60-aligned-test` SHA-256 is
`5c844425a4d5c124334b6f7cea0bc1f20f4b619c65edb0536937d0c77965d308`.
The normal 7.0.14-23 initramfs and installed module remain v2; the 7.0.14-20
rollback is untouched. The temporary test entry and `next_entry` were removed.
The approved persistent generator `41_b60_bar` and `zz-b60-bar.cfg` now select
`b60-bar-aligned-7.0.14-23` by default. Boot ID
`0b822e46-9f9e-469b-8927-38782b20dcc5` reproduced full BAR and full CPU-accessible
VRAM. The separate verified image retains its historical `aligned-test` name.

This entry is deliberately pinned to kernel 7.0.14-23 and its verified image.
Do not remove that kernel or silently adopt a new kernel: rebuild and validate
the helper/image against matching headers before separately approved migration.
No DKMS or automatic cross-kernel deployment is configured.

For console recovery select a normal 7.0.14-23 or retained 7.0.14-20 entry under
Advanced options. To revert the default, remove only
`/etc/default/grub.d/zz-b60-bar.cfg`, then run `update-grub`; normal boot returns
to the small-BAR path. This recovery mutation requires appropriate authorization.

Build using `Kbuild` from a clean module directory and the matching headers:

```sh
make -f /usr/src/linux-headers-7.0.14-23-pve/Makefile M="$PWD" modules
```

The module's vermagic is `7.0.14-23-pve SMP preempt mod_unload modversions`.
Strict checkpatch found no errors and two cosmetic split-log-string warnings.
The unsigned, out-of-tree module produces expected kernel taint messages.
Secure Boot was disabled for the approved trials.

`41_b60_bar_test` contains this host's exact LVM identifiers and is a reviewed
candidate, not a portable installer. GRUB cannot clear `next_entry` itself on
this LVM setup; explicitly clear it with `grub-editenv /boot/grub/grubenv unset
next_entry` after returning, or select a normal entry manually at the console.

## Matched historical performance comparison — 2026-10-10

`benchmark-production.sh` reruns the exact production summary runner/fixture
hashes with unchanged 9B model, binary, unit, Q4 KV, reasoning-off and 256-token
cap. One warm-up and five measured 16-case suites gave median end-to-end
latency 2.403453 seconds (suite medians 2.399258–2.407435), versus historical
3.070279 seconds: **21.7% lower observed latency**. All completion-token counts
match, and the same four assertions fail: 12/16 before and in each repeat.
Do not call this a clean correctness pass or a BAR-only causal improvement.
The historical first eight cases were disproportionately slow, only one old
suite exists, and the kernel changed. Isolating BAR requires separately approved
attended same-kernel small/full/small boots with identical warm-up and repetitions.
No additional boot or service change was performed for this comparison.
Evidence and hashes: `bar-performance-20261010.json` in the project directory;
raw immutable suites reside in LXC 114 `/var/lib/b60-inference/evidence/`.

## Private persistent SYCL and native OpenVINO — 2026-10-11

The owner-approved persistent runtime is staged at `/opt/aster-sycl-b11429`
in LXC 110 after a verified fresh backup/mirror and approved 64→72 GiB root
growth. It uses b11429 FP16, fusion 1, private Level Zero loader 1.33.1 and
oneAPI libraries. No system package/global driver/linker/boot change is made.
Two clean production starts, regression, exact Vulkan rollback and final
exercised soak passed. SYCL accepted at 01:39 PDT; full evidence is recorded
in the project ledger.
Exact source unit: `../b60-inference/aster-llama-9b-sycl.service`.

`stage-production-sycl.py` verifies/copies every runtime byte/link/mode and
prepares the exact unit plus Vulkan rollback. `production-sycl.py --activate`
requires the independent host rollback timer. `--rollback` explicitly restores
the retained Vulkan profile; `--restore-accepted-sycl` restores accepted SYCL
after later trials without changing the unit. Never use the legacy matched
Vulkan/SYCL trial controller for a native OpenVINO comparison: its historical
labels and lifecycle assumptions predate SYCL acceptance.

Native OpenVINO trial uses pinned vendor IR rather than unsupported native
Qwen3.5 GGUF input. Downloads and guest copies are hash-verified and isolated;
only `dpkg-deb -x`/private wheel extraction, never system installation. The
model's text-embedding/vision-merger blobs and runtime are RAM-backed to
preserve disk headroom; these temporary trial paths do not survive reboot.
`native-openvino-trial.py` requires a fresh explicit SYCL preflight and
independent SYCL recovery timer, runs matched controls and synthetic checks,
then restores SYCL exactly. It avoids active backup I/O and the 02:30 boundary.
No automatic failure retry or permanent OpenVINO deployment is authorized.
The HTTP adapter is deliberately synthetic-only, not full production API
parity. Report end-to-end latency and quality with quantization/cache/metric
caveats; do not report a backend-only causal decode percentage.

## Original isolated build

The source compiled successfully in a temporary x86-64 Debian builder against
the official `proxmox-headers-7.0.14-23-pve` package (verified package SHA-256
`4a65d1279907ca20e9c8d8a2facd86f2d94082142c19be20419a03e5594d79c4`).
The resulting unloaded module had SHA-256
`16feed7a34c9d80941ceb27f6d8e1981c18b719332a57865d11f3092bf3ea7d4`,
vermagic `7.0.14-23-pve SMP preempt mod_unload modversions`, no declared module
dependency and expected versioned references to the PCI ReBAR APIs. The module
was neither installed nor loaded; both temporary build directories were
removed. The artifact is intentionally reproducible rather than committed.

The module targets only Intel PCI device `8086:e211`. It refuses to operate if
any VF is enabled, selects the device's smallest supported VF LMEM BAR2 size and
uses the kernel's exported `pci_iov_vf_bar_set_size()` API. It must execute
before `xe`; the stock driver can then perform its existing PF BAR2 resize.

The preferred first deployment, if separately approved, is against a second
official Proxmox kernel rather than the current working kernel:

1. rebuild against that kernel's matching headers in an isolated builder and
   require the recorded source and header hashes;
2. inspect the module metadata, undefined symbols and package contents;
3. install it only for the second kernel and include it before `xe` in only that
   kernel's initramfs;
4. retain the current 7.0.14-20 kernel and initramfs unchanged as rollback;
5. verify a local console and the exact GRUB selection procedure;
6. after a fresh LXC 110 backup and successful TrueNAS mirror, perform one
   attended boot of the candidate kernel; and
7. accept only if the VF reservation is 6 GiB, PF BAR2 is 32 GiB, `xe` and BMG
   G21 Vulkan enumerate, LXC 110 starts, Aster production passes authenticated
   generation and no new PCI/kernel/GPU fault appears.

Abort on any unexpected device match, enabled VF, module error, missing rollback
entry, failed backup/mirror, PCI allocation surprise, device loss, reset, OOM,
guest failure or production health failure. A failed candidate boot is rolled
back by selecting the retained 7.0.14-20 kernel locally; do not add a persistent
kernel command-line parameter.
