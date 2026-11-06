# SA4 public trust owner review — 2026-11-05

## Recommendation

Accept the three public identities from the completed custody ceremony as the
SA4 source trust candidate:

| Role | Signer | Custody | Public-JWK SHA-256 |
|---|---|---|---|
| owner approval | `jason-owner` | macOS login Keychain, sensitive/non-exportable, empty trusted-app ACL | `17738e78d92b3ba4fff496f4d51904b6c6dd18d4acf80b3ef2a34a27ea6de946` |
| AI-PAM grant | `aster-ai-pam` | LXC 104 `hlabroker`, private mode 0600 | `f9ff0e192840dc0794e4adb65dad91a608e32e5d1d389bccbeac3612f54e9cb0` |
| independent observer | `aster-observer` | Proxmox root, private mode 0600 | `a8b5e876898ddcd7882a51c74d8b8388bb26160c96f87ab23dbeeecab9c0892b` |

The public-only custody fixture has SHA-256
`23c6544e1a4910456a00fccf5b2ae9402bff330d22db72ff6bbe5d69a9958edc`.
It passed the frozen three-domain admission validator with distinct keys and
signer IDs, no private material accepted and no installation/effect authority.

## Compiled candidate boundary

`sa4_public_trust_candidate_v1.py` compiles the three exact public JWKs,
signer IDs and digests into two candidate authority entries plus one observer
entry. Its SHA-256 is
`90c55a4e545c0f703896bf44e9d48837c6886243da3c61f2b1625afcc9094058`.

The candidate is deliberately unreachable from the live verifier modules:
`sa4_authenticated_authority_v1.TRUSTED_KEYS` remains two empty dictionaries
and `sa4_independent_postcheck_receipt_v1.TRUSTED_OBSERVERS` remains empty.
The candidate declares `candidate-only-not-runtime-trusted`, zero effect
authority and automatic routing off. Mutation tests fail closed on changed key
bytes or digests. The complete SA4 suite passes **78/78**.

No private key is represented in source. No live LXC 104 file, trust registry,
service, grant, checkpoint, receipt or repair changed.

## Owner decision requested

Approve or reject these exact three public identities for promotion into the
source trust registries. Approval permits only the next source change binding
these exact public JWKs and signer IDs into the existing verifier modules. It
does not authorize installing that changed source on LXC 104, signing a real
plan/grant/receipt, creating a checkpoint, or performing a repair. Trust
installation and the first repair remain later exact gates.
