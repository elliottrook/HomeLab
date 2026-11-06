# SA4 signed zero-effect ceremony result — 2026-11-05

## Result

The first owner/AI-PAM ceremony completed and passed cryptographic verification
without becoming eligible for an effect. The retained canonical public evidence
has SHA-256
`3d3edf5473f20e222f6792392b1c22b4de8e619c8e262eb7a28874367be00833`
and is stored in
`SA4-signed-zero-effect-ceremony-public-evidence-2026-11-05.json`.

The exact evidence digests are:

| Evidence | SHA-256 |
|---|---|
| plan | `596417038ccef2ad49b689417437877820b2e918968dfd8a0eb97485c7eb6956` |
| owner approval | `71044960be433a2716774574b0eff869f6d9e0906ae754665e02a3d93facc295` |
| owner detached proof | `576e803e50286dcd0d1b4fc384002aa648feda94e3b360837d05fcd918ba4358` |
| AI-PAM grant | `1881d594755823ff196c8b0c861409f2be4c1f733e534d4b18355234628f739a` |
| AI-PAM detached proof | `b2e3ebd77bf8c2833609f4cb3b423f6ef769bfe276d4da16ad3c9e0bad61e511` |

The installed Mac helper requested one Keychain authorization and produced one
owner signature over only the exact canonical owner statement. The installed
LXC wrapper, running as `hlabroker`, produced one AI-PAM signature over only
the matching canonical grant statement. Neither private key was printed,
copied, exported or read into the repository or model context.

The compiled verifier accepted both signatures against the exact installed
public trust. It returned `authority_authenticated=true`,
`grant_consumed=false`, `maximum_effects=0`, `preflight_eligible=false`,
`effect_authorized=false` and automatic routing off. The short-lived grant and
approval expired without use.

## Postchecks

The canary remains at its drifted SHA-256
`19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`.
The repair checkpoint directory remains empty, and no claim or receipt path
exists. Transient statements were removed from the Mac, Proxmox and LXC 104.
LXC 104/110/116, Aster Agent, accepted llama.cpp/SYCL, Aster Speech,
`pvescheduler` and `pvestatd` remain healthy. No service or model changed.

## Milestone meaning

This proves the two-party public trust and signer custody can authenticate the
exact repair proposal without granting or performing it. The remaining SA4
work is the fresh effect preflight, exclusive checkpoint/one-use claim,
atomic canary repair, independent postcheck receipt, and rollback/reconciliation
proof. The first repair effect still requires a new exact immediate approval;
this expired zero-effect ceremony cannot be reused as that authority.

