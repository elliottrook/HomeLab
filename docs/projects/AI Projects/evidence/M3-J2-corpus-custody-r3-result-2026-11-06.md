# M3 J2 corpus custody revision-3 result — 2026-11-06

## Decision

**PASS — accepted corpus custody evidence.** The revision-3 corpus session
completed before the later evaluation-wrapper rejection. Its returned evidence
is independently valid and does not need to be repeated under revision 4.

The persistent return contains exactly three files and no private input:

- public-key file SHA-256:
  `47feec850ae4dc67443249edcbc5c134c767e293c6dcc4bbede5a31c2749574c`;
- corpus receipt file SHA-256:
  `43a9820a6438405ab010b6e358db4800c02d4ac5df8c3569db24325f1c2e284e`;
- corpus proof file SHA-256:
  `ef2a8a6dd7f205e04c505b2c3eba2ed599bb55ba9a38aeeba98edb7d91d48fa4`.

The exact corpus receipt validator passes. The receipt binds the required
corpus and independent-review identities, 768 training rows, 192 validation
rows, 16 labels, all eight comparison references, zero normalized overlap,
`content_in_receipt:false` and `authority:not-granted`. The proof binds the
receipt digest, exact scope `corpus-custody`, signer
`independent-j2-corpus-custodian` and RSA PKCS#1 v1.5 SHA-256. Independent
signature verification passes against public-key fingerprint
`47feec850ae4dc67443249edcbc5c134c767e293c6dcc4bbede5a31c2749574c`.

## Next gate

Only the fully bounded revision-4 evaluation workflow remains external. After
its five named content-free files return, Stream A must verify its exact role,
signature, distinct key, evaluation seal and zero corpus intersection before
either key can enter an owner trust-review candidate. This result authorizes no
training, Lab Hours booking, model call, routing or promotion.
