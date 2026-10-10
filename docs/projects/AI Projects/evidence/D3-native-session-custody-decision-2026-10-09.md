# D3 native saved-login custody: next decision

> Status: Design decision after a failed live update gate; no new credential
> change authorized or implemented.
>
> Owner: Jason. Stream: A, subject to the programme's stop conditions.

## Verified current state

- Signed Companion version 13 is installed, opens signed in, and restarts
  without a Keychain prompt. The `oidc_session_v3` item is present with
  Companion-only access, not all-app access.
- A same-signer version 14 update produced another Companion Keychain prompt.
  The no-repeat-prompt update gate failed. Version 14 was removed from the
  active application path; version 13 was restored and restarted normally.
- Reverting the binary to version 11 did not restore its older login: the app
  reported that its session was expired or revoked. The exact reason was not
  traced. A copied refresh token must not be counted as a durable rollback.
- `codesign -dv` on installed version 13 reports
  `TeamIdentifier=not set`; `codesign -d --entitlements` returned no
  entitlements. This is a metadata check, not access to signing secrets.
- The prompt was observed during an **app update**. This evidence does not
  establish a prompt on every normal launch or every Aster request. It also
  does not establish that AI-PAM grants are failing; the Mac Keychain's app
  trust and AI-PAM's infrastructure authority are separate controls.

Full observations and rollback paths are in the
[signing and Keychain evidence](D3-native-stable-signing-keychain-design-2026-10-09.md).

## Decision now

Keep version 13 as the working native app. Do not repeat a real-session
migration, expand the Keychain ACL, or build a standing credential broker yet.
The measured failure is one prompt per binary update in this test, while normal
restarts passed. During development, avoid installing every local build;
release only after offline tests and a reviewed build gate. Record prompt
frequency separately from build count and normal-launch count. A helper
service solely to remove update prompts would add lifecycle, IPC and identity
failure modes before its value is demonstrated.

This interim decision is **not** an acceptance of repeated prompts in normal
use. If prompts recur without an app update, or token refresh fails, pause D3
release and investigate that separately. Natural token refresh has not yet
passed a deliberate observation gate.

## Candidate alternatives and evidence threshold

| Option | Potential benefit | Constraint or cost | Decision |
|---|---|---|---|
| Current signed app with fewer installs | No new security boundary; working restart path | One prompt may recur on each update; user friction | Interim default |
| Apple Developer ID signing plus data-protection Keychain | App-ID/access-group model designed for stable per-app access | Requires a valid Apple Team ID, entitlements, provisioning where required, and an owner decision on Apple dependency | Feasibility study only |
| Immutable local login helper | Helper's Keychain identity can stay fixed while UI builds change | New local privileged service and IPC; caller verification, token exposure, failure recovery and maintenance | Defer until prompt frequency or availability justifies it |
| AI-PAM/OpenBao as Companion OIDC session store | Central custody and revocation | Adds network/service dependencies to a household interface; does not by itself solve local app authentication | Do not adopt for this symptom |
| All-app Keychain access or automatic approval | Removes prompts | Materially broadens secret access | Reject |

Apple's [TN3137](https://developer.apple.com/documentation/technotes/tn3137-on-mac-keychains)
distinguishes file-based from data-protection Keychain behavior. The
[data-protection Keychain API](https://developer.apple.com/documentation/security/ksecusedataprotectionkeychain)
uses the latter without iCloud sync. Apple's
[access-group guidance](https://developer.apple.com/documentation/security/sharing-access-to-keychain-items-among-a-collection-of-apps)
ties isolation to the app ID and signed entitlements, and
[Developer Technical Support](https://developer.apple.com/forums/thread/115425)
says this path expects Mac App Store or Developer ID signing with an Apple
Team ID. The current local self-signed certificate has no verified Team ID.
These are platform claims, not proof that a new Aster build would work.

## Smallest next experiment

1. Confirm the current signed app's *non-secret* entitlements and signing
   metadata (done for version 13). Do not read passwords, private keys or
   session values. Whether Jason has another suitable signing identity is
   **UNKNOWN** and need not be queried until the synthetic path warrants it.
2. In an isolated test app, use a random disposable string, a unique service
   name and `kSecUseDataProtectionKeychain=true`. Record add/read/delete status
   codes only. Never use the real Companion service or account name.
3. If the synthetic write succeeds, update that test app with a different
   binary signed by the same identity; measure whether it reads without a
   prompt. If it fails with missing entitlement, record that result and stop.
4. If Developer ID is available and Jason wants to use it, repeat the
   synthetic two-version test with correct app ID and validated entitlement
   before considering a real login migration.
5. A real migration requires a separate gate: verified old and new session
   behavior, refresh-token-aware recovery, no cloud credential disclosure,
   an explicit rollback, and a successful synthetic update test. It must not
   be inferred from passing unit tests alone.

**Acceptance:** two distinct signed synthetic builds read the same isolated
item without a prompt; the second build survives restart; denial of an
unrelated app is verified; item cleanup is confirmed. Anything less leaves the
current release model unchanged.

**Stop conditions:** unexpected access to the real Companion item, an
unanticipated Mac security prompt, a request to broaden ACLs, failed cleanup,
or an entitlement path requiring an unplanned Apple account or payment.

## Programme implication

AI-PAM remains the authority for infrastructure credentials and scoped worker
grants. Companion's OIDC login is a client-session custody problem. Keeping
those boundaries distinct prevents a UI convenience fix from giving the
assistant broader infrastructure authority. The result also supplies a useful
Learning Plane example: the hypothesis (stable signer plus fresh item prevents
update prompts) was preregistered, tested, rejected, and retained with a
working fallback. A new architecture is justified only by a measured outcome,
not by the attractiveness of a broker design.
