# SA4 transaction inactive-install packet — 2026-11-05

An exact reversible zero-effect installation packet is now source-complete for
the joined SA4 transaction components. Fresh read-only host inspection found
four new operation/observer producers absent on LXC 104, the observer signer
and its `/usr/local/libexec/aster-sa4` parent absent on Proxmox, and two LXC
predecessors present as root:root mode 0644 single-link regular files:

- independent postcheck validator: `ab58b635…2c355`;
- receipt/ledger reconciler: `873fa764…b820`.

The packet pins seven source and destination hashes. It would create four new
inactive LXC files, checkpoint and atomically replace the two exact LXC
predecessors, and create the new Proxmox signer parent/file exclusively. The
retained LXC checkpoint is root-only; rollback restores both predecessors,
removes only unchanged new files, and removes the Proxmox parent only if it is
still empty. Any uncertainty retains state and stops.

Postchecks are intentionally zero-effect: exact installed metadata/hashes,
isolated imports, all three operation host bindings still `unconfigured`, fake
runner signer self-test, and the disposable joined rehearsal. Private-key use,
signing, live measurement, checkpoint creation, ledger use, receipt creation,
target write, repair, rollback, service action, timer, booking and model calls
are explicitly excluded.

Three focused tests pass and the full SA4 suite is **123/123**. The packet is
not an installation and grants no effect. Its next gate is the bounded
reversible inactive installation; only after that passes can a live zero-effect
dry preflight be assembled. The first real repair remains a separate exact
immediate approval gate.
