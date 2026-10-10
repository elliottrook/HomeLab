# D3 manual uncertain-result handling — offline candidate

**Status:** built and tested locally on 2026-10-10; not installed or enabled.

If the one-shot native bridge returns no confirmed completed answer, the manual
Companion view previously retained the request ID but left the user with a
generic uncertain message until the view was reopened. The candidate now runs
the same recorded-status preflight used on reopen. It can offer recovery of an
already completed turn or reconciliation of an already recorded turn without
submitting a new question. If the journal cannot prove either path, the ID
remains blocked and the view says so. There is no automatic retry or clearance.

`swift test` passed 55 Companion tests with a temporary scratch/cache path. A
normal sandboxed invocation failed before compilation because SwiftPM's nested
`sandbox-exec` could not apply under the current tool sandbox; rerunning with
SwiftPM's `--disable-sandbox` and temporary build directories succeeded. This
is compile and offline regression evidence only. It does not establish live
Keychain behavior, provider availability, routine handoff reliability or D3
release readiness. Signed version 15 remains installed in ordinary mode with
the manual send control hidden; no new Codex question was sent.
