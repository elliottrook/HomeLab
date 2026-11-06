# SA4 three-way custody candidate result — 2026-11-05

## Result

Jason approved the corrected owner-only Keychain mechanism from commit
`485eff23`. The corrected Swift source compiled and passed its no-effect
self-test. Its ad-hoc-signed binary SHA-256 is
`b56d9a35d1edd66a4efcc5a1624e5c1640797678e7397a9a1c2489f3720e372b`.
The exact owner tag was still absent immediately before creation.

The traditional login-Keychain ACL helper then created one sensitive,
non-extractable RSA-2048 owner key with an empty trusted-application list. The
helper returned only its public JWK. A second public-only query returned the
same identity. The owner public-JWK SHA-256 is
`17738e78d92b3ba4fff496f4d51904b6c6dd18d4acf80b3ef2a34a27ea6de946`.
The obsolete failed helper binary was removed after the corrected helper and
public identity passed validation.

Together with the previously created custodians, the retained public-only
candidate has three distinct fingerprints:

- owner approval: `17738e78…6de946`;
- AI-PAM grant: `f9ff0e19…4e9cb0`; and
- independent observer: `a8b5e876…c0892b`.

The candidate fixture SHA-256 is
`23c6544e1a4910456a00fccf5b2ae9402bff330d22db72ff6bbe5d69a9958edc`.
The source admission validator accepted the exact role order, custody domains,
signer locations, three distinct signer IDs and three distinct canonical
RSA-2048 public keys. It confirmed no private material was accepted, automatic
routing is off, no effect is authorized and the candidate is ready only for
owner review—not installation. A retained-fixture regression raises the full
SA4 suite to **75/75**.

## Boundary

No private key was printed, copied, exported, committed or placed in model
context. The installed LXC 104 SA4 source still contains empty custody slots
and empty trust registries. None of the three identities can currently
authorize a plan, grant or receipt. No service, restart, checkpoint, repair,
model or route changed.

## Next gate

The three public identities can now be compiled into a source trust candidate
for owner review. That source work is offline and effect-ineligible. Installing
the compiled public trust into LXC 104 will be a later exact remote mutation.
The first signed ceremony, grant, checkpoint and repair remain separate gates;
the first repair effect still requires exact immediate approval.
