# F2 October 24 exact-cycle activation review — 2026-10-23

## Reviewed candidate

Stream A independently reviewed the platform-owned inactive candidate at full
commit `054ada0698d4b35cf99217b1d6fe7bac97ff1cb3`. The commit contains only the
October 24 activation card and its two exact-date timer candidates.

| Candidate | Independently recomputed SHA-256 |
|---|---|
| `f2-preflight-prepare-20261024.timer` | `0b13bcd78b6ec1623f35942bcbc9f7ae63a03433223058eac25ce0920df53376` |
| `f2-preflight-final-20261024.timer` | `81c7cb6a57c95f946d85348f856852db9839f469acd76ad21a3c15511a666860` |

Both hashes match the card. The timer text fixes `OnCalendar` at 01:15 and
01:20 America/Vancouver on October 24, uses one-second accuracy, disables
random delay, and sets `Persistent=no`.

## Boundary review

The card is a fresh date-specific candidate rather than a shifted October 23
card. It preserves October 19–23 terminal evidence, limits absence checks to
the new cycle state plus live lease/lock and trusted receipt, and names the
Stream A 01:42 observation-only heartbeat as cleanup owner. Cleanup cannot
invoke, retry, reschedule, acquire a lease or advance F3.

The candidate is suitable for an activation decision. It remains inactive.
Before activation, the installed hashes/custody and live absence gates must be
re-read and both timers must pass target-side systemd unit/calendar validation.

## Decision boundary

This review authorizes nothing. Installing or enabling the two one-shot timers
is a distinct host change requiring explicit approval. F3/F4 remain separate
future gates even if F2 succeeds.
