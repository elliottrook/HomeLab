# D2 subscription round trip — bounded connectivity passed

Jason explicitly approved the Orion pilot on 2026-10-06. Executed once from
commit `9222fce` with prepared manifest fingerprint
`6a8a916165d50bb35f779face26c5705dc147961bdf42f14e88297c827679d12`.

## Verified current state

The restricted adapter completed a real turn using ChatGPT authentication,
native OpenAI provider, `gpt-5.6-luna` and medium reasoning. Matching terminal
status was `completed`; a usable final answer arrived in **5.509 seconds**,
measured from thread/turn processing through completion, excluding preflight.

The answer distinguished the past HTTP 503 and later HTTP 200 from proof of
continuing health. It identified missing evidence and proposed checks, without
claiming real inspection or repair. No API-key fallback, model substitution or
adapter retry occurred. This verifies the configured ChatGPT-authenticated path,
not a billing-invoice audit.

A fresh restricted process read only the dedicated pilot thread and recovered
the identical answer without new inference. The thread contained one turn and
only `userMessage` and `agentMessage` items, with no recorded tool activity.
Recovered answer SHA-256:
`5cde10775ae7492e073cd32932b11a47f349fa72b9e2f947312ae39643ff6959`.

The fictional [full result](D2-Orion-result-2026-10-06.json) is retained in Git.
Thread/turn identifiers, manifest, dispatch database and recovery receipt remain
under `/private/tmp/aster-d2-orion-20261006`; Codex retains its dedicated thread
normally. Temporary-directory state is not a production recovery store or backup.
Owned child processes were closed. No production deployment or Git push occurred.

## Implication and limits

The Aster-adapter → Codex agent → Aster-adapter response path is feasible through
existing ChatGPT sign-in, without Hermes. Live Aster UI/voice integration is not
yet implemented. This one fictional fixture does not qualify a sysadmin engine,
establish comparative competence or measure broad reliability. The installed
default tested connectivity; it is not selected as the eventual sysadmin model.

The bounded connectivity and completed-turn recovery gates passed. Token usage
is **UNKNOWN**, not zero. Usage collection and live cancellation remain untested;
the entire original D2 acceptance is therefore not complete. Further cloud turns
need a bounded scope; the approved one-turn request has been consumed.

Next Stream A work is local usage-event handling and authenticated Companion
job/status fixtures, keeping the integration disabled pending its deployment
gate. Prepare cancellation, limit and outage acceptance cases before another
connected canary. Do not ask Qwen to rewrite or adjudicate Codex's returned answer.
No general sysadmin authority follows from this result.
