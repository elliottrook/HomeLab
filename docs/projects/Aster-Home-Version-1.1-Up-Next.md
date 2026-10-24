# Aster Home v1.1 - Up Next

Owner: Jason. Created 2026-10-23. Stream M. Status: deployed to HP and BOSGAME;
production promotion explicitly approved, household remote walkthrough pending.
Current patch: **1.1.1**, available-episodes-only correction approved/deployed.

## Purpose, authority and exclusions

Urgent bounded upgrade ahead of v2: the existing Continue Watching rail keeps
unfinished films/episodes and adds the next unwatched regular episode after
the last completed episode of a started series, **only when that episode is
available in the synced library**. Caught-up series, future-dated entries and
missing-file episodes produce no card. A newly available first episode of the
following season can bring a series back. Do not recommend unstarted shows,
show future-release notices or guess release dates. This supersedes v1.1.0's
caught-up placeholder design at the owner's explicit correction.

Also requested during this change: Aster's own Skip intro at a real Intro
marker and Play next episode at a real Outro marker. Owner explicitly approved
replacing both native Jellyfin popups on HP. No auto-skip, autoplay countdown
or fake last-90-seconds detector. Requires actual segment markers and safe
remote navigation. Missing markers must be explicit; new server detector
installation is not implicitly authorized by the client UI request.

Kodi's synced Jellyfin library supplies episodes, availability and watch/resume
state. Jellyfin remains the server authority; do not mark watched or mutate
progress to manufacture a test. No new credential, firewall, subscription,
acquisition, OS/firmware or unrelated v2 feature is in scope.

## Assessment and architecture

Read-only HP discovery confirmed VideoLibrary.GetTVShows and GetEpisodes
provide tvshowid, season/episode, playcount, resume, lastplayed, firstaired,
art and existing playback file. Aster's existing rail supplied only resumable
items; completed episodes therefore disappeared without replacing the row.

Read the complete series directory up to 1,000 shows and query up to 2,000
episodes for each started series; visible rail remains at most 24 items. A
truncated or failed query must not be interpreted as availability. Existing episode resume
suppresses another Up Next card for the same series. Respect Specials/episode
zero, season boundaries, unavailable files and future dates. Preserve existing
Kodi/Jellyfin playback URLs and authentication path. No private state export.

Risk: wrong ordering/deduplication, stale embedded rail refresh, popup focus,
long catalogue queries and regressions in resume/watch state. Validate helpers,
fake Kodi adapter and real read-only directory results before user testing.
Checkpoint HP before installing; one brief Kodi restart is approved. Stop on
new dependency, unverified checkpoint or unexpected identity/OS change.

## Milestones and acceptance

- [x] M0: source/requirements and risk recorded; HP-only test approved.
- [x] M1: helper/adapter tests: resume, next, season boundaries, caught-up,
  future/missing episode, malformed/nonfinite data, partial reads, dedup/order.
- [x] M2: package deterministic 1.1.0 candidate without overwriting v1.0.5;
  private HP checkpoint, file-hash verification and restart.
- [x] M3: real HP directory/art/focus/refresh tests; no fabricated watch state.
- [x] M4: intro/outro prompt using verified metadata; exact intro seek,
  next-episode bookmark handover, dismiss and manual Next; no auto-play/skip.
- [ ] M5: owner remote/episode-completion walkthrough, independently accepted
  production promotion and recovery handover.

## Recovery, integration and maintenance

Reuse accepted v1.0.5 package plus private HP profile/keymap/boot checkpoint;
do not change OS, server identity or saved libraries. Record candidate hashes
and restore only changed add-on files then restart Kodi if needed. No package
or profile deletion. Full destructive restore is not required for this UI gate.

No new NetBox, Beszel agent, DNS, firewall, Homepage, rack or credential object.
Existing Kodi/Jellyfin health covers the client; bounded sanitized warnings
and live query latency are the service-native observability handoff. Update
project/release/operator records; wiki/mirror accepted behavior follows promotion.
No new speech. Official Aster assets/accepted TV visual identity are retained.
Per-milestone local commits; push needs explicit approval, then mirror check.

## Evidence / next safe action

2026-10-23: HP schema probe succeeded; the most recent sampled series has nine
episodes, seven watched and nine indexed playback files. Local helper tests
include next-season transition, held release date, caught-up series and resume
priority. Installed Jellyfin add-on already supports native MediaSegments and
Up Next events, but a compatible segment provider and popup consumer must be
verified; presence of Python code alone is not proof of available markers.

