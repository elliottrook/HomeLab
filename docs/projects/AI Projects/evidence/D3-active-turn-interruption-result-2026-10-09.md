# D3 one-attempt native process-interruption result — 2026-10-09

**Result: narrow recovery observation passed; D3 routine release remains on hold.** Jason approved the [one-attempt proposal](D3-active-turn-interruption-proposal-2026-10-09.md), reviewed its exact fictional Nova question in native Aster Companion, checked per-request ChatGPT consent, and clicked Send once. No further live question is planned for this gate.

## Boundary and preflight

- Installed version 15 and its version-13 rollback copy passed strict signature checks and matched their recorded executable SHA-256 values, respectively `f83ed9fe74c33222beb39a73519644c5b6fd796e991e6f0f6c598cca950936b1` and `c3b016f41045a636c0503af2b7448a5f255f54dcd859a61f6dbb5fc84221394c`.
- The private journal held 14 completed rows. The prior Vega answer was recovered read-only, then its completed-only guard was acknowledged through the native UI; the pending record disappeared and the journal remained at 14 rows. No shell deletion cleared it.
- One flagged Companion process was verified at exact PID 85483, with the installed executable hash pinned by the watcher. The app's own preflight enabled the review screen. A separate sandboxed shell metadata-preflight returned `Local bridge incomplete; reconcile before retry` without inference; it was not used to authorize a send or represented as a successful check. The native preflight and exact manifest guard controlled the send.
- The one-shot watcher had five passing offline tests, observed only the owner-only request record and content-free journal, and was armed for this one PID with a 45-second limit. It could not start or repeat a Codex turn.

## Observation

The watcher reported `signalled_on_observed_running` for request `request-bc8935e1-b3e3-4ef8-adc2-1cb69216f646`: it observed journal state `running` with a recorded turn ID, then sent SIGTERM to PID 85483. That process was absent on the subsequent check. The journal then held 15 completed rows and no other states; the new ID occupied one row with one recorded turn ID. Its private pending record remained in place.

The same signed app was reopened once in manual mode. Its UI found the saved ID, said the recorded turn had completed, and offered **Recover original answer**. Clicking that action displayed the original Nova answer with a recovery message. The journal stayed at 15 completed rows. No retry, replacement ID, second Send click, tool item, approval request or infrastructure action was observed. The answer text was not copied into Git.

The manual view was closed, the flagged process quit, and the app reopened once in ordinary unflagged mode. One unflagged process, signed-in Aster screen and AI-PAM's **No pending approvals** state were observed. No Keychain prompt was visible on this restart. The saved request ID was deliberately retained, so a later explicit manual recovery remains possible without resubmission.

## What this establishes and what it does not

This is evidence that the native path can survive termination of its UI process after a running turn has a durable ID and can show that same completed answer after restart. It does not prove that SIGTERM preceded model completion: a completion race between the watcher's journal read and signal cannot be excluded. The journal's one row/turn ID and read-only recovery support no duplicate in this attempt, but do not independently establish a provider-side reliability rate. This did not test a hard crash, network loss, natural token refresh, sustained Keychain behavior, tool use, sysadmin competence or automatic routing.

**Decision:** stop additional live-question trials for this D3 evidence gate. Next do an independent review of the existing finite answers without fresh inference, passively observe ordinary Companion sign-in/Keychain behavior through natural use, and make an explicit limited-release or hold decision. Preserve version 13 as rollback. Keep ordinary Codex intake, worker authority, gateway intake, automatic routing and sysadmin delegation closed pending their own gates.
