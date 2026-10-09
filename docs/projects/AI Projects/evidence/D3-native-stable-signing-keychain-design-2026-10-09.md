# D3 Companion Keychain access across app updates — 2026-10-09

**Status: design and local build-script candidate; no signing identity created,
no Keychain trust or item access rule changed.** This addresses Jason's request
for Companion to keep access to its own saved login until revoked, without
repeated approval after each app rebuild. It does not grant Codex, a worker,
`/usr/bin/security`, or other apps standing access to that item.

## Verified cause

The installed Companion uses the generic-password item
`com.elliottrook.aster-companion` / `oidc_session_v2` for its OIDC token set.
`KeychainStore.get` reads it at startup. The earlier installed build and the
current repair build have the same bundle identifier but different ad-hoc
designated requirements:

| Build | Code-signing designated requirement |
|---|---|
| Previous | `cdhash H"0430bed6ccd3379d288b212b7c78312d2bb3031b"` |
| Current | `cdhash H"0c8309756aacaa6f0cd00d35a8cb1ca35edb4c33"` |

`codesign` reports `Signature=adhoc`, no TeamIdentifier, and `security
find-identity -v -p codesigning` reports zero valid identities. The repository
build script explicitly re-signs every assembled bundle with `--sign -`.
**Architectural inference:** each changed binary appears to macOS Keychain as
a different code identity, which explains prompts after app replacement. A
separate confirmed defect caused an extra Keychain read during token refresh;
the installed repair removed that read. First-launch read access is necessary
and remains. A process stack showed the current replacement waiting there
until Jason resolved the prompt. The ordinary Aster composer, AI-PAM view and
closed Codex intake then opened, and the installed helper read all twelve
completed turns without inference or tool items.

Apple explains that macOS uses a **designated requirement** to recognize an
updated app as the same code and that the Keychain is one of the subsystems
using this identity. Apple's Keychain guidance distinguishes **Allow Once**
from **Always Allow** for a specific app/item. These sources support a stable
signing identity; they do not prove that this Mac's existing Keychain item will
migrate without a one-time approval.

Sources: [Apple code-signing designated requirements](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements),
[Apple code-signing guide](https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/Procedures/Procedures.html),
[Apple Keychain app access](https://support.apple.com/en-gb/guide/mac-help/kychn002/26/mac/26).

## Proposed durable route

Use **one stable, owner-held code-signing identity** for this private Mac app.
Because this is an internal HomeLab app, an owner-created self-signed
code-signing certificate in Jason's login Keychain is a candidate; it needs no
Apple Developer subscription. Apple describes self-signed certificates as
appropriate for internal testing/development and unsuitable for public
distribution. An Apple-issued Development or Developer ID identity is an
alternative if Jason later wants broader distribution. Do not make the
certificate a system-wide or TLS trust anchor merely to stop prompts.

The private signing key should stay in Jason's login Keychain, preferably
non-exportable, with confirmation required when `codesign` uses it to publish
an app update. Do not copy it into Git, OpenBao, scripts, shell history or a
CI worker; do not allow all applications to access the key. This deliberately
shifts a prompt from **every app startup/update** to **authorized app signing**.
After a one-time transition approval for Companion's existing saved-login
item, subsequent updates signed by the same identity should satisfy the same
designated requirement. Verify that on this Mac before calling it solved.

The local `build-app.sh` candidate now accepts `ASTER_CODESIGN_IDENTITY` and
an optional `ASTER_CODESIGN_KEYCHAIN` for signing, while ordinary disposable
builds remain ad-hoc. `ASTER_REQUIRE_STABLE_SIGNING=1` fails closed before
building if no stable identity is supplied. Shell syntax passed, and the
fail-closed mode rejected an absent identity. No production signing key or
installed app changed from this script edit.

An isolated disposable certificate probe in `/private/tmp` reached macOS
identity validation but could not sign because its self-signed certificate
was reported `CSSMERR_TP_NOT_TRUSTED`; its temporary keychain and files were
removed, and the user's keychain search list remains unchanged. This is a
useful negative result: a production signing identity needs a deliberately
scoped code-signing trust setup, not an ad-hoc certificate or blanket trust.

## Test and transition gate

Before changing Companion's signer, establish a local code-signing identity
and user-domain **code-signing-only** trust with its private key retained in
the login Keychain. Do not change system-wide trust. Build two isolated app
variants with different contents, sign both with the same identity, verify
both signatures and assert equal designated requirements despite distinct
code hashes. If that fails, stop before touching the installed app.

Then close Companion, retain a fresh hash-checked rollback app, and install
one stable-signed build at `/Applications/AsterCompanion.app`. Its first access
to the existing `oidc_session_v2` item may legitimately need one approval;
only an exact **Aster Companion** / saved-login prompt qualifies. Never choose
“Allow all applications” or grant the older worker credential to the generic
`security` utility. Confirm normal sign-in, AI-PAM and closed Codex intake;
restart the same signed build, then update to a second build signed by the
same identity and check that neither launch asks again. Observe a natural
token refresh without forcing time or token state. Any repeat prompt or
normal-mode regression fails the gate and triggers rollback.

Record certificate fingerprint, designated requirement, app hashes, prompt
count, restart/update outcomes and rollback result **without** recording token
or private-key material. If the signing identity expires or is lost, future
updates will require a new identity and likely a new one-time Keychain
approval. Do not silently weaken the access rule to hide that event.

## Revocation and authority

Jason can sign out of Companion to delete its saved OIDC item, remove
Companion from that item's Keychain Access Control list, or retire the local
signing certificate/private key. Those are separate controls: removing item
access blocks use of the stored login; retiring the signer blocks future
updates from presenting the same code identity. Existing sessions should be
revoked through Authentik when actual access revocation is required. AI-PAM
continues to control infrastructure credentials independently of macOS
Keychain. A stable signer is not permission for Aster or Codex to grant itself
tools or remote authority.

Creating/trusting a persistent signing identity changes a security boundary.
It is a separately reviewed operation after this design, not an implicit
consequence of approving the earlier finite test or refresh repair.