HP-only candidate evidence: 99 skin/helper, 19 media plugin, 13 Books bridge,
three sound-pack and three deterministic packaging tests (137 total). Initial
rail package deployed after verifying 3,525 private checkpoint members;
SHA-256 `57b3e888e338d5dd07036acf6c02101d216d1a0c1a62ea93468aa067c93eb88f`,
device directory `/storage/.aster-checkpoints/aster-v1.1.0-prepromotion-20261023/`.
No OS, keymap, refresh identity/timer or server settings changed. All four
add-ons are enabled; initial 151-file package and later 153-file credits
candidate matched their respective manifests. New credits files received a
verified changed-file checkpoint under
`/storage/.aster-checkpoints/aster-v1.1.0-rail-before-credits-20261023/`; skin
reload avoided a second Kodi restart. Candidate build revisions are retained
in separate dist directories; none is production accepted.

Two live directory reads returned 24 rows, eight Up Next and five caught-up
series in 0.34-0.44 seconds. Actual playback paths and season art are retained.
The new popup was rendered as an explicit TEST layout and Keep watching was
dismissed with remote Right/Select. No automatic next playback was requested.

Credits discovery: installed Jellyfin 2.2.0 already supports MediaSegments.
The first source-local query used an obsolete token-header format and got
401; using its normal MediaBrowser authorization succeeded without modifying
the identity. Twelve sampled episodes expose 13 Outro segments and two named
credits chapters. Aster reads only the active item's bounded markers using
the existing single-server client's identity; no credential copy, bearer URL,
new transport, provider or server write. No markers means no claimed credits
detection, with manual OSD Next retained. Multiple configured servers fail
closed until exact current-server selection is supported.

Live playback checks used already-watched episodes with no resume bookmark.
A season finale correctly offered no nonexistent next episode. The next sample
resolved current Kodi episode 5965 to following 5966. At the verified Outro
timestamp 4,985.628 seconds, Jellyfin's existing native credits popup appeared
first and blocked Aster's focus. That popup currently has skipCreditsMode=2;
requested approval to disable only that redundant HP popup while retaining
intro skipping and marker data. Playback was stopped and test overlays closed.
These normal playback tests may update last-played/watch counters; no watch
state was manually fabricated and no unfinished source bookmark was selected.

Follow-up approval and evidence: owner approved native credits replacement and
explicitly expanded this to native intro replacement and Aster intro/outro.
Verified private settings checkpoint:
`/storage/.aster-checkpoints/aster-v1.1.0-native-popups-20261023/jellyfin-settings.xml`,
SHA-256 `6eba8a1c07e1f419fe9569b14f8b698ad856d632c1845cade2bb7c1cd90ae1f7`.
Using the live Kodi add-on settings API, set only skipIntroductionMode and
skipCreditsMode to 0; mediaSegmentsEnabled stays true. Native settings and the
full pre-promotion checkpoint are copied to private Mac recovery storage under
`/Users/jelliott/lab/private-backups/aster-tv/hp/2026-10-23-v1.1.0/`, outside Git.

The first in-place Player.Open transition exposed the following episode's ID
before its clock changed, clearing its existing resume point during test.
Recovered the exact original 1,802-second bookmark from recorded evidence,
independently re-read server state, and corrected the handover to stop/settle
the old session before opening the next with Kodi's boolean resume option.
A numeric resume argument is a percentage, not seconds; the rejected trial
was replaced and covered by a runtime mock regression. The corrected live
test opened episode 5966 at 29:52 (the normal Jellyfin resume rewind from the
saved position), then stopped. The final candidate uses boolean resume only.

Real intro test: current completed episode 6113 has Intro 252.0-310.31 seconds
and no next episode in its indexed series. Aster showed Skip intro, explicit
Select sought to 00:05:10.310 in the same episode, and the test stopped media.
Thus intro does not depend on there being a following episode. The real Outro
test independently showed Play next episode at 4,985.628 seconds. Dismissal
and a labelled layout capture were also checked. No episode auto-starts and
no marker is estimated. Modal selector focus is respected.

