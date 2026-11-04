# AsterTV v3 M0 service-contract inventory

> Status: read-only repository inventory; live endpoint and identity validation
> remains incomplete where noted.

This inventory separates the service that owns each fact from AsterTV's current
read or action boundary. It records no credential value, private media history,
camera image or household state.

| Area | Current authority and boundary | Evidence | V3 gap / next proof |
|---|---|---|---|
| Film, television and music | Jellyfin owns catalogue, person IDs, watched/progress state and playback media. AsterTV consumes the signed-in user's visible library; trailers are read from the exact library item and handed only to the official YouTube add-on after strict route validation. | `docs/projects/AsterTV-v3.md`; `services/kodi/astertv-v3/jellyfin_trailer_route.py`; low-spec authenticated catalogue/range-read evidence | Define per-profile Jellyfin mapping in M2; prove user-scoped person-title queries and the accepted Movie/TV adapters against real data. |
| YouTube | The official Kodi YouTube add-on owns account authorization, recommendations, Subscriptions, Watch Later and search. Credentials are client-local and are not copied between AsterTV clients. | Accepted v2 boundary and PA2 synthetic design | Determine whether genuinely isolated guest state is supported. Reject guest YouTube rather than sharing the primary add-on profile if isolation cannot be proved. |
| Film/TV requests | Seerr owns discovery and request state. Existing clients use a restricted broker/token path; the low-spec identity proved search, denial and one explicit real request without exposing a token. | `services/kodi/astertv-v3/low-spec/EVIDENCE-2026-11-04.md`; v2 Requests routes | Map each household profile to request authority and retain explicit final submission. Podcast requests may not be routed through Seerr. |
| Audiobooks and podcasts | Audiobookshelf owns catalogue and listening progress. AsterTV uses a restricted client configuration; credentials remain outside Git and release packages. | Accepted v2 boundary; low-spec Books refresh and restricted-key evidence | Prove profile mapping, resume semantics and select a duplicate-aware podcast request/subscription authority before enabling writes. |
| eBooks and narration | Calibre/CWA supplies eBook metadata/content. The prepared narration store and its generation manifest decide which books are playable; canonical Kokoro sentence timing is the accepted fallback. | v2 Books payload; `services/unified-media/calibre-worker/`; project evidence | Confirm the exact read-only catalogue boundary and ready-generation schema. Word-follow timing must come from measured canonical output and fail back to sentences when tolerance is missed. |
| News | Existing News Digest runtime owns feed, article and narration state. The canonical Aster voice contract is already in production. The v3 page is presentation-only until the existing routes are adapted. | Accepted v2 digest; `services/kodi/astertv-v3/deploy/news-playback/`; PA3 News screenshot | Complete the recurring lifecycle repair acceptance, then bind the v3 surface without replacing digest ownership or narration controls. |
| Household state | Home Assistant owns entity and automation state. The existing AsterTV Home delivery is a restricted read path. The repository `aster_registry` exporter is disabled by default and registers no service/action/route. | `services/home-assistant/aster_registry/README.md`; low-spec 63-reading delivery evidence | Review the exact alias/entity allowlist and freshness contract. A separate per-client semantic control bridge is still required; do not expose arbitrary HA service calls. |
| Cameras and door events | Frigate/camera sources plus Home Assistant own imagery and event state. Existing AsterTV access is source-restricted and uses forced-command delivery; camera images are not library media. | Low-spec camera start/frame/stop evidence; PA3 synthetic fresh/stale/unavailable/door states | Select exact allowed sources, profile/display entitlements, refresh/live mode, event debounce, timeout, quiet hours and playback policy before any live page integration. |
| Whole-home Aster AI | The existing Aster service and AI Access Broker own inference, tools and approvals. Kodi has no Aster credential or general tool authority. | `services/aster-agent/`; project architecture and PA3 synthetic Aster AI surfaces | Create a dedicated AsterTV broker identity exposing only media search, page navigation, bounded playback, News and reviewed HA commands. Prove denial, timeout, cancellation and prompt-injection behaviour before live use. |
| Accounts/profiles | No system-wide AsterTV account authority is currently adopted. Service identities and client-local profiles exist independently. | Project authority model | M2 must choose the account authority, field-level shared/private matrix, recovery admin and mappings before guest mode or private integrations proceed. |
| Client state and recovery | Each Kodi client owns its active player/application state. The host-bound reliability guard may restore only accepted Aster-owned files and clear only the narrowly defined volatile Music recovery latch after repeated idle/empty proof. | `services/kodi/astertv-v3/reliability/README.md`; installed-state evidence | Define the semantic Home Assistant/Aster Remote surface without arbitrary JSON-RPC, then resolve the low-spec repeated mixed-media lifecycle stall before release qualification. |

