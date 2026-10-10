# Aster subscription backed Codex delegation

Adopted by Jason on 2026-10-06 as the next Stream A priority within Aster Adaptive
Computing. This amendment supersedes further local general-sysadmin qualification
and the proposed structured-verification tuning cycle. It does not retire Qwen,
change existing infrastructure, authorize general administrator access or approve
a Git push.

## Decision and rationale

Aster owns the familiar voice/chat experience. Deterministic skills handle known
operations; local models handle separately qualified language tasks; the Codex
agent handles unfamiliar investigation and consequential engineering.
Delegate to the agent and its tool/approval workflow rather than merely placing a
stronger model behind the old Aster loop.

Jason supplies goals and business/risk decisions, not expert technical review.
Checks, evidence and recovery must establish technical correctness without
expecting him to detect subtle engineering errors.

The fresh Qwen evaluation found diagnostic meaning correct in 20/20 cases per
mode but complete correctness only 6/20 off and 4/20 compact. Compact reasoning
took roughly twice as long. These bounded simulations do not establish a permanent
local-model ceiling or B60 inadequacy. They also do not justify further general
sysadmin tuning as the default investment. The [evaluation decision](evidence/SA3-fresh-evaluation-result-2026-10-06.md)
remains unchanged evidence.

The Git record shows broader engineering work: collision diagnosis and isolation
checks, ARR authentication repairs, media-code repairs, backup restoration and
storage migration. These are historical records, not a controlled model comparison.
Codex remains fallible. Preserve controls rather than transferring unquestioned
trust to another engine.

## Integration choice and verified limits

