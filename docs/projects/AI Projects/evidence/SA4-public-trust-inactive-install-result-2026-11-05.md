# SA4 public trust inactive installation result — 2026-11-05

## Result

The approved four-file public-trust installation completed on LXC 104 without
an effect, service action or restart. Fresh preconditions matched the three
installed empty-trust source hashes and found the candidate module absent.
The installer retained exact mode-0600 rollback copies under the root-owned
mode-0700 directory
`/var/lib/aster/sa4/source-checkpoints/public-trust-v1` before replacing any
source.

The installed public-source hashes are:

| Installed file | SHA-256 |
|---|---|
| `sa4_authenticated_authority_v1.py` | `367bf1a1e473363b8c8aac7d13a4f06456964de45093c172e32a1f3c93a725d6` |
| `sa4_independent_postcheck_receipt_v1.py` | `ab58b635d823a1c82f30d8d89f68c1ed25519914270c7e3d467228bf2452c355` |
| `sa4_key_custody_slots_v1.py` | `e1d9088a1725847a6b7f16460177e266e076fd987b01894daf4a69c5b2b8d0d0` |
| `sa4_public_trust_candidate_v1.py` | `3c1f02bba3985033157977d6810192888b09595ec3af0c55ef1e1c15e135195e` |

## Independent postchecks

All 18 installed modules imported from the installed directory. The installed
custody slots report exactly the accepted owner, AI-PAM and observer public
identities; the authority registries contain one owner key and one AI-PAM key,
and the observer registry contains one observer key. The candidate bytes match
those source registries. All four files are root-owned regular files with mode
0644 and no temporary file remains.

The verifiers still report `effect_authorized=false`, automatic routing is
off, and no approval, grant, claim, checkpoint, receipt or repair was created.
LXC 104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech, `pvescheduler`
and `pvestatd` remained healthy. No SA4 unit exists and no service was started,
stopped, reloaded or restarted.

## Boundary

This closes the inactive public-trust installation gate only. The retained
private keys were not read, printed, copied or exported. A signed zero-effect
ceremony, the production-target preflight correction and the first repair
effect remain separate gates. The first repair effect still requires Jason's
exact immediate approval after all static and runtime preconditions pass.

