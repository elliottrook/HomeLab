# M3 NLU dense supervised head v1 exposed cross-set rejection — 2026-10-26

## Decision

**REJECT. Do not create a fresh calibration, open the sealed holdout or enable
automatic routing.**

The regularized supervised kernel-mean head was trained only inside each
nested partition over the fixed BGE dense representation. All six outer folds
failed to find an eligible threshold during inner selection. The learned-head
family therefore does not satisfy the accepted v2 coverage, error and safety
policy on the exposed development battery.

## Frozen inputs

- head source SHA-256:
  `2d58861c5f2e9c71a7da9ccef80f6f2048bdd86851f7782f07c09e23b230e152`;
- nested evaluator SHA-256:
  `e3000a277d35c6bbd82efa31f6e35aff2f640e18d795c2a82a50bfe360cb3410`;
- runtime wrapper SHA-256:
  `2565131dbc14cdbc15bedb09c548623f6a77ced7f4804589b5f91324113952b1`;
- shared vector loader SHA-256:
  `f1532fcbab4d9c5b4388509a146f22c0b5da31d166b9b9a1278b5afdbdd22789`;
- owner-only six-set packet: 15,191 bytes, SHA-256
  `2d6c46641de59bb424adf84efbd11494040243f5760c1cc8a3d2f3baf82a1637`;
- source packet: 7,086 bytes, SHA-256
  `30c067fe6541ddfcaee9a9ca594de14b8781255431d7430050c892605add89e6`;
- BGE Q4_K_M: 24,808,576 bytes, SHA-256
  `363a0a4855dff6c653e06efe3209157debcf7f74e52d0d7c71e2747cd523043e`.

The dependency-free NLU suite passed 375/375 before the run.

## Nested result

The one approved private evaluation completed in **63.819 seconds**. Its
canonical terminal aggregate SHA-256 is
`38a5517eb801f422441ba8ec6676f8b2d863eaa6d4035029d7196120048af67d`.

| Outer set | Inner selection | Outer result |
|---|---|---|
| v1 | no eligible threshold | not evaluated |
| v2 | no eligible threshold | not evaluated |
| v3 | no eligible threshold | not evaluated |
| v4 | no eligible threshold | not evaluated |
| v5 | no eligible threshold | not evaluated |
| v6 | no eligible threshold | not evaluated |

`nested_pass` is `false`, authority is `not-granted`, and automatic routing
remains `off`.

## Runtime and custody

The encoder ran once as a temporary CPU-only loopback process in LXC110. The
accepted Qwen3.5-9B/SYCL service and Aster Agent were not stopped, replaced,
reconfigured or restarted. After bounded reconciliation, the temporary
encoder process, model, source, six private sets and result were removed from
LXC110, Proxmox and the Mac. `local-ai-lease status` returned `ready`; both
production services remained active/running with zero restarts.

## Practical consequence

Nearest-neighbour and supervised-head variants over this BGE representation
have both failed honest cross-set transfer. Do not tune this head or reuse
these spent sets to select another BGE-head variant. The next M3 candidate
must change the encoder family and first pass the public gate before any
private six-set transfer is proposed.
