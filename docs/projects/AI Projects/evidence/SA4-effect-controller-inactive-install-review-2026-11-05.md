# SA4 effect-controller inactive-install review — 2026-11-05

Fresh checks found all three destinations absent and the fixed Proxmox
observer signer unchanged at `d804154c…cf16`. The inactive plan creates only
the LXC one-shot controller and exchange plus the Proxmox fixed bridge as
root-owned mode-`0644` files. Rollback removes only exact installed hashes.

Postchecks may hash, inspect and import only. They cannot create runtime state,
invoke a controller or signer, create authority, touch the target or act on a
service. Three focused tests and the complete 184-test SA4 suite pass. No
installation occurred. The three-file inactive installation is the next gate.
