# D3 Companion Keychain access across app updates — 2026-10-09

**Status: stable-signed version 11 restored and working; real update failed the
legacy-item prompt gate; version-13 migration candidate is local only.** The
design initially made no trust or item-access change. The approved
implementation checkpoints below record the current state.
This addresses Jason's request
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

## Approved implementation checkpoint — 2026-10-09

Jason explicitly approved creating an owner-held Companion code-signing identity,
user-domain code-signing-only trust and an isolated two-build test before app
replacement. Certificate Assistant created `Aster Companion Local Signing 2026`
in the login Keychain with both certificate and private key present. Read-only
inspection verified subject `CN=Aster Companion Local Signing 2026, O=HomeLab,
C=CA`, SHA-256 fingerprint `FA:05:7D:32:AA:13:40:1B:60:2E:58:A6:D0:CD:4C:B9:9B:79:0F:1D:66:6C:F4:C4:79:9F:74:DC:E7:03:AC:F7`, digital-signature key usage,
code-signing-only extended key usage, and expiry 2029-10-08. No private key was
exported or read. The assistant's 4096-bit selection resulted in an actual
2048-bit RSA certificate; the observed key size governs the record.

The first CLI attempt to apply `trustAsRoot` with a code-signing constraint
returned `SecTrustSettingsSetTrustSettings` invalid parameters. A second CLI
attempt with `trustRoot` stalled and was interrupted without a recorded trust
change. In Keychain Access, Code Signing was set to `Always Trust` while the
other purpose fields remained unspecified, but closing the certificate window
timed out at the macOS authorization step. The user was asked to handle any
Mac password prompt privately. Subsequent `security find-identity -v -p
codesigning` still reported **zero valid identities** and the exported user
trust settings were empty. Therefore trust is **not verified** and no signing
test or installed-app replacement may proceed yet. The installed Companion
remains the prior ad-hoc build. Resolve the local trust authorization and
recheck policy-scoped trust before resuming. Do not broaden to all-purpose or
system-wide trust merely to make the command succeed.

## Trust, two-build test and installed transition — 2026-10-09

Jason completed the macOS authorization prompt. `security find-identity -v -p
codesigning` then reported one valid identity, the new Aster certificate. An
export of **user-domain** trust settings showed exactly one trust-list entry,
for its SHA-1 fingerprint, with `kSecTrustSettingsPolicyName=CodeSigning` and
no all-purpose policy entry. The first test signing operation initially
appeared stalled, but finished validly without a visible prompt; Jason
reported no prompt. No key ACL was broadened.

Two disposable app variants were made from the same assembled bundle, with
different `CFBundleVersion` values (12 and 13). Both passed strict/deep
signature verification. Their code hashes differed (`a41b1572b738b3661002dd4013c88f8abe36722a`
and `64ebfd93ee61a22e3543962c1ced9ff714c6219c`), while both designated
requirements were exactly:

`identifier "com.elliottrook.aster-companion" and certificate root = H"10b67a3b122fafcdb2bb55124caf327115a4e6fa"`

The production build script's stable-signing mode then built and verified the
staged app. The previously installed, working ad-hoc app executable had SHA-256
`2a1ec983b2701b614ffeecf0f8f1bd2de33005e51a5431ec8de9cd704c1aa4a6`;
a strict-verified copy remains at
`/Applications/AsterCompanion.pre-stable-20261009.app`. After Companion quit,
the staged app replaced `/Applications/AsterCompanion.app`. The new executable
SHA-256 is `5a5eef77274b17d2e359e5730a4e9997ee54a5effe474b55b267546064df58b3`.
Its strict/deep signature and certificate-based designated requirement passed.
The prior installed bundle also remains temporarily at
`/private/tmp/AsterCompanion.ad-hoc-retired-20261009.app` for rollback.

