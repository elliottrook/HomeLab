# Candidate-g reserved-runner inactive activation card — 2026-11-03

## Decision boundary

This card freezes a reversible three-file inactive replacement that admits the
already installed `sa3-evidence-envelope-quality-v1` transaction to the booked
Lab Hours runner. It does not create a booking, schedule a unit, acquire a
lease, stop production or make a model request.

## Exact replacement

| Target | Installed predecessor | Candidate | Mode |
|---|---|---|---|
| `full_inference_lab_runtime.py` | `875836ce…ef40` | `b4fc31b0…4da9` | `0755` |
| `lab_hours_reserved_runner.py` | `ee4ab4c3…5abf` | `63c7a116…aba` | `0755` |
| `lab_hours_release_manifest.json` | `9dfea8ad…6792` | `c970bd70…9886` | `0644` |

The deterministic four-file bundle is
`aster-sa3-envelope-runner-activation-v1.tar.gz`, SHA-256
`ce6242bc603668ce5c1f32af50145d4fbdf128384e987bc172fb325c454f794f`.

## Fail-closed gates

The installer requires exact predecessor and candidate bytes, regular-file
custody and modes, no existing checkpoint, no active lease/drain state or lock,
and no reserved, claimed or running Lab Hours booking of any workload. It
checkpoints every predecessor before replacement, imports both changed modules,
requires the candidate-g runner kind to be present, and validates the complete
release manifest. Any failure restores all three predecessor files.

The runner accepts only the exact candidate-g workload profile and validates a
content-free receipt with 20 cases, exactly 14 model requests, zero errors, a
64-character lowercase result digest and `production_restored=true`. The
existing full-drain controller, listener absence check, GPU-holder check and
unconditional restore path remain in force.

## Offline proof

- all Lab Hours tests: 39/39 passed;
- runtime, candidate transaction/listener and installer tests: 27/27 passed;
- two independent deterministic bundle builds matched the frozen digest;
- source formatting and Python compilation passed.

## After installation

Installation alone leaves the candidate inactive. Before any run, Stream A
must query the authoritative reservation ledger for the full execution and
recovery window, create an exact registered booking, then pass the fresh
booking, whole-host lease, shared-lock, accepted-production and quiet-host
runtime gates. No retry, model/backend change, routing promotion or restart is
included.
