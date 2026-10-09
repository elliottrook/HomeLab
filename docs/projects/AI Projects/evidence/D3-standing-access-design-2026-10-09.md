# D3 standing access: reduce repeated prompts without broad authority

Status: local design and uninstalled broker candidate, 2026-10-09. No production permission,
Keychain ACL, Codex sandbox, or remote repository setting was changed by this
record. Jason requested access that remains valid until revoked because prompts
every minute or two are impeding Stream A.

## Verified sources of prompts and limits

| Boundary | Current evidence | Standing access mechanism | Limit |
|---|---|---|---|
| Project authority | `docs/Project-Creation-Standard.md` and `AGENTS.md` already authorize routine local implementation and read-only LAN work for approved Stream A. | Treat that scope as standing; do not ask again for each routine check or local edit. | Remote Git writes still need immediate confirmation under `AGENTS.md`; platform prompts still apply. |
| AI-PAM | `ops/credential-broker/broker_core.py` persists an agent-capability grant; Green requests are approved without a human prompt while Yellow/Red are request-bound. Agent suspension, service disable and global disable stop new issuance. | Grant only named Green capabilities to the specific registered agent, keep an audit trail and an operator-visible revoke path. | AI-PAM governs brokered HomeLab capabilities, not macOS Keychain, ChatGPT disclosure or the Codex sandbox. A single-capability revoke exists only as a tested local candidate; it has no Companion UI or live deployment. Existing grant creation does not yet audit its human issuer. |
| Native Companion pilot | `LocalCodexEvaluationView.swift` requires review and consent for each of 12 fixed fictional, no-tools questions. This is a deliberately narrow local pilot gate. | Replace repeated consent with a visible, revocable consent for the exact finite fictional batch, and record its corpus hash, scope and version. Preserve review/result capture and stop-on-uncertain behavior. | Never infer standing consent for real HomeLab data, tools, unrestricted prompts or paid API use. This pilot is hidden by default and is not a production Codex route. |
| macOS Keychain | Installed `/Applications/AsterCompanion.app` is ad-hoc signed; `build-app.sh` re-signs with `codesign --sign -`. This Mac currently reports no valid code-signing identity. The separate worker uses `/usr/bin/security` to read a Keychain item. | For the Companion's own session item, use Keychain Access to trust only the exact app; establish a stable signing identity before expecting that trust to survive rebuilds. Replace the generic worker CLI read with a dedicated, signed helper or brokered short-lived credential before permanent worker access. | Do not select `Allow all applications` or permanently trust the generic `/usr/bin/security` tool for a worker secret. AI-PAM cannot set macOS Keychain ACLs. The exact recurring dialog is not yet identified. |
| Codex platform | The repository uses a workspace-write sandbox. OpenAI documents approval policies and narrow permission profiles; this app session may still enforce its own approval review. | Prefer a narrow per-chat approval or permission profile for routine operations, where the host permits it. Work in writable roots and use direct read-only LAN transport to avoid avoidable escalations. | Repository instructions and AI-PAM cannot waive platform-enforced approvals. Do not switch to unrestricted filesystem/network access merely to remove prompts. |

## Proposed standing grant contract

Represent a grant as **issuer, subject, environment, named capabilities,
target/data boundaries, allowed change classes, maximum duration or until-revoked
condition, revocation handle, and audit record**. “Until revoked” applies to
authorization to request work within that scope; each tool execution still
checks current policy, identity, service health and global disable. Revocation
must deny future requests immediately, and unconsumed requests must be
invalidated. Execution already started needs its executor-specific stop or
postcheck; broker revocation alone cannot undo an action. The operator must see active
grants and be able to revoke one capability, an agent, or all AI access.

For current D3 work, the smallest useful standing scope is fixed synthetic,
no-tools Codex evaluation through the existing ChatGPT subscription; routine
read-only HomeLab validation; and local code/doc/test/build work in the
authorized workspace. It excludes credential display or export, real personal
context sent to cloud, unsupervised production changes, changing security
policy, unrestricted shell delegation, and remote Git writes. A later live
scope needs its own named targets, change classes, postchecks and rollback.

## Implementation and acceptance sequence

1. Identify which dialog is actually recurring from its title and buttons,
   without collecting passwords or secret values. Count the prompt rate and
   origin for 15 minutes. Address that boundary first.
2. Remove unnecessary conversational re-approval for already authorized Stream
   A local/read-only work. For the fixed fictional pilot, add a single explicit
   batch-consent/revoke control. Confirm no question outside the pinned corpus
   can be sent, no tools are granted and uncertain requests are not retried.
3. Review and deploy the local fine-grained AI-PAM capability-revoke candidate
   through the authenticated management surface. Its tests show immediate denial
   and invalidation of outstanding requests; 86 broker tests pass. Add an
   operator-visible UI and active-grant/last-use view without secrets before
   treating it as the normal revocation path.
4. Resolve native app signing and Keychain identity before trusting persistent
   access to the Companion session item. Do not grant a general CLI access to
   the worker credential. Measure prompt count across two app rebuilds/restarts.
5. Evaluate a narrow Codex permission profile or chat-scoped approvals for the
   remaining platform prompts. Treat any mandatory host approval as mandatory.

Success means no repeat prompt for the same low-risk, already-authorized
operation during a normal session, while a denied/revoked capability is blocked
and audited. Deliberately sensitive or out-of-scope actions should still prompt
or fail closed. Stop if the prompt source differs from the hypothesized one.

## Sources

- Repository: `AGENTS.md`, `docs/Project-Creation-Standard.md`,
  `docs/reference/AI-PAM-Operational-Reference.md`,
  `ops/credential-broker/broker_core.py`,
  `apps/AsterCompanion/build-app.sh`, and
  `apps/AsterCompanion/Sources/AsterCompanion/LocalCodexEvaluationView.swift`.
- Apple, [Allow apps to access your keychain](https://support.apple.com/en-gb/guide/mac-help/kychn002/26/mac/26).
- OpenAI, [Codex permissions](https://learn.chatgpt.com/docs/permissions) and
  [configuration basics](https://learn.chatgpt.com/docs/config-file/config-basic).
