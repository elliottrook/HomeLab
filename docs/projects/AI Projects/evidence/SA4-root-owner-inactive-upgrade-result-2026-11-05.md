# SA4 root-owner inactive-upgrade result — 2026-11-05

## Result

The explicitly approved four-file inactive LXC104 upgrade completed. The
installer transport exceeded its 30-second client wait, so it was not retried.
Direct reconciliation found no installer process and all four intended final
files at their exact hashes:

- preflight composition `a38ccb0b…d11`;
- receipt/ledger reconciler `9688ae6e…69a1`;
- final effect admission `16d6bba0…040b`;
- root transaction owner `d8a6d69a…1c39`.

All are root:root 0644, one regular link, and import together in isolation.
The two exact predecessors remain root:root 0600 under the retained source
checkpoint. The independent canonical result validates four rows with digest
`1a4fe00593c4590d15aaf69a9a2dfacde3b1404133bcaa1b989f3937c5e548ff`.

## Safety postcheck

- all effect-capable host bindings remain `unconfigured`;
- the root owner was not invoked;
- no key, signature, authority, ledger, repair checkpoint or receipt was used;
- the canary remains `19b4e02d…df1a` and no temporary target exists;
- no repair/rollback/root-owner process remains;
- LXC104/110/116, Aster Agent, accepted llama/SYCL and Speech are active;
- Lab Hours dispatcher/Doctor and Proxmox daemons are active;
- the accepted News and registered-workload EPUB baselines are unchanged;
- no service action, restart, model change, schedule, booking or route occurred.

The bounded Proxmox staging directory was removed after validation. The source
rollback checkpoint was retained.

## State

The machinery is installed but inert. Installation does not authorize the
first repair. The next work is a fresh installed-manifest/dry-preflight check
and exact first-repair release packet; the actual repair remains an immediate
separate approval gate.
