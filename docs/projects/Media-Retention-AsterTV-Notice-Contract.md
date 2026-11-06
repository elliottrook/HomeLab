# AsterTV Archive notice and Keep contract

> Status: Local design candidate; no AsterTV v3 implementation or deployment authorized by this document
>
> Parent: [Media retention and recall](Media-Retention-and-Recall.md)

Jason selected **AsterTV** as the household notice route on 2026-11-06. This
contract prepares the Stream A retention backend. The client is governed by
the separate [AsterTV v3 Stream M project](AsterTV-v3.md), whose implementation
and deployment require its own bounded approvals.

## Household flow

When raw `Media` pool use reaches 60%, the server may propose otherwise safe
Archive movies or whole seasons for removal. An AsterTV Archive notice shows
the title, scope, earliest removal time and a **Keep** action. A household
member can choose Keep during the three full days. Any household member's Keep
protects the whole movie or season, including later file upgrades. Watched,
partly watched and favorite signals still protect it independently. If no safe
candidate can reclaim space, AsterTV must show capacity pressure without
promising that something will be removed. The operator receives the Doctor
alert at 60/62% under the existing HomeLab route.

## Server boundary

- AsterTV reads an authenticated, profile-scoped notice feed. A GET is
  side-effect free and returns only provider identity, display metadata,
  movie/season scope, notice state and UTC deadline. No ARR key, file path,
  private watch history, user list or snapshot names reach the client.
- A separate authenticated **POST Keep** carries the provider/scope identity
  and an idempotency key. The server resolves the signed-in household profile,
  rechecks identity and records a durable title-level Keep decision. No client
  can directly change ARR monitoring or delete media.
- The retention server first records a **proposal** bound to the exact ARR
  file-set digest. AsterTV can fetch and display that proposal, but it has no
  removal deadline yet. The server records a visibility reference only after
  the accepted household client path confirms the notice is available. That
  confirmation starts the three-day clock. A replacement file invalidates
  the old proposal or confirmation; a controller dry run starts no clock.
- Immediately before any eventual ARR deletion, the controller rechecks the
  notice deadline and current-file binding, all seven users, retained playback
  logs, Keep decisions, active playback/download, ARR/Jellyfin identity,
  subtitles, recovery and actual snapshot-free reclaim. A missing feed,
  authentication failure or stale status holds the candidate.
- A bounded, authenticated operator route can revoke a notice or inspect its
  non-secret state. Cancelled/expired notices cannot be replayed as a fresh
  authorization. Audit records contain action IDs and timestamps; household
  identity and title-level records stay source-local.

## Acceptance before any live notice

1. Complete the lifecycle ARR/Jellyfin identity contract and source-local
   candidate adapter. The current path audit alone certifies no deletion.
2. Under AsterTV v3 Stream M, approve a local client candidate, then verify
   remote navigation, account separation, notice visibility and Keep on the
   lab client. Test offline and stale-feed behavior. Production Family
   promotion remains a separate gate.
3. Prove server-side idempotency and a synthetic Keep race during the last
   second of grace. Confirm a replacement file resets notice eligibility.
4. Run repeated read-only/dry-run controller passes and verify Doctor alerts.
   At today's 41% pool use and full snapshot coverage, there is no live
   notice or deletion candidate.

The eventual recall **Request again** card is a separate explicit action
through Seerr/ARR. Opening a notice or playing a status clip never triggers it.
