# M1 Companion read-only passkey session candidate — 2026-10-25

> Result: **OFFLINE CANDIDATE PASS; NOT INSTALLED**

## Problem corrected

The installed Companion can start fresh authentication only as the prelude to
an approval or management mutation. Merely opening AI-PAM Management performs
four read-only fetches and does not invoke the passkey flow. The approved M1
claim-transport check therefore cannot be completed safely from the installed
UI without approaching an effect-bearing control.

## Candidate behavior

The candidate adds one content-free `AIPAMSession` response model, one client
GET for `/v1/companion/approvals/session`, and an **Approval session** panel in
AI-PAM Management. Its **Verify with passkey** button performs the existing
mandatory fresh login and, on success, calls only that session GET. It displays
only three booleans: authorized, passkey verified and fresh.

It does not create or consume a request, call a model, or invoke a management
action. Unknown response fields are discarded by decoding; the new unit test
proves an injected subject field is not represented by the model.

| File | SHA-256 |
| --- | --- |
| `AIPAMModels.swift` | `dce688c18e96a94c907612b3068326ffda4b9673c7ef2608c7d87cc0f121dd07` |
| `AsterClient.swift` | `93f15175601453b4bc31ceddbacd8244f3030c80e46ad11f3de6219073b3936e` |
| `AIPAMView.swift` | `359c51a1194fd7f0892cbe582efdc6993db6f29d8676b338b18544b8695d9461` |
| `AIPAMModelsTests.swift` | `6f13434feccbb02077030d62bd0f293aa93e67ad2b7bf15de02d1346a3e1602d` |

The complete native suite passes **61/61** on the Mac. Installation, signing,
launch and a real passkey ceremony remain a separate live change. Preserve the
current signed app and rollback copy; do not exercise Red approval or any
management mutation during that check.
