# Full-stop retained receipt sequencing review — 2026-10-15

**Scope:** Read-only review of the platform owner's current main-checkout
source. No Proxmox installation, timer, lease, backup scan or model call.
The platform owner owns the implementation and live release card.

The source-only `FixedSourceAdapters.backup_from_retained()` verifies a fixed,
root-owned prior archive check against the current Proxmox inventory and
TrueNAS chain. It is intentionally unused. The default `evidence()` method
still calls `backup()`, which runs a serial live `zstd -t` check with a
300-second cap per archive. `source_receipt_boundary.produce_candidate_receipt()`
calls that default `evidence()` method. The current
`platform_receipt_producer.main()` requires `lease.json` to be in `leased`
state before calling the boundary.

**Architectural inference:** A revised full-stop flow needs two explicitly
ordered decisions: current-cycle backup integrity before effectful lease
acquisition, then post-stop consumer quiescence before benchmark admission.
The existing post-lease receipt path alone cannot be cited as evidence that
the pre-acquire backup gate is wired to the retained method. The revised card
must identify which fixed producer writes the retained result, which verified
pre-acquire consumer reads it, and how the post-stop receipt binds to the same
lease and backup identity. This is a sequencing question, not proof that the
platform owner's new source candidate is defective.

The platform owner was sent the exact call-chain observation. The installed
controller/watchdog schema mismatch and absence of a trusted current-cycle
integrity receipt remain the measured live NO-GO gates; this source review
does not clear them.
