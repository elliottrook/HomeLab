# Candidate-g reserved-runner inactive activation result — 2026-11-03

**Result: PASS; installed inactive.**

The corrected deterministic bundle
`68ba4a16129b17f2e2ed2fc8c8a0f9e8236b7a1dda05f602f9766362b03f38d0`
was installed once. The live-ledger precheck found only completed/failed
historical workloads and standing future exclusive-stack reservations with no
runner workload. No booking was claimed or running, and all lease/drain state
and locks were absent.

Installed identities and custody:

| Target | SHA-256 | Custody |
|---|---|---|
| `full_inference_lab_runtime.py` | `b4fc31b0eaeab14b0beb81b47103f2d03a62cf9e6bf3bbccdfc4560a0f444da9` | root:root 0755, regular, one link |
| `lab_hours_reserved_runner.py` | `63c7a116f326161dfb550cb3bfdaf268cbab29820e7b9f0105e810c595a75aba` | root:root 0755, regular, one link |
| `lab_hours_release_manifest.json` | `c970bd70cc7e97fa707bdec50a027add4e6a3a77189aa5a86903be6e4b049886` | root:root 0644, regular, one link |

The checkpoint is root:root mode 0700. Installed imports, the complete release
manifest and exact candidate-g runner registration passed. No candidate unit,
lease, lock, drain state or candidate process exists. LXC104/110/116, Aster
Agent, accepted aster-llama and Speech are active; `pvescheduler`, `pvestatd`
and the Lab Hours Doctor timer are active. Existing inactive dispatcher, News
and EPUB timer states were unchanged by this installation.

No booking, service stop, model request, retry, restart, route or promotion
occurred. Candidate-g is now runnable only through a fresh authoritative
reservation plus the existing whole-host lease/shared-lock gates.
