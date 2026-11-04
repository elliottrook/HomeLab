# SA3 candidate-g diagnostic inactive install card — 2026-11-04

## Purpose

Install the source-proven r3 diagnostic correction without invoking candidate-g,
restarting a service, changing a model, or creating a Lab Hours booking. The
installation makes a future fresh transaction retain a bounded guest failure
class instead of collapsing it to `unclassified guest failure`.

## Exact effect

On the Proxmox host:

- replace `sa3_evidence_envelope_listener_adapter.py`
  `e668c6ca…c4123ae` → `fecb32cb…c74600c`;
- replace `lab_hours_release_manifest.json`
  `b29f1e6c…f41987` → `6fa56d9c…a157f71`.

In LXC110:

- replace `aster_llama_sa3_evidence_envelope_wrapper.py`
  `8e9e01eb…26a36f` → `1d01c8c…3a4fc2`.

The installer creates root-only rollback checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-diagnostic-r1-20261104`
on both host and guest before replacement. It refuses an existing checkpoint,
baseline drift, non-regular custody, a non-ready lease, drain/shared-operation
state, source-pin drift, failed import/manifest proof, or failed rollback proof.

## Verification before effect

- Candidate diagnostic and surrounding runtime suite: **31/31 passed**.
- Installer-focused Proxmox suite: **4/4 passed**.
- Source modules compile under macOS and target Python.
- Deterministic six-entry bundle reproduced twice at SHA-256
  `e3605e427d2c0bb40598114c015bc13a81b4accf73cd70f2e7d635b510806e3a`.
- The target staging directory and both local test bundle directories were
  removed after verification.

## Required installed postcheck

Accept only when:

1. all three installed hashes and root custody match;
2. the release manifest loads all 34 exact pins;
3. noisy stderr yields its final bounded JSON code and malformed stderr remains
   unclassified;
4. a guest result error yields only bounded count plus sorted class names;
5. the lease is still ready, no drain/shared lock exists, production services
   remain healthy, and no candidate process or listener exists.

Any failure triggers rollback and is NO-GO. Preserve an uncertain checkpoint or
target rather than overwriting it.

## Exclusions

This effect authorizes no workload invocation, model request, booking, retry,
service restart, backend/model change, blind review, routing change, or
promotion. A future candidate run requires a new authoritative conflict-free
Lab Hours booking and all fresh runtime gates.
