# SA3 candidate-g capture-projection inactive install result — 2026-11-04

## Result

**PASS — installed inactive.** The exact two-file correction came from mirrored
platform commit `6d66683dc72f4e0e60170eb0d30f11f2c2960a40`. Its deterministic
bundle SHA-256 was
`616ce57009fdcf579ac36e338862d3fb4e84bc4eb31b7be6c8e36e1cb8fed2ca`.

The installation made no booking, model call, guest/runtime change, or service
restart.

## Installed identities and recovery

| Target | SHA-256 | Custody |
|---|---|---|
| `sa3_evidence_envelope_listener_adapter.py` | `101ce58e6e103db22b9da9532528e44ac84171e178a5baeee0a4e196fe3e3c9f` | root:root 0644, one regular link |
| `lab_hours_release_manifest.json` | `1d18a86d756e6388a72794f74f3299611234be43937c12c32159f976556d9537` | root:root 0644, one regular link |

The predecessor bytes are retained as root:root mode-0600 regular files under
root:root mode-0700 checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-capture-projection-r1-20261104`.

## Independent proof

- all 34 release-manifest pins load from the installed path;
- bounded JSON is selected from either captured channel;
- a synthetic traceback retains only
  `candidate-g guest traceback-class:KeyError`, excluding its message;
- empty capture retains only
  `candidate-g guest exit-status:137;stdout-bytes:0;stderr-bytes:0`;
- the whole-host lease is exactly ready and shared state/locks are absent;
- no port-11436 listener remains;
- Lab Hours Doctor is healthy with zero codes;
- the dispatcher, Doctor and EPUB scheduler timers are active and waiting;
- LXC104/110/116, Aster Agent, accepted 9B/SYCL llama, Speech,
  `pvescheduler`, and `pvestatd` are healthy; and
- Aster Agent, accepted llama, and Speech report zero restarts.

The exact host staging archive and directory were removed. The rollback
checkpoint was deliberately retained.

## Boundary

This installation does not recover or score spent attempts r3–r5. A future
attempt requires a new authoritative conflict-free booking and all fresh
runtime gates. It authorizes no automatic retry, model/backend change,
restart, blind-review claim, route, tool grant, or promotion.
