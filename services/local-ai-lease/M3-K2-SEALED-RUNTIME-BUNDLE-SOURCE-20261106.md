# M3 K2 sealed runtime bundle — source review 2026-11-06

Status: source-only, content-free and non-authorizing. This review did not
extract or install the bundle, register a workload, create or change a Lab
Hours reservation, acquire a lease, start a listener, or change production.

## Exact identities

| Item | SHA-256 |
|---|---|
| sealed runtime bundle | `3b7e7cf40b08808cb94721a5778a1474e35a4d8f8d30c7dac858a37dc6e6aed6` |
| `scripts/local-ai/m3_k2_sealed_bundle_contract.py` | `e2b9986487336a449940149cc5eb0ed2f48eafa14ee68c172513df1ef42bad86` |
| `scripts/local-ai/test_m3_k2_sealed_bundle_contract.py` | `f4f93008a8089bd75d12c3b4b1482720149fed8b16a79d69a048226057357ab7` |

The validator pins preregistration digest
`4e7754585aeeef597c66eb2d3f2c6bf673f140f35c2f06d1856274429580adb1`
and all thirteen source-file digests.

## Fail-closed checks

The validator reads the gzip-compressed tar archive without extracting it and
requires the exact member set, regular files only, root numeric ownership,
mode `0600`, zero mtime, empty owner/group/link names, bounded non-empty member
sizes, the canonical content-free manifest, and every source hash. It rejects
an outer archive identity change independently of internal source validation.

The manifest requires `private_inputs_included=false`,
`effect_authorized=false` and `authority=not-granted`. No corpus, evaluation,
key, credential, nonce or model output is in the package.

## Verification

- focused tests: 4/4 passed;
- syntax compilation: passed;
- exact archive validation: passed with 13 source files and the expected
  preregistration digest;
- extraction, transfer, installation and runtime effects: none;
- next gate: the already-booked K2 development transaction must complete and
  restore production before any separate installation or release gate can be
  considered.