Cleaned up test effects: used the verified pre-promotion video database to
confirm that source episodes 6113 and 5965 were completed with no resume and
target 5966 was unfinished at 1,802 seconds. Restored only those source
Played/no-resume flags and the exact target bookmark through authenticated
Jellyfin user-data updates, then independently re-read the results. Normal
test play counters/last-played history were not rewritten. These recovery
writes are an explicit test-cleanup exception, not runtime watch-state logic.

Final package: `services/kodi/dist/aster-home-v1.1.0-candidate8`, all 153 installed
files matched on HP; release hashes and detailed validation are tracked in
`services/kodi/releases/aster-home-v1.1.0.json`. Earlier candidate artifacts and
changed-file checkpoints are retained. No OS, native media files, production
client or broad network access was changed. HP is idle after tests.

At the candidate8 handoff, the owner G20/embedded-rail walkthrough and separate
BOSGAME promotion approval were pending. The later approval/promotion below
supersedes that hold. No push is authorized; v2 services are not deployed.
See the operator note below for actual behavior and rollback.

### Production promotion and episode-hero repair — 2026-10-23

The owner confirmed the production unit was available, explicitly requested
v1.1 deployment, and authorized fixing the TV hero if minor. This supersedes
the earlier production hold. Both clients were independently confirmed idle.

Read-only directory checks reproduced the same defect on HP and BOSGAME:
episodes have `tvshow.fanart` but no direct `fanart`, while films normally have
direct `fanart`. The home hero only read the latter. Added an ordered series
fallback for both home rails, retaining direct movie artwork. No server data,
watch state, episode playback path or source artwork was modified. HP received
only the changed Includes.xml with a verified checkpoint at
`/storage/.aster-checkpoints/aster-v1.1.0-before-episode-hero-20261023/` and skin
reload. Actual HP screenshots show The Voice and Dark hero artwork; Dark also
retains its real episode synopsis. Missing source synopsis/genre/year is not
invented by this repair.

Candidate9 is reproducible with 138 passing tests (100 skin/helper, 19 media,
13 Books bridge, three sound and three packaging). All 153 files match this
same manifest on both clients. BOSGAME was briefly stopped after verifying the
package, its active refresh timer was paused/restored, and a private profile,
configuration, SSH and boot archive was created and byte-checked against
3,023 regular source files before installation. Checkpoint:
`/storage/.aster-checkpoints/aster-v1.0.5-before-v1.1.0-20261023/`.
Archive SHA-256:
`2458b7e5b41f32643758f28b8aa68baa66b8f01f5ee5253508f6d71679752d42`.
An independently hashed 0600 off-device copy is retained outside Git in
`/Users/jelliott/lab/private-backups/aster-tv/bosgame/2026-10-23-v1.1.0/`.

Production installation changed the four packaged add-ons and only the two
Jellyfin popup values (`skipIntroductionMode=0`, `skipCreditsMode=0`);
`mediaSegmentsEnabled=true` remains unchanged. Verified all four add-ons enabled
at 1.1.0, no active player and Kodi active with zero automatic restarts.
Two independent live rail reads returned 24 rows / seven Up Next cards,
10 episode cards all exposing inherited series fanart, in 0.63/0.36 seconds.
Production screenshot confirms the selected episode's hero now renders.
An independent film screenshot confirms direct movie artwork still renders.
Compared with the stopped-session checkpoint: 145 audio/display/language/
subtitle settings, remote keymap, catalogue-refresh units and boot files are
unchanged. No v2 prototype, OS, firmware, identity, network or server changes.

M5 remains open only for the owner's household remote/real-credits walkthrough
and release acceptance. No production playback was initiated for this promotion;
the exact marker/seek/handover evidence remains the previous HP tests. No Git
push is authorized. Existing service-native health/refresh coverage remains;
there is no new Beszel, Doctor, NetBox, DNS or firewall object to register.
Repository operator/release records are updated; wiki/mirror publication is
deferred until owner acceptance (the local mirror checkout is absent).

Recovery: stop Kodi; use this production checkpoint to restore only the four
changed Aster add-on trees and the checkpointed Jellyfin settings. Remove only
the new v1.1 intro/outro script/dialog if absent in the v1.0.5 archive, then
restart and verify ordinary media/resume. Do not restore another client's
profile, overwrite libraries/watch state or change the OS/audio settings.
Retain both the accepted v1.0.5 bundle and immutable candidate9 artifacts.

## Operator note

