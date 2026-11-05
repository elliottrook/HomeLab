# SA4 owner Keychain signer source boundary — 2026-11-05

## Result

A dedicated macOS owner-approval signer is now source-complete. It uses the
Security framework to create one permanent RSA-2048 private key under the
fixed application tag `com.elliottrook.aster.sa4.owner-approval.v1` with:

- `WhenUnlockedThisDeviceOnly` accessibility;
- mandatory user presence for private-key use;
- private-key usage only;
- non-extractable and sensitive attributes; and
- a fixed human-readable SA4 owner-approval label.

The helper has only four commands: a no-effect self-test, one-time creation,
public-JWK output and signature of one canonical owner-approval proof file.
The signing input is limited to 4096 bytes and must be byte-for-byte canonical
JSON with the exact detached-proof schema, `owner-approval` scope,
RSA-PKCS1v1.5/SHA-256 algorithm and `signature-only-no-effect` authority.
It rejects unknown fields, changed scope, malformed identities/digests and
non-canonical bytes. There is no private-key export command and the only
external representation call is on `SecKeyCopyPublicKey`.

The source SHA-256 is
`55864940ce9f53703683899ee777483a2fa0f0f7e410872f9451419b36bcfd6a`.
The Python build test compiles the Swift source in isolated temporary module
caches, runs its DER/canonical-JSON self-test and statically asserts the
non-exportable, sensitive, device-local, user-presence boundary. The complete
SA4 suite passes **74/74**.

## Placement review

Read-only checks established that Swift 6.4.2 and the macOS Security framework
are available. Proxmox and LXC 104 both have OpenSSL 3.5.7. The proposed
AI-PAM signer path `/var/lib/homelab-broker/sa4-signing` is absent and the
existing broker state parent is `hlabroker:hlabroker` mode 0700. The proposed
Proxmox observer path `/var/lib/aster/sa4-observer` is absent. No existing key,
Keychain entry, certificate, token or private material was enumerated or read.

## Boundary

No binary was installed and no key was created, queried, signed with or
exported. The helper self-test does not call Keychain. The installed LXC 104
SA4 framework and its empty key slots are unchanged.

## Next gate

Credential creation is now the first remaining effect:

1. compile and retain the exact owner helper, then create its device-local key
   under a visible user-presence ceremony and retain only its public JWK;
2. create a non-exported `hlabroker` RSA-2048 key under the new mode-0700
   broker subdirectory and retain only its public JWK; and
3. create a root-owned RSA-2048 observer key under the new mode-0700 Proxmox
   observer directory and retain only its public JWK.

This requires exact credential approval. It does not authorize compiling the
public keys into trust registries, installing changed SA4 source, granting a
repair, creating a checkpoint or performing an effect.
