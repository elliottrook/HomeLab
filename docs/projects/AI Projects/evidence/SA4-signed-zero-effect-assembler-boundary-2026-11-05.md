# SA4 signed zero-effect assembler boundary — 2026-11-05

## Result

`sa4_signed_ceremony_packet_v1.py` now closes the boundary between the two
fixed signer outputs and the installed authenticated-authority verifier. It
accepts only the exact five-field unsigned packet, canonical owner and AI-PAM
statements, and two lowercase 256-byte RSA signatures. It inserts each
signature only into its matching detached proof and immediately invokes the
compiled verifier over the exact plan, approval, grant and current ceremony
time.

The assembler accepts a result only when authority authentication is true,
the grant is unconsumed, maximum effects are zero, preflight eligibility is
false and automatic routing is off. Any changed scope, statement, signature
shape, consumed grant, preflight eligibility or nonzero effect fails closed.
Its returned record contains the exact public evidence bytes and digests while
still declaring `effect_authorized=false`.

Four focused tests cover exact assembly, signature-shape rejection, effectful
verifier rejection and changed-statement rejection. The complete SA4 suite
passes **97/97**. Tests use synthetic signature bytes and an injected zero-
effect verifier result; neither installed signer nor private key was invoked.

## Next gate

The source and inactive installed paths are ready for one short-lived signed
zero-effect ceremony. That ceremony requires a fresh packet, an explicit owner
Keychain authorization prompt, one AI-PAM signature, immediate cryptographic
verification and deletion of transient unsigned inputs after the public
evidence is retained. It cannot claim the one-use ledger, create a repair
checkpoint or change the canary. The first repair effect remains a separate
exact immediate approval after a later fresh preflight.