On HP and production Aster Media Home, Continue Watching contains resumable films/episodes,
and available Up Next episode cards. No caught-up placeholders or future-release
notices remain. A started show returns when its next unwatched regular episode
has an indexed playback path and is not future-dated; no numbered episode or
season gap is skipped. For example, after MobLand episode 6, wait for episode 7;
after The Morning Show season 4 finale, wait for season 5 episode 1. This follows
the existing Jellyfin-to-Kodi sync and home-rail refresh, not an immediate push
notification or a download subscription. Return to/reopen Aster Media if the
home page has remained open during synchronization. Series with no viewing
history are not added. Malformed segment responses fail without a prompt.

During a TV episode, Intro markers show Skip intro, Outro markers show Play
next episode only if a following episode is actually indexed. Press OK to act,
or choose Keep watching/Back to dismiss; playback is never automatic. Without
markers no prompt is invented; the OSD Next button still uses the indexed
following episode. Finales do not point to nonexistent episodes. Known target
resume is retained; Kodi/Jellyfin may rewind a few seconds for context.

Both native Jellyfin popups are disabled on both clients to avoid competing prompts;
Jellyfin remains the marker and playback authority. The marker reader currently
supports one configured server, failing closed for multiple servers. To roll
back, restore accepted v1.0.5 add-ons and the checkpointed Jellyfin settings
under a stopped Kodi session, then restart and verify the ordinary UI/streams.
Preserve private user credentials; never publish recovery XML or profile files.

References: [Jellyfin media segments](https://jellyfin.org/docs/general/server/metadata/media-segments/)
documents typed Outro metadata supplied by providers, not a client-side timing
guess. [Seerr](https://github.com/seerr-team/seerr) is v2, not this change.

## v1.1.1 correction — 2026-10-23

Owner explicitly rejected caught-up cards and approved a checkpointed HP-first,
then production patch with one Kodi restart per client. Removed those cards;
future/missing-file next episodes now return no card, and missing numbering
cannot skip straight to a later episode/season. Expanded the old 24-recent-show
candidate read to a complete bounded 1,000-show read so a long-absent started
series can return. Current HP inventory: 209 shows, 51 started, all within the
complete-read bound. No acquisition, metadata or watch-state writes.

144 tests pass: 100 skin/helper, 25 video plugin, 13 Books bridge, three sounds,
three deterministic packaging. New synthetic regressions cover both owner's
examples, delayed availability, missing numbering, resumed films retained and
an older show beyond the former 24-show cutoff. Complete-read failure keeps
genuine resume entries rather than silently treating missing data as available.

Both clients received only six changed files: library helper, directory adapter
and four version descriptors. All 153 packaged files verified on each and all
four add-ons enabled at 1.1.1. HP validation passed before production began.
Two independent reads per device return 24 rows / nine available Up Next cards,
no series placeholders, and no MobLand or The Morning Show card. Independently
queried both shows' episode catalogues and confirmed no eligible next episode.
HP rail latency 0.590/0.575 seconds; production 0.542/0.537 seconds, bounded
and acceptable relative to previous ~0.4-second recent-only reads. No playback
was initiated, no fake episode was added, and no resume/watch state was set.

Pre-patch private checkpoints on each client:
`/storage/.aster-checkpoints/aster-v1.1.0-before-v1.1.1-20261023/`.
Full stopped-session archive/member verification: HP 3,555 regular files,
SHA-256 `3a73afa04285ce6a72aa73dd6d606a074d803fbcac85f192d56d1af3a3d2c8fe`;
production 3,044 regular files,
SHA-256 `0ac095832eff397bfe76ed2d59f897f1173d56c3c453e4903f8d399b66cfd044`.
Off-device copies are restricted to 0600 under the existing private Mac backup
tree for each client, dated `2026-10-23-v1.1.1`, outside Git. Rollback needs only
those six changed add-on files from the client's own checkpoint and a Kodi
restart; do not restore databases, credentials or another client's profile.

Post-restart comparison preserves 136 HP / 145 production AV/language/subtitle
settings and exact Jellyfin settings, keymap, refresh units and boot files.
Both catalogue timers restored; production Kodi active with zero auto-restarts.
No new network, credential, service or monitoring object; existing integration
ownership and wiki/mirror publication gate remain as above. No v2 code deployed
and no Git push authorized. Immutable artifact/manifest:
`services/kodi/dist/aster-home-v1.1.1-candidate1`, tracked in
`services/kodi/releases/aster-home-v1.1.1.json`.
