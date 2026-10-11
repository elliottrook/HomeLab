# B60 VF BAR proof candidate

This directory contains a source-only, one-shot kernel-module candidate. It is
not approved for production deployment.

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
