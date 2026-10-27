# Stream A F4/F5 root writer inactive installation result

Date: 2026-10-26 America/Vancouver  
Source branch: `codex/f4-f5-root-writer`  
Approved source tip: `16a6b1c5b9a4f7d3f82975f458445e2d5cb82758`

Result: **PASS — INSTALLED INACTIVE**

## Installed files

| Target | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_f4_f5_transaction.py` | `db4066d05ec37e27c1301a4bf79f35c7d418aa797bca49f43d8f33326c0cbbaa` | root:root, 0644, one regular link |
| `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_f4_f5_root.py` | `d57e95c196a079bce6460b5d2cca514d27a27db1c39fdfa815ec0a365c5b3d18` | root:root, 0644, one regular link |
| `/usr/local/sbin/stream-a-evaluation-evidence` | `7685d5896931b8c684a00ed4428192a58dd7a503464160a5c27fa48b12c56685` | root:root, 0755, one regular link |

The final transaction ran 9/9 root-writer and transaction tests against the
installed dependency paths, passed installed imports and wrapper argument
rejection, and independently re-read all three target hashes and custody.

## Pre-install test corrections

The first attempt failed before installation because Python 3.13 interpreted
absolute unittest filenames as module names. The transaction reported
`rolled_back`, `uncertain=0`; no target existed.

The second attempt exposed a development-test-only dependency on the newer
`decode_stream_evidence` helper, which is absent from the installed
`pre_acquire_receipt.py`. The candidate source itself had already removed that
runtime dependency. The transaction again reported `rolled_back`,
`uncertain=0` before installation. The test was corrected to inspect the exact
canonical F4 payload directly. The three installed candidate hashes did not
change.

## Postconditions

- `local-ai-lease status` remained exactly `ready`.
- Whole-host and evaluation lease, lease-lock and operation-lock paths remained
  absent.
- F4, F5 and admission paths remained absent. The writer was not invoked.
- Aster Agent, accepted llama.cpp/SYCL and Aster Speech remained active.
- Both News timers remained enabled and active; `pvescheduler` and `pvestatd`
  remained active.
- No service or timer was stopped, started, restarted or enabled; no model was
  called or changed; no schedule was changed.

This result closes only the inactive installation. One separately approved
invocation may be considered after the same-cycle F2 and F3 are complete and
the 03:00 TrueNAS pull has succeeded. That invocation writes only F4, F5 and
admission. F6 remains a separate restart/effect gate.
