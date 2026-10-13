# D3 manual Codex and current native Companion integration gate

**Status: Jason approved installation of the stable-signed composite on the
Mac mini. Signed-in UI, read-only passkey/OpenBao status, AI-PAM panel and one
ordinary Aster answer pass; D3 routine manual-Codex release remains held.**
The [v16 refresh result](D3-v16-natural-refresh-and-current-bundle-drift-2026-10-12.md)
is valid historical evidence, but before composite installation the installed
`/Applications/AsterCompanion.app` was a different signed 0.2.2/build-4 binary.
Its executable hash was
`7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`.
The current main checkout's `Info.plist` names the same version/build and its
runbook calls this an AI-PAM parity candidate. That is source/repository
context, not proof that its installed binary exactly matches the checkout.

**Read-only rollback inventory, 2026-10-12:** the current app still verifies
under strict deep code-signature checking and retains the executable hash
above. The runbook names
`/Applications/AsterCompanion.pre-optional-callback-fix-20261012.app` as the
preceding bundle. That bundle also verifies under strict deep code-signature
checking, reports version 0.2.2/build 4, and has executable SHA-256
`1b01b92885bfd9485d0e70617b502cecfecc2e30c49321425f08d444966f588d`.
It is **not yet an accepted functional rollback**: the runbook documents that
this preceding build stalled normal sign-in because it skipped the
authorization-code exchange when no optional completion handler was supplied.
No bundle was launched, replaced or restored during that inventory. The later
verified copy of the then-working signed app supersedes this faulty predecessor
as the local rollback candidate; functional restore remains untested.

The app owner subsequently confirmed published source `f26e3c48` as the
current app baseline, with no further unpublished Companion edits in that
line. The owner reports no separately accepted certificate-signed predecessor
rollback. Stream A prepared [local composite candidate
`eb69280`](D3-composite-offline-candidate-2026-10-12.md) from that baseline;
offline build and tests pass while current OpenBao/auth source stays unchanged.
The owner reviewed its source and found no direct passkey/OpenBao/Keychain
conflict, without claiming live acceptance. A stable-signed release bundle
was built offline and a byte-verified, signed copy of the currently working
app was retained at
`/Users/jelliott/lab/private-backups/aster-companion/pre-composite-20261012.app`.
The composite was subsequently installed on the Mac mini; the prior app is
also retained at `/Applications/AsterCompanion.pre-stream-a-20261012.app`.
The local rollback has not undergone a restore-and-launch drill. See the
[installation and live observations](D3-composite-offline-candidate-2026-10-12.md).
The browser
Companion's OpenBao UI and service are unchanged by this Mac-only candidate;
browser-side manual Codex is outside its scope.

## Source divergence found read-only

Stream A's worktree contains eight native source files absent from the main
checkout, including the manual Codex view, its bridge/pending records,
evaluation views and delegation UI. A read-only search of the main native
sources found no manual Codex view or `--aster-local-codex-manual` flag. Both
lines touch `AsterClient.swift`, `AsterCompanionApp.swift`, `AuthManager.swift`,
`ContentView.swift`, the native build script and auth tests. The main checkout
has uncommitted edits in these shared files. This is a real source-integration
boundary: a successful v16 pilot cannot silently graduate into a different
installed app, and reverting the current app would overwrite another lane's
work. Whether the current binary contains any compiled Codex pilot code is
**UNKNOWN**; the source comparison alone cannot prove binary absence.

The shared-file differences are substantive, not just conflicting line
numbers. Stream A's `AuthManager` uses a v3 Keychain item with a migration
path from v2 and emits bounded refresh observations; the current main source
uses the v2 item and has explicit callback handling, a sign-in timeout and
the October 12 no-completion fix. The current main app delegate forwards
`aster-companion://` callbacks; Stream A's older app entry point does not.
The current main client/view add OpenBao recovery functions and a panel,
while Stream A's client/view add manual Codex requests and a hidden delegation
panel. The Stream A build script packages `LocalCodexBridge` and re-signs the
completed bundle; the current main script has no bridge packaging. The two
source lines also differ in speech delivery (`synthesizeStream` versus
`synthesize`), which needs a separate normal-chat regression check. These are
read-only source observations, not evidence about which features are compiled
into the installed binary.

## Smallest safe integration sequence

This was the pre-install plan. Steps 1–3 have source/build evidence; step 4
is partially verified by the signed-in Mac UI, OpenBao/AI-PAM panels and one
ordinary response. The exact composite has not yet shown natural refresh or
flagged manual-Codex behavior. Step 5 remains **HOLD**.

1. The current app owner identifies the exact source commit plus any pending
   local changes, installed-binary hash, signing identity, current AI-PAM
   acceptance state and a **functional** signed rollback bundle. The known
   pre-sign-in-fix bundle is an integrity checkpoint, not a proven rollback.
   Do not treat the dirty main checkout as a reproducible release.
2. Reconcile the eight Stream A files and six shared-file touchpoints on an
   isolated branch from that pinned app line. Keep manual Codex hidden by
   default, require per-question cloud consent and preserve zero tool grants.
   Keep the current sign-in/callback/OpenBao behavior and verify a migration
   path for any Keychain item change; do not copy the older v16 auth file over
   the repair. Preserve the ordinary speech path. Resolve shared-file changes
   deliberately, not by choosing one whole file version.
3. Run the complete native auth, AI-PAM, ordinary assistant and D3 offline
   suites. Check stable code signing, bundle identity, exact bridge manifest,
   and a preserved current-app rollback. A build/test pass does not authorize
   installation.
4. Install one reviewed composite candidate only after the app owner and
   Stream A agree on the release artifact and rollback. Confirm ordinary
   sign-in, read-only AI-PAM access and the hidden manual surface. Use the
   existing completed Codex journal for read-only recovery checks; do not send
   another model question merely to prove feature presence. Observe any
   natural refresh and Keychain prompts on the composite build separately.
5. Make an explicit **release / hold** decision for the limited manual
   handoff. Connected tools, automatic routing and general sysadmin remain
   separate gates regardless of the result.

**Stop conditions:** unpinned current build, unclear ownership of active
native edits, changed signing requirement, recurring Keychain prompts,
broken ordinary assistant/AI-PAM operation, uncertain Codex turn, or any
attempt to reuse the v16 refresh result as qualification of the composite
binary. Preserve both app lines and their historical evidence until the
integration is reviewable.
