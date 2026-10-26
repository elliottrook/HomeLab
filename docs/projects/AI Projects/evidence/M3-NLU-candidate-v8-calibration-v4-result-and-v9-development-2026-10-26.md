# M3 NLU Candidate-v8 calibration-v4 result and Candidate-v9 development — 2026-10-26

## Decision

**REJECT Candidate-v8.** Its one bounded, tool-free calibration-v4 run
completed all 60 attempts, but the registered zero-unsafe-route constraint
failed. The selector exited `2` and wrote no threshold. The independent
holdout remains sealed and automatic routing remains off.

## Independent calibration-v4 custody

- Candidate-v8 artifact SHA-256:
  `033aa138e9995034d0ea19237f929e4dccab1c9341f0ff531e03ced84ac6d6a1`
- Synthetic source SHA-256:
  `09f82238506e01b8e8e2b443dfaee566263344a020032862cfb1570e958079c3`
- Blind labels SHA-256:
  `daff07ce5521ccc9469a780c30ac5c625467435d84e21d1c760c05939cc50edb`
- Custody manifest SHA-256:
  `12bb95b21c003ba43fbc40252eb8b6eee5eb3cb874690323cc953864d824f17d`
- Normalized text-set SHA-256:
  `1a78b883cc5a39c88f96b5def07574c2ebe1821dfc17c15465ca80e87cbb906f`
- Content-free release artifact SHA-256:
  `75bcffb8c6ef995e2b5e8ff09a5b8287790cdc418237282b03f3033af7e9a581`
- Release canonical self-hash:
  `f90aa4e1a8f24d4f2c5172c5d0a718560a2ad431c5091723b1f2d2e3b10182c2`
- Registered policy SHA-256:
  `805534b7ae00005207ebb02572efca09145d3c24c0eb59f772353e8130988c57`

The source contains 60 fresh fictional cases, ten per family, with zero
normalized overlap with public development or calibrations v1 through v3.
Case custody, blind label review and release derivation remained separate.

## Bounded calibration-v4 result

The exact packet ran in root-only LXC110 custody against the already-running
accepted llama/SYCL service. No service, News schedule, lease, tool or route
was changed.

- Run SHA-256:
  `34203b034d2f2ca8dd4a12e1e3aacbc62e7ee0272ca235af3ba9994b4f9f1e57`
- Attempt-journal SHA-256:
  `d4f22e51774d2fcfac7d55e457ae50af49f2f6184de05708b0bee0bd842b3d66`
- Score SHA-256:
  `ac45b6800be8cfcaad517240193435d1225fbf33ccdfe5da417f7b8ddc56c0df`
- Attempts: `60/60`
- Structurally valid responses: `54/60`
- Routed: `38/60`
- Safe and exactly correct routed rows: `30/60`
- Privacy underclassifications: `0`
- Unsafe false routes: `3`

The three aggregate unsafe classes were safety-control-disablement denial
bypass, private-data-publication denial bypass and impossible-or-unverifiable
request abstention bypass. No request text or holdout material was used to
develop the successor.

## Candidate-v9

Candidate-v9 adds general rules for those three safety classes, canonical
capability ordering, backup deletion, combined household/timer actions,
general factual answers and public-only research. It remains local-only,
tool-disabled, case-data-free and `authority=not-granted`.

- Adapter SHA-256:
  `74bd1ee43254556c09a29141120c536b62d8ac17c6ea2e6ac4d35397c97e0023`
- Policy artifact SHA-256:
  `6672dc9209dda1b848a7e93be04264f34626fba8c2206cdfa0d798a828dc5953`
- Candidate canonical bundle hash:
  `85f74dd4807cc7fff3fd427d4d1f4336fa88e1e5a0b24b7d9c92e565edcd1d0c`
- Candidate artifact SHA-256:
  `1941b4754c5195e11b623479f63cb368cacfea64a7adc3223bf22794e3b825f5`

Its public 24-case development run completed 24/24 with 24 structurally valid,
22 exact, zero privacy underclassification and zero unsafe false routes. The
remaining mismatches are one ambiguous change family and one mixed personal
research capability set. Result SHA-256:
`91770cf00d182097c5805fadbdd8c67a1220f760d5e37fe6fd1239f9f410a474`.

## Next gate

Candidate-v9 needs a fresh, independently created and blind-labelled
calibration-v5, disjoint from development and calibrations v1 through v4.
Candidate-v8's calibration is now development evidence only. No threshold,
holdout access, shadow promotion or automatic route is authorized.
