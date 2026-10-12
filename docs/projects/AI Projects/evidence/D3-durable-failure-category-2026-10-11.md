# D3 durable failure-category candidate — 2026-10-11

**Status: offline candidate only.** The installed Companion and its bundled bridge are unchanged; routine Ask Codex remains hidden and on HOLD.

## Problem and bounded change

The local Codex session already maps a failed turn's provider error code to one of `subscription_limit`, `rate_limit`, `session_budget`, `authentication`, `provider_unavailable` or `other`. Previously that category existed only in process memory. After a restart the owner-bound status could confirm `failed` but could not distinguish a quota/rate failure from a general failure.

The candidate adds one nullable, allowlisted `failure_class` field to the private dispatch journal. A terminal failed state and its category are saved in one transaction before a result is exposed. Existing journals migrate in place without releasing claims or rewriting request IDs. Read-only status emits the category only for the exact owner's confirmed failed job; older journals and missing categories remain generic. The native manual view maps known categories to plain language, always says nothing will be retried automatically, and requires the same bound terminal record before allowing acknowledgement. Raw provider error text, prompts, answers and credentials are not persisted by this change.

## Evidence and limits

- 305 delegation tests passed in the existing local dependency environment, including owner binding, legacy schema migration, invalid category rejection and restart durability. A system-Python full run lacked `httpx`/`pydantic`; no dependencies were installed for this candidate.
- 57 native Companion tests passed, including a new category/unknown-value display test. SwiftPM's first sandboxed attempt could not initialize its own sandbox; the local test passed when rerun with permitted filesystem access.
- No Codex turn, live quota event, credential read, model call, app install, service restart or remote write occurred.

This demonstrates deterministic handling of synthetic error codes, **not** that the current Codex provider emits those exact codes for every real limit or that the UI has survived a real failed turn. The installed version-15 bridge manifest pins its old source; a later signed release must repin, rebuild, verify the private journal migration and run one separately reviewed ordinary-use check. Do not use this candidate to waive the natural session-refresh gate or to enable connected tools, automatic routing or retries.
