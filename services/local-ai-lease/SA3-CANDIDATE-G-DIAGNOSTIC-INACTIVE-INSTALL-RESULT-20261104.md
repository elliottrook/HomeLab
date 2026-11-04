# SA3 candidate-g diagnostic inactive install result — 2026-11-04

## Result

**PASS — installed inactive.** No candidate workload or model request ran, and
no service restarted.

The installed source came from mirrored platform commit
`b92a551b1e225af8399b0c1fcafdb356c519def9`. Its committed deterministic
bundle SHA-256 was
`9ba99e5819384f0fe62b76292b68c81731a7f51755cd5ae8f1b44484c3704510`.

## Installed identities

| Target | SHA-256 | Custody |
|---|---|---|
| Host `sa3_evidence_envelope_listener_adapter.py` | `fecb32cb29b2981aeab769efff7450e93c9853b30f79ca2131acb4015c74600c` | root:root 0644, one regular link |
| Host `lab_hours_release_manifest.json` | `6fa56d9c98817e84875966fb5addb6006fa14e9f07edb4cf3acbebc50a157f71` | root:root 0644, one regular link |
| LXC110 `aster_llama_sa3_evidence_envelope_wrapper.py` | `1d01c8c5bda942ddb42386eb56066c4858bf8032db39c136a4c9efbb933a4fc2` | root:root 0644, one regular link |

Host and guest each retain root:root mode-0700 checkpoint directory
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-diagnostic-r1-20261104`;
its predecessor files are root:root mode 0600 and one regular link.

## Installed proof

- all 34 release-manifest pins load;
- noisy host stderr returns the last bounded JSON code;
- malformed host stderr remains `unclassified guest failure`;
- the guest wrapper returns only the exact bounded count and sorted
  `TimeoutError,ValueError` class set for a synthetic result error;
- the aggregate Doctor returned `state=healthy`, `codes=[]`;
- the whole-host lease returned exactly `ready`;
- no drain state, drain lock, shared-operation lock, candidate listener, or
  port-11436 listener remained;
- LXC104/110/116, Aster Agent, accepted 9B/SYCL llama, Speech, News, EPUB,
  `pvescheduler`, and `pvestatd` were healthy;
- Aster Agent, accepted llama, Speech and both Proxmox daemons reported
  `NRestarts=0`.

The Lab Hours Doctor timer remained enabled, active and waiting; its direct
diagnosis found no reservation or restoration fault.

## Cleanup and boundary

The exact host staging archive/directory and local bundle directory were
removed. Rollback checkpoints were deliberately retained.

This installation makes a future failure class observable; it does not recover
or score r3. A fresh run still requires a new authoritative booking and all
fresh lease, lock, production, and installed-hash gates. No retry, model change,
restart, blind review, routing change, or promotion is authorized here.
