# M3 NLU E5 encoder v1 exposed cross-set rejection — 2026-10-26

## Decision

**REJECT. Do not create a fresh calibration, open the sealed holdout or enable
automatic routing.**

E5 v1 changed encoder family from BGE and used asymmetric `query:` and
`passage:` representations. Coherent whole-label voting and the accepted v2
decision/safety policy remained unchanged. Every outer fold failed to find an
eligible threshold during inner selection.

## Frozen inputs

- owner-only six-set packet: 13,991 bytes, SHA-256
  `54c5addce2e7a205febfb46e8bbc63193d751d7e789fb8ed910cfd0a6427189b`;
- frozen source packet: 7,775 bytes, SHA-256
  `763c9920dfe77e864b89403dd45636896a3cb9244e816b923404fef4393aaaaf`;
- asymmetric nested evaluator SHA-256:
  `223a4f4b28f11f0dc70e5075f8a3de54e634210af22867a2ab4456382c383b4b`;
- owner-only runtime SHA-256:
  `c4f635034b5956109b0342ab600a4a16e96c68cc8af8b0959add149bcdcaca75`;
- E5-small-v2 Q8_0: 36,685,088 bytes, SHA-256
  `afdfb5c342d2efc2a051c426dd1d00913495d5f2bbceaea100d2f3892aa31cbc`.

The dependency-free NLU suite passed 381/381 before and after the run.

## Aggregate result

- schema: `aster-nlu-e5-crossset-result.v1`;
- v1: `no_inner_threshold`;
- v2: `no_inner_threshold`;
- v3: `no_inner_threshold`;
- v4: `no_inner_threshold`;
- v5: `no_inner_threshold`;
- v6: `no_inner_threshold`;
- `nested_pass`: `false`;
- elapsed: **202.512 seconds**;
- result SHA-256:
  `8976f5936e57d0a919b89dbf15d4fdedde757e079332cfc6f5998ae39b5891a4`;
- authority: `not-granted`;
- automatic routing: `off`.

## Runtime and cleanup

The single approved evaluation used a temporary CPU-only loopback E5 process
in LXC110. The accepted Qwen3.5-9B/SYCL service and Aster Agent were not
stopped, reconfigured, replaced or restarted. The temporary process, model,
source, private six-set packet and result were removed from LXC110, Proxmox
and the Mac.

Postcheck found `local-ai-lease status` ready and both production services
active/running with zero restarts. No holdout, credential, routing, deployment,
repair authority or remote write was used.

## Practical consequence

The public gate was a useful cheap filter but did not predict cross-set
transfer. E5 nearest-neighbour iteration against these spent sets is closed.
Another attempt needs a materially different training/data method and a public
gate; do not tune E5 prefixes, neighbour settings or thresholds on these six
sets.
