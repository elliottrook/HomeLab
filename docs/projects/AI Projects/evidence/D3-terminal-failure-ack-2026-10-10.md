# D3 terminal-failure acknowledgement — offline candidate

**Status:** local source and test candidate; not installed or enabled.

The hidden native manual view previously allowed a new question only after a
completed answer was acknowledged. A durable `failed` or `interrupted` turn
therefore left its request ID blocking the view indefinitely, even though the
turn had a final recorded outcome. That was safe against duplicate dispatch
but unsuitable for normal use.

The candidate first reads the private, owner-bound dispatch journal without a
Codex/provider preflight. Only `failed` or `interrupted` with a recorded turn
ID offers an explicit acknowledgement button. Pressing it rechecks that exact
request and terminal state, then removes only the matching local admission
record. A later question still requires a fresh review and cloud-consent step.
`running`, `unknown`, `dispatch_unknown`, a missing turn ID, a mismatched ID,
and journal errors remain blocked. No request is replayed or retried.

Three focused native tests pass, including denial cases for uncertain work;
the modified Companion target builds. This tests local state handling, not a
provider failure, a Keychain session, or a full release. The signed installed
version 15 and its ordinary Aster path are unchanged. Before release, a
separate normal-environment acceptance check must confirm the button's
wording and restart behavior without creating repeated live test questions.
