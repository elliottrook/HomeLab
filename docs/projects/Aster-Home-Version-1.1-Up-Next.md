# Aster Home v1.1 - Up Next

Owner: Jason. Created 2026-10-23. Stream M. Status: implementation/local tests;
HP test deployment approved; production promotion not authorized.

## Purpose, authority and exclusions

Urgent bounded upgrade ahead of v2: the existing Continue Watching rail keeps
unfinished films/episodes and adds the next unwatched regular episode after
the last completed episode of a started series. When caught up, retain a
browsable series card saying New episodes when available. Use real known air
dates only. Do not recommend every unstarted show or guess future releases.

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

Bound queries to 24 recent series and 2,000 episodes per series. A truncated or
failed query must not be interpreted as caught up. Existing episode resume
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
- [ ] M3: real HP directory/art/focus/refresh tests; no fabricated watch state.
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

Resume: owner G20/embedded-rail walkthrough remains M3/M5; obtain separate
BOSGAME promotion approval afterward. No push is authorized. V2 services are
not deployed. See the operator note below for actual behavior and rollback.

## Operator note

On HP Aster Media Home, Continue Watching contains resumable films/episodes,
Up next episode cards and browsable caught-up series. A future date appears
only if supplied by indexed metadata; otherwise New episodes when available
is deliberately non-specific. Series with no viewing history are not added.
The hero action for a caught-up card is Browse series, not an instruction to
queue an entire show. Malformed segment responses fail without a prompt.

During a TV episode, Intro markers show Skip intro, Outro markers show Play
next episode only if a following episode is actually indexed. Press OK to act,
or choose Keep watching/Back to dismiss; playback is never automatic. Without
markers no prompt is invented; the OSD Next button still uses the indexed
following episode. Finales do not point to nonexistent episodes. Known target
resume is retained; Kodi/Jellyfin may rewind a few seconds for context.

Both native Jellyfin popups are disabled on HP to avoid two competing prompts;
Jellyfin remains the marker and playback authority. The marker reader currently
supports one configured server, failing closed for multiple servers. To roll
back, restore accepted v1.0.5 add-ons and the checkpointed Jellyfin settings
under a stopped Kodi session, then restart and verify the ordinary UI/streams.
Preserve private user credentials; never publish recovery XML or profile files.

References: [Jellyfin media segments](https://jellyfin.org/docs/general/server/metadata/media-segments/)
documents typed Outro metadata supplied by providers, not a client-side timing
guess. [Seerr](https://github.com/seerr-team/seerr) is v2, not this change.
