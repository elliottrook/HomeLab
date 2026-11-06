# SA4 signer/preflight reversible install review — 2026-11-05

## Fresh target facts

Read-only checks found the current macOS helper unchanged at
`b56d9a35d1edd66a4efcc5a1624e5c1640797678e7397a9a1c2489f3720e372b`
with `jelliott:staff` mode 0755. On LXC 104, the installed preflight source is
the expected old SHA-256
`a45335dcb6ab209433e71bd486345904d4e0748f5ae03bc85f24a7863926b569`
at root:root mode 0644 and the AI-PAM wrapper is absent. Metadata-only checks
confirmed the existing private key remains a regular `hlabroker:hlabroker`
mode-0600 file and `/usr/bin/openssl` remains a root-owned mode-0755 regular
file. No private key bytes or Keychain item were read.

Two independent builds of the corrected owner source produced the same
ad-hoc-signed binary SHA-256 when compiled under its versioned installed name:
`ecf91f6356c368777a5910d8e4c228418ebc05728f3c11f1d7b0b53ed6288836`.
Strict code-sign verification and the no-Keychain self-test passed.

## Exact install packet

`sa4_signer_preflight_install_plan_v1.py` freezes three changes:

1. create the new versioned macOS helper
   `sa4-owner-signer-4148fee1` without replacing the currently installed
   helper;
2. retain the exact old LXC preflight source mode 0600 in root-owned mode-0700
   checkpoint `preflight-correction-v1`, then atomically install corrected
   source SHA-256 `d96fcba…a2ea06`; and
3. exclusively create the AI-PAM wrapper as root:`hlabroker` mode 0640 with
   SHA-256 `10a7e39f…92e55`.

Postchecks are limited to exact hashes/metadata, owner binary strict code-sign
and self-test, real canary resolution, AI-PAM wrapper import/canonical
validation, and unchanged production health. They do not query Keychain or
invoke either private key. Rollback removes only the new versioned helper and
wrapper when their hashes remain exact, and restores the retained preflight
bytes; uncertainty retains state and stops.

The three focused plan tests and the complete SA4 suite pass; the complete
suite is **93/93**. No installation, signing, grant, claim, checkpoint, repair,
receipt, service action or restart occurred.

## Next gate

The packet is ready for one bounded inactive installation. It is not a signing
ceremony and grants no repair authority. After installed-path validation, the
first signed ceremony remains zero-effect. The first repair effect still
requires its own exact immediate approval after fresh preflight.

