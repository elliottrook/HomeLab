# F4/F5 fixed-source writer inactive installation review — 2026-10-26

Result: **PASS AT THE INACTIVE BOUNDARY**

Stream A independently reconciled the platform source at Forgejo branch
`codex/f4-f5-root-writer`, approved tip `16a6b1c5`, the installed target and
the platform result subsequently committed as `69690526`.

The installed files match the reviewed candidate:

| Target | SHA-256 | Custody |
|---|---|---|
| `stream_a_evaluation_f4_f5_transaction.py` | `db4066d05ec37e27c1301a4bf79f35c7d418aa797bca49f43d8f33326c0cbbaa` | root:root 0644, one regular link |
| `stream_a_evaluation_f4_f5_root.py` | `d57e95c196a079bce6460b5d2cca514d27a27db1c39fdfa815ec0a365c5b3d18` | root:root 0644, one regular link |
| `/usr/local/sbin/stream-a-evaluation-evidence` | `7685d5896931b8c684a00ed4428192a58dd7a503464160a5c27fa48b12c56685` | root:root 0755, one regular link |

The final target-side run passed 9/9 root-writer/transaction tests and imports
against the installed dependency set. Two earlier pre-install test harness
failures occurred before any target copy and each reported complete rollback
with `uncertain=0`. The corrected test removes its dependency on a newer
development-only decoder; the three installed candidate hashes did not change.

Postchecks found the whole-host lease exactly ready; all whole-host and
evaluation lease/lock paths absent; F4, F5 and admission absent; Aster Agent,
accepted llama.cpp/SYCL and Speech active; News timers enabled/active; and
Proxmox scheduler/status daemons active. The writer was not invoked. No model,
service, timer or schedule changed.

This closes the missing fixed-source writer and inactive-install gates. It
does not complete F4 or F5. One same-cycle invocation may occur only after
accepted F2, verified F3 and the successful 03:00 TrueNAS pull. F6 remains a
separate restart/effect approval.
