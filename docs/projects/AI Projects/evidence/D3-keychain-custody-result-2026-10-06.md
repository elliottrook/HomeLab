# D3 Mac Keychain custody — result

**VERIFIED CURRENT STATE:** the approved fictional check passed once.
Jason approved the [exact gate](D3-keychain-custody-gate-2026-10-06.md).
Combined source fingerprint verified before execution:
`2175c99afda3aefea71eef5dc9e3d4ee303e47e24831c9481b6eb6ff5d1ae159`.
Approval is consumed and does not authorize real credential provisioning.

The exact helper returned:

```json
{
  "created": true,
  "exact_reader_passed": true,
  "fixture_removed": true,
  "real_credentials_used": false,
  "model_calls": 0
}
```

The check established absence before creating the dedicated worker item,
compiled the helper in a temporary directory, supplied the public fictional
value over stdin, and retrieved the exact value using `/usr/bin/security`.
Deletion occurred only after that equality check. The helper confirmed absence
and exited successfully, cleaning its temporary compiler directory.

A separate `/usr/bin/security find-generic-password` query for only service
`com.elliottrook.aster-codex-worker`, account `authentik-app-password`, suppressed
all item output and returned status **44 (not found)**. No password-read option
was used by this independent cleanup check. No manual consent action was needed
during the observed run; this does not guarantee prompts cannot occur later.

No existing Companion/ChatGPT login item, vault, identity provider, recovery
material, service or repository remote was changed. No permanent worker item
remains. No rollback was needed. The test used an intentionally public fixture,
not an authentication credential.

## Limits and resume

The proposed reader works in the current Mac user/Keychain context. This does
not prove isolation from other code running as Jason, behavior after reboot or
lock, or suitability for unrestricted tool-enabled Codex. Keep those boundaries
explicit. The Swift implementation's legacy Keychain API warnings remain a
maintenance limitation; this successful observation does not erase them.

Both custody primitives now have host evidence. Continue the protected
provisioning controller, durable stage recording, human-only vault ceremony
instructions and bounded integration deployment. Do not repeat these primitive
checks without a changed implementation or new failure. Real credentials have
not been issued; delegation remains disabled and no push occurred.
