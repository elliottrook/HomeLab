# D3 Companion version-16 installation checkpoint — 2026-10-11

**State at this checkpoint: installed and process running; ordinary sign-in, Keychain prompt behavior and natural token refresh remain unverified because the Mac is locked. Routine manual Codex release remains HOLD.** No Codex question, Aster tool or infrastructure action was sent from Companion during this installation.

## Before replacement

The installed version 15 was strictly signed under the established designated requirement `com.elliottrook.aster-companion` and certificate root fingerprint `10b67a3b122fafcdb2bb55124caf327115a4e6fa`; its executable SHA-256 was `f83ed9fe74c33222beb39a73519644c5b6fd796e991e6f0f6c598cca950936b1`. One ordinary Companion process was running. The private Codex journal was inspected **only for aggregate states**: 15 completed rows and none running or uncertain. Its one content-free pending UI record matched a completed row and was preserved; no request ID, prompt, answer or token was printed.

A second copy of the signed v15 bundle was made at `/private/tmp/AsterCompanion.v15-stream-a-rollback-20261011.app` and verified as version 15 with the same executable hash and a valid strict/deep signature. The app-path rollback copy is `/Applications/AsterCompanion.v15-before-v16-20261011.app`. Do not delete either while v16 is under observation.

## Candidate and swap

The version-16 source candidate and bridge tests are recorded in the [offline build gate](D3-native-v16-offline-build-2026-10-11.md). The local bundle was owner-signed with the existing stable identity; no Keychain prompt appeared during that signing command. A staged `/Applications/AsterCompanion.v16-stage-20261011.app` passed strict/deep verification, carried version 16, matched the v15 designated requirement, and had executable SHA-256 `06eab741db94718ac5eb8ae7c270da3b3423467ca40a9fa4e737b84f4236ebff`. The reviewed bundled bridge preflight remained metadata-only and matched its pinned no-tools manifest.

After exact-hash checks, the single v15 process received a graceful `TERM` and was verified absent. The v15 bundle was moved to the app-path rollback name and the staged v16 bundle was moved into `/Applications/AsterCompanion.app`. The app was launched without the manual Codex flag. Independent read-only checks found installed version 16, the expected executable hash, valid strict/deep signature, and one running ordinary-mode process.

## Pending observation and stop rule

The Mac locked before the sign-in screen could be inspected. No `session` category refresh event was found in a bounded content-free log-code query immediately after launch; this is **unknown**, not a failed refresh, because the observer records only an actual refresh branch. Jason has been asked to unlock the Mac. Do not infer that sign-in succeeded, count Keychain prompts as zero, release manual handoff, clear the completed pending record, or trigger a Codex question. Once unlocked, verify ordinary sign-in and any update/launch prompt count. A later normal authenticated read-only request after natural expiry must show `refresh_started` then `refresh_succeeded_persisted`, without repeated Keychain prompts, before the D3 release decision can advance.

If ordinary Companion use fails or Keychain prompts repeat, stop v16, restore the retained signed v15 bundle to the app path, verify its signature/hash, and relaunch normally. Its prior Keychain access after rollback is not guaranteed; use human sign-in if needed, never copy or alter session secrets. Leave all Codex journal rows and the completed pending UI record intact.

## 2026-10-12 ordinary-use observation

Jason reported that unlocking the Mac led to **one** Keychain login prompt and that he selected **Always Allow**. No password or token was requested or inspected. The installed v16 window was then accessible and showed Aster signed in with **Sign out** available. Its ordinary-mode Codex request screen showed only recorded completed requests and explicitly said new Codex requests are closed. The AI-PAM approvals screen loaded with **No pending approvals**. One manual **Refresh** on that existing read-only screen left it usable and did not show a new prompt in the observed app state. No approval, Codex question, tool action or infrastructure mutation was initiated.

A bounded macOS log query emitted only allowlisted `session` event codes, not messages or credentials. It found zero refresh events in the preceding two hours and zero after the read-only refresh. A second ordinary read-only AI-PAM opening around 10:15 Vancouver time still showed **No pending approvals** and the app signed in; a 90-minute fixed-code log query again found zero refresh events. No new Keychain prompt appeared in the observed app state. This is expected if the current access token has not expired; it **does not** prove a natural refresh or persistent Keychain write. The signed v15 rollback remains retained. D3 routine manual release remains **HOLD** until a normal request after natural expiry yields `refresh_started` followed by `refresh_succeeded_persisted`, without repeated Keychain access requests.

Jason subsequently signed out and authenticated again without entering credentials. The native v16 window showed **Sign out** afterward. The existing browser/identity session may explain the credential-free sign-in, but that mechanism was not inspected. A new sign-in is not a token refresh and resets the useful aging window for the passive D3 observation. No credential was read, and routine manual release remains **HOLD**.
