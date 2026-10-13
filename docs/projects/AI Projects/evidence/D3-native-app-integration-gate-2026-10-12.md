# D3 manual Codex and current native Companion integration gate

**Status: integration candidate required; no app change in this checkpoint.**
The [v16 refresh result](D3-v16-natural-refresh-and-current-bundle-drift-2026-10-12.md)
is valid historical evidence, but the installed `/Applications/AsterCompanion.app`
is now a different signed 0.2.2/build-4 binary. Its executable hash is
`7ba99c035fcd4ac69bb0da72220eec2eeda76c16dc5dcbb35050eb0cefe4076d`.
The current main checkout's `Info.plist` names the same version/build and its
runbook calls this an AI-PAM parity candidate. That is source/repository
context, not proof that its installed binary exactly matches the checkout.

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

## Smallest safe integration sequence

1. The current app owner identifies the exact source commit plus any pending
   local changes, installed-binary hash, signing identity, current AI-PAM
   acceptance state and signed rollback bundle. Do not treat the dirty main
   checkout as a reproducible release.
2. Reconcile the eight Stream A files and six shared-file touchpoints on an
   isolated branch from that pinned app line. Keep manual Codex hidden by
   default, require per-question cloud consent and preserve zero tool grants.
   Do not overwrite AI-PAM's passkey, sign-in, callback, OpenBao or Keychain
   paths. Resolve shared-file changes deliberately, not by choosing one whole
   file version.
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