## Decisions still required before implementation

1. Account authority, recovery administrator and the shared/private field matrix.
2. YouTube guest feasibility based on actual add-on profile isolation.
3. Podcast request/subscription authority and duplicate/idempotence contract.
4. Exact Calibre/CWA read boundary and ready-narration manifest contract.
5. Camera source allowlist, continuous-feed display/profile, door-event policy
   and quiet hours.
6. AsterTV broker identity/capability set and whether speech capture starts with
   the G20 microphone or a synthetic transport fixture.
7. Home Assistant alias/entity allowlist and the separate semantic control
   bridge contract.

No decision above authorizes an operational change. Each implementation remains
a bounded Stream M step with its target, checkpoint, validation and rollback
presented immediately before mutation.

## Client baseline observations

Read-only checks on 2026-11-04 produced the following current comparison. An
initial Bedroom reachability failure was subsequently diagnosed and repaired;
the table records its later live state rather than filling from history.

| Client | Current hardware / output | Kodi integration surface | Recovery boundary |
|---|---|---|---|
| AsterTV Family | Intel N95, four physical cores; Alder Lake-N UHD `8086:46d2`; HDMI 0 reports `Beyond TV`; Intel I226-V Ethernet and RTL8822CE Wi-Fi are present | LibreELEC 13 nightly `440640e`; Kodi 22.0 RC1 `01d4146…d46`; Aster/Jellyfin/YouTube/Books/Music/Requests/Home/voice/player/reliability add-ons present; Jellyfin repository add-on also present | `astertv-release-guard.service` enabled; accepted-manifest SHA-256 `84cced22…93bc` |
| AsterTV Bedroom | Intel i5-9500T, six cores; Coffee Lake UHD 630 `8086:3e92`; HDMI 0 reports `LG TV SSCR2`; Intel Wireless-AC 9560 and Realtek gigabit Ethernet | LibreELEC 13 nightly `440640e`; Kodi 22.0 RC1 `01d4146…d46`; same functional Aster/Jellyfin/YouTube/Books/Music/Requests/Home/voice/player/reliability add-on surface as Jen | Release guard enabled; accepted-manifest SHA-256 `474c887d…f204`; Wi-Fi stability unit enabled at SHA-256 `6a829d42…6b90` after a proved power-save latency repair |
| AsterTV Jen | Intel i5-4570T, two cores/four threads; Haswell iGPU `8086:0412`; HDMI 0 currently reports `LG HDR 4K`; Intel I217-LM Ethernet | LibreELEC 13 nightly `440640e`; Kodi 22.0 RC1 `01d4146…d46`; same functional Aster/Jellyfin/YouTube/Books/Music/Requests/Home/voice/player/reliability add-ons as Family, without the Jellyfin repository add-on | `astertv-release-guard.service` enabled; accepted-manifest SHA-256 `dfc51bc8…c3ff` |

The hardware and accepted-manifest hashes intentionally differ. Equality of
software version does not imply codec, audio, recovery payload or performance
parity. Family retains the production Dolby/HDR contract; Jen remains the
measured low-spec 1080p candidate.

Bedroom's earlier unreachable result was a combination of stale Mac SSH trust
for `.140` and Intel Wi-Fi power saving. The live host had remained up for almost
four days, signal was `-54 dBm`, and no repeated driver disconnects appeared.
Disabling power saving changed 20-packet latency from 107.540 ms average /
211.173 ms maximum to 2.440 / 4.973 ms in the volatile trial and 2.244 / 4.974 ms
after persistent installation, with zero loss throughout. Kodi remained active.
The service is documented under `services/kodi/astertv-v3/deploy/bedroom-wifi/`;
an approved reboot proved it enabled/active with power saving off, Kodi active,
and 4.085 ms average latency. That reboot also exposed a pre-existing release-
guard unit defect: systemd expanded `%H` to `LibreELEC`, while the accepted
manifest is correctly host-bound to `AsterTV-Bedroom`. Direct verification of
all 535 accepted files returned clean. The unit binding needs a separate bounded
repair; no accepted payload change or resnapshot is required. That repair was
subsequently approved and completed: only the guard unit's argument changed to
the literal `AsterTV-Bedroom`; unit SHA-256 is `5839efc…be65`. The guard then
returned `Result=success` / `ExecMainStatus=0`, the accepted-manifest hash
remained `474c887d…f204`, all 535 files verified clean, Kodi remained active,
Wi-Fi power saving remained off and `systemctl --failed` was empty. Regression
tests now enforce that the Wi-Fi unit remains outside the add-on release payload
and that future reliability installs render the validated literal hostname.