First launch of the stable-signed app started, but computer-use inspection
timed out while macOS appears to be waiting at the existing saved-login item.
Jason was asked to authorize only the exact Companion/item prompt privately
with `Always Allow` if visible, or report that no prompt is visible. **Normal
mode, restart without another prompt, natural token refresh and update-after-
signing are not yet validated.** Do not mark the standing access solved until
those checks pass. The installed app is now the stable-signed version, with
the verified old app retained for rollback.

## Real update test and legacy-item finding — 2026-10-09

Jason selected `Always Allow` for the exact first-launch Companion saved-login
prompt. Normal signed-in mode opened; AI-PAM approvals and closed ordinary
Codex intake were visible. Two clean launches of installed stable-signed
version 11 subsequently opened without a prompt. A real update to signed
version 12 retained the identical textual designated requirement and passed
mutual requirement checks in both directions (`codesign --verify -R`). Yet
the first version-12 launch prompted again for Aster Companion to access the
existing `com.elliottrook.aster-companion` Keychain item. Jason supplied a
screenshot of the exact prompt and confirmed he had used `Always Allow` on
the prior prompt. This **fails** the no-repeat-prompt update gate. Signature
continuity alone did not make this legacy item update-stable on this Mac.

Keychain Access showed the exact saved-session item (`oidc_session_v2`) still
on `Confirm before allowing access`, with **five** separate
`AsterCompanion.app` entries in its trusted-app list. It did not have
`Allow all applications` selected and did not have `Ask for Keychain password`
selected. A separate diagnostic using `security find-generic-password -g`
was interrupted before it could return any credential value; any `security`
utility prompt must be denied. The initially suspected second Companion
restart prompt was that diagnostic's SecurityAgent dialog; after cancelling
it, version 11 opened normally. The actual version-12 prompt is independently
confirmed by Jason's screenshot.

Apple documents that file-based Keychain items have per-item application ACLs,
that `Always Allow` adds the current app to the trusted list, and that a new
item normally references its creator via a designated requirement. Apple's
documentation also says the trusted-application data may include a
cryptographic hash. This supports a **hypothesis**, not proof, that the
existing item carries legacy per-build trust records from its ad-hoc-signing
history. Sources: [Access Control Lists](https://developer.apple.com/documentation/security/access-control-lists),
[SecTrustedApplicationCopyData](https://developer.apple.com/documentation/security/sectrustedapplicationcopydata%28_%3A_%3A%29),
[Apple DTS on file-based Keychain ACL and updates](https://developer.apple.com/forums/thread/115425).

The blocked version-12 process was stopped, and the strict-verified signed
version 11 was restored to `/Applications/AsterCompanion.app`. It again opened
the signed-in Aster screen without a prompt. Version 12 remains preserved at
`/private/tmp/AsterCompanion.stable-v12-retired-20261009.app`; version 11
remains at `/private/tmp/AsterCompanion.stable-v11-20261009.app`.

## Candidate session-item migration — not installed

Local code now prefers a new `oidc_session_v3` item under the same Companion
service. Only when that item is genuinely absent does it read `v2`, decode the
session, and write the identical token set to `v3` from a stable-signed app.
An unavailable or invalid `v3` does **not** fall back to `v2`; that prevents a
second prompt and use of a potentially stale token. Routine saves use `v3`.
The old `v2` item is retained as rollback until an update proves `v3` access
is stable. Explicit sign-out removes both. No token values are logged or
exported. The candidate is version 13, passes all 52 local Companion tests,
and its uninstalled bundle passed strict/deep signature verification. The
tests use synthetic session strings; they do not touch the real Keychain.

The next live gate is **separate** from creating the signing identity: approve
one bounded copy of the existing saved session into a new Companion-only
Keychain item by installing the version-13 candidate. The old item must remain
intact, and the signer and bundle ID must remain unchanged. Inspect only item
presence and app state, never secret contents. Then restart version 13 and
perform a version-14 signed update; both must open without another item
approval before considering the standing-access problem solved. If creation
fails, a prompt returns, or normal Aster regresses, stop and restore version
11. Do not delete `v2`, alter its five ACL entries, enable all-app access,
or claim a durable fix on the basis of unit tests alone. Natural token refresh
remains a separate observation gate.