Official [Codex authentication](https://learn.chatgpt.com/docs/auth) distinguishes
ChatGPT subscription sign-in from API-key billing. Local CLI inspection reported
ChatGPT login and codex-cli 0.158.0-alpha.2.1. The metadata-only adapter successfully
completed initialize, account/read and model/list: ChatGPT authentication and six
catalogue entries. Successful inference and usable subscription capacity through
the new adapter were initially unproven. The subsequently approved
[D2 Orion pilot](evidence/D2-subscription-result-2026-10-06.md) completed one real
ChatGPT-authenticated turn and recovered the identical answer through a fresh
connection. This demonstrates bounded connectivity, not general capacity or
production readiness.

[Codex App Server](https://learn.chatgpt.com/docs/app-server) documents embedding
authentication, conversation, approval and streamed events. Its command/transport
has experimental status; pin and test the installed protocol. Prefer local stdio
and a separate bridge process, not browser automation or a public agent endpoint.

[ChatGPT plan usage](https://developers.openai.com/siwc/token-sharing-open-source)
also documents eligible OSS/local-app subscription requests, with
[app-server support](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server).
This distinct preview flow has eligibility and feature constraints. Do not assume
that a generic API key uses the subscription, or copy Hermes's credential import.
First evaluate the official installed Codex integration. If separate app
registration is necessary, record that requirement and use its supported consent
flow rather than impersonating another client.

[Hermes providers](https://hermes-agent.nousresearch.com/docs/integrations/providers)
demonstrate provider switching and Codex-model OAuth; this is not evidence that
Hermes runs the complete Codex agent. No Hermes dependency is required here.

## Stable boundaries

- Local routing uses an allowlisted intent/capability table first. Unknown requests
  clarify. Sysadmin escalation does not depend on Qwen recognizing its own limits.
- Privacy authorization precedes cloud dispatch. Explicit local-only requests stay
  local or return unavailable. Public/synthetic fixtures come first; real incident
  data requires an explicit approved scope and redaction.
- Subscription-only policy: no API-key fallback, paid-provider fallback, automatic
  credit purchase or automatic quota reset. Quota/auth failures are typed states.
- Aster retains its persona and speaks the returned final answer faithfully; no
  weaker-model rewriting of caveats or approvals. Hidden reasoning is not retained.
- Route selection grants no tools, credentials, network reachability or write
  authority. Codex sandbox and deterministic broker controls remain authoritative.
- Approval must bind authenticated Jason, exact action/targets, expiry and job
  identity. Voice alone cannot approve high-impact actions. No approval bypass.
- Aster job ID maps to a dedicated Codex thread/turn, not arbitrary existing chats.
  Context and permitted tools must be explicitly configured; this chat's context,
  plugins and permissions do not automatically transfer.
- Store minimal durable job state, not secrets or hidden reasoning. Mark an
  interrupted dispatch unknown until reconciled; never resubmit it automatically.
  Completion requires the terminal success event and usable final output.
- Cancellation is a request until acknowledged; disconnection is not cancellation.
  Verify running work before retry. Expiry cannot be treated as proof tools stopped.
- Household deterministic functions survive GPU, Codex, Internet and bridge loss.
  Complex work queues or reports unavailable; it never falls back to unqualified
  autonomous local repair.

## Delivery gates

Canonical progress lives in the programme's D0–D4 table.

| Phase | Goal and dependency | Acceptance and measurement | Risk and rollback |
|---|---|---|---|
| D0 | Record decision; inspect installed protocol and auth, no inference | Source citations, local CLI/version, protocol compatibility evidence; no secrets logged | Experimental interface; remove candidate without affecting live Aster |
| D1 | Offline routing and lifecycle candidate, after D0 | Tests for privacy/auth denial, duplicate dispatch, unrelated events, failure, cancellation, quota and faithful output | A pure contract is not OS isolation; no runtime authority added |
| D2 | One explicit synthetic read-only round trip via subscription, after D1 | Aster job → Codex → terminal answer; record auth mode, selected model, elapsed time and usage; no paid fallback | Concrete run manifest fixes prompt, allowed tools, host, limits and recovery; disconnected outcome reconciled before retry |
| D3 | Authenticated Companion pilot with durable status, after D2 | Follow-up context, reconnect, cancellation, busy/limit/unavailable handling and completion notification; local fast path unaffected | Limited egress and isolated working area; disable bridge feature flag to roll back |
| D4 | Scoped live investigation, then separately guarded changes | Compare full workflow against actual runbook tasks; independent postchecks; user approval for defined changes | No generic SSH/root delegation; retain checkpoints and existing manual Codex path |

No new hardware or major dependency is needed for D0/D1. Prefer the existing Mac
for the first bridge because Codex is installed there; its sleep/offline state is
an explicit availability dependency. An always-on deployment is a later placement
decision, not permission to copy personal credentials into a container.

### D3 native-placement review — 2026-10-08

The bounded gateway/worker transport completed one native request and one
original-answer recovery, then was closed. Its worker identity is inactive
between trials; the current broker does not provide per-session activation or
Mac process startup. Gateway session routes by themselves would preserve the
operator timing race. For the *native Mac app*, evaluate a one-shot local Codex
bridge before adopting a standing distributed workflow. The D2 local stdio
adapter is already proven for one fictional turn; an offline coordinator now
passes duplicate-dispatch and uncertainty checks, without a model call. A
signed, uninstalled build 9 bundles the one-shot bridge, and fake-process tests
cover private stdin, duplicate refusal, timeout and bounded output. The native
App Server connection has passed metadata-only preflight; a live native turn
and app replacement remain unapproved. The gateway remains a
candidate for future voice/remote ingress; no authority transfers to either
path. The [D3 comparison](evidence/D3-session-and-answer-recovery-design-2026-10-08.md)
and [one-question native gate](evidence/D3-native-local-bridge-gate-2026-10-08.md)
record the current placement decision and proposed test.

## Current authorization and next action

### Standing access review — 2026-10-09

Jason requested an access-until-revoked approach to stop repeated prompts while
Stream A is built. The [standing-access design](evidence/D3-standing-access-design-2026-10-09.md)
separates existing Stream A project authority, AI-PAM capability grants, native
Keychain trust, ChatGPT disclosure consent and Codex platform approvals. Its
first implementation gate identified the native Companion saved-login dialog.
Stable local signing and migration to a new Companion-only Keychain item made
version 13 restart without a prompt, but a signed version 14 update prompted
again. Version 13 is the current working app; the no-repeat-prompt update gate
failed. The [custody decision](evidence/D3-native-session-custody-decision-2026-10-09.md)
keeps login custody separate from AI-PAM, rejects broader Keychain access, and
sets a disposable-credential test before any other live migration. Routine
in-scope local/read-only work should proceed without new conversational
approval.

Jason directed recording this logic, retooling the project and continuing Stream A.
Proceed with local documents/code/tests and read-only integration preflight.
Connected pilots retain concrete privacy, tool and deployment gates under the
canonical project. Prepare the complete bounded D2 manifest before asking for any
missing authorization; do not ask him to approve routine local implementation.
Existing per-push confirmation still applies.
