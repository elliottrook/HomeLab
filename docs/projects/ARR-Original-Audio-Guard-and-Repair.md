# ARR English-first audio guard and repair

> Status: Active — M1 policy and approved M3 removal complete; M2 validator and two subtitle gaps remain
>
> Owner: Jason
>
> Proposed: 2026-10-23
>
> Authorization: Stream M
>
> Service release: existing production ARR stack V1 configuration change
>
> Current/target environment: Production applications on TrueNAS, VLAN 20
>
> Build reference: Sonarr 4.0.20.3014; Radarr 6.4.4.10685; Profilarr 2.2.0
>
> Rollback reference: exact M1 API exports plus fresh native backups; the approved M3 media deletion deliberately has no new snapshot and is recoverable only by reacquisition or unrelated pre-existing retention

## Purpose and desired outcome

Give every Sonarr and Radarr quality profile an English-first release policy,
prevent foreign-only releases for titles whose original language is English,
and preserve legitimate foreign-language films and shows. Produce a safe,
resumable way to identify and replace existing English-original files that lack
an English audio stream.

## Current state and evidence

- A read-only `ffprobe` inventory on 2026-10-23 covered 7,214 files. Thirty-two
  files had only non-English audio tags; 26 had embedded English subtitles, none
  had an external English sidecar, and six had no identified English subtitles.
- Thirty-one of those files initially mapped to Sonarr/Radarr records. ARR
  metadata marks 25 as English-original; six map to another original language.
  One Swedish film, `A Man Called Ove`, was initially present on disk without a
  matching Radarr file record.
- Before M1, Sonarr had one `English Audio` language custom format. It scored 100 with a
  minimum score of 100 in the current `HD-720p`, `HD-1080p`,
  `HD - 720p/1080p`, and `Any - English Audio (TV)` profiles, but scores zero in
  `Any`, `SD`, and `Ultra-HD`. Every profile has upgrades disabled.
- Before M1, Radarr had no custom formats. Its profiles had minimum custom-format score
  zero and upgrades disabled.
- At diagnosis, Seerr's default current-library target was `HD-1080p` for both Sonarr and
  Radarr. Current roots use Sonarr profiles 3/4/6/7 and Radarr profiles `Any`
  and `HD-1080p`. Archive roots use the unguarded `Any` profile.
- The affected `Sense8` season was acquired through a Sonarr search on
  2026-10-08 with custom-format score zero even though the series now uses the
  `HD-1080p` profile whose current minimum is 100. This indicates the guard was
  added or tightened after acquisition; it does not prove the present rule
  would accept the same release.
- ARR's stored language metadata disagrees with direct stream tags for several
  files. Release parsing therefore cannot prove that the downloaded container
  really contains the promised audio.
- Profilarr is healthy and has a local profile database, but its live database
  contains zero ARR instances and zero assigned profiles. It is not currently
  synchronizing or overwriting Sonarr/Radarr despite the operational reference
  naming it as profile authority. This is documented drift to reconcile.
- Native Sonarr and Radarr scheduled backups exist from 2026-10-19. The latest
  `Media@auto-2026-10-23_00-00` snapshot protects the dataset, but the production
  services have no configured recycle-bin path.
- The accepted M1 policy is live on all seven Sonarr and six Radarr profiles:
  `Original Audio` scores 100, `English Audio` scores 50, and the minimum is 100.
  Upgrades remain disabled.
- The reviewed correction classified 25 files as English-original mismatches
  and seven as legitimate foreign originals. On explicit approval, the 25
  mismatches were removed through ARR and left monitored and missing. The seven
  foreign originals were retained; five have embedded English subtitles, while
  `Parasite` and `The Lunchbox` still need English subtitle correction.

## Scope and exclusions

In scope:

- apply the same English-first rule to every Sonarr and Radarr quality profile;
- require original-language audio as the eligibility floor and award an
  additional score for English audio;
- preserve legitimate foreign-original films and shows;
- validate profile behavior with read-only release evaluations and a bounded
  synthetic/known-title comparison;
- design and implement a report-first post-import stream validator;
- prepare a reviewed correction queue for the existing affected files;
- perform the specifically approved one-time removal of 25 English-original
  mismatches without a new snapshot, while retaining all foreign originals;
- register `A Man Called Ove` in Radarr without searching or replacing it.

Excluded without a later explicit approval:

- any media deletion, replacement, move, transcode, or rename beyond the exact
  25-file removal approved and completed on 2026-10-23;
- searches or grabs beyond the separately approved M4 target set, queue
  cancellation, unmonitoring, or profile reassignment;
- enabling upgrades globally;
- treating language tags alone as proof of spoken language;
- changing indexers, download clients, Bazarr, Jellyfin, Seerr request behavior,
  network policy, credentials, or public exposure;
- configuring Profilarr synchronization until its authority drift is separately
  reconciled and tested.

## Authority model

| Fact | Authority |
|---|---|
| Release eligibility and profile assignment | Live Sonarr/Radarr configuration |
| New-request default profile/root | Seerr production configuration |
| Actual container audio/subtitle streams | Direct `ffprobe` on the media file |
| Original language | Sonarr/Radarr metadata, with title-level human override where metadata is wrong or the work is intentionally dubbed |
| Profile-as-code intent | Profilarr only after an ARR instance and explicit profile mapping are configured and validated |
| Current operational design | `docs/reference/ARR-Stack-Operational-Reference.md` |

## Architecture and data flow

Normal acquisition remains:

`Seerr request -> Sonarr/Radarr search and profile evaluation -> SABnzbd -> ARR import -> Jellyfin/Bazarr`

The deployed guard uses two Servarr language custom formats on every profile:

- `Original Audio`: score 100, with minimum custom-format score 100. This is the
  eligibility floor. An English production therefore needs English audio, while
  a German, Japanese, Spanish, Hindi, Swedish, or other foreign production can
  still qualify with its genuine original audio.
- `English Audio`: score 50 above that floor. This makes an English-containing
  release rank ahead of an otherwise equivalent original-audio-only release.
  A foreign title with original plus English audio therefore scores 150 and is
  preferred, while its original-only release remains eligible at 100.

All existing profile format scores are preserved unless they conflict with
these two language entries. Upgrades remain disabled, so this profile change
does not itself launch searches or replace existing files.

The proposed validator runs source-locally after import or on a bounded schedule:

`ARR item/original-language metadata + ffprobe streams -> classified finding -> report/notification -> reviewed repair candidate`

It must not delete or replace a file automatically. A later repair action may
request an ARR search only after the candidate title, existing file, recovery
copy, replacement constraints, and post-import verification are explicit.

## Privacy and security design

- API keys stay inside the TrueNAS source-local shell/container boundary and are
  never printed, copied into Git, or written to the evidence log.
- The validator emits title, path, language tags, classification, and timestamps
  only. It does not publish API keys, download URLs, indexer GUIDs, or credentials.
- No new listener, firewall rule, DNS record, external service, or public path is
  required.
- Any future mutation path uses the existing ARR APIs and a bounded service
  identity or the existing approved operator path; natural-language output alone
  is never repair authority.

## Pre-start risk assessment

| Risk | Likelihood / impact | Control and residual risk |
|---|---|---|
| Legitimate foreign-original media is rejected | Medium / high | Use `Original` as the required floor and English only as a bonus; validate against English, German, Japanese, Spanish, Hindi and Swedish examples before acceptance. Metadata can still be wrong for multilingual works. |
| Existing archive titles are unintentionally reacquired | Medium / high | Apply the rule to archive profiles as requested, but leave upgrades disabled and run no search/grab command. Compare queues and wanted state before and after every profile edit. |
| Existing media is deleted during replacement | Medium / high | Jason explicitly accepted deletion of the reviewed 25-file English-original set and declined a new snapshot because the files were unusable to him. That bounded exception is complete; future automated replacement still requires a separate safety design and approval. |
| Release metadata claims audio that is absent | High / medium | Add direct post-import stream validation; release-title custom formats alone remain insufficient. |
| Mislabelled stream tags cause false alarms | High / medium | Report first. Where tags conflict with ARR metadata or title expectations, require a playback/listening check or local speech-language classification before repair. |
| Profilarr later overwrites direct ARR changes | Low now / medium later | Live state shows zero instances/mappings. Record drift and do not enable sync until profile-as-code is reconciled and rollback-tested. |
| Service interruption | Low / low | Custom-format/profile API updates should not restart containers. Abort on health degradation, queue growth, unexpected commands, or profile-assignment drift. |

No destructive or irreversible operation was needed for the preventative
profile change. Fresh API exports and native backups provide configuration
rollback. The later 25-file deletion was separately and explicitly approved
without a new snapshot; those media files are not rollback-protected by this
project and must be reacquired. This exception does not authorize future
unattended deletion.

## Persistence plan

- Persist current custom-format and quality-profile exports as sanitized evidence
  before mutation.
- Record every applied object ID, before/after digest, validation query, and
  rollback payload in this document or a linked evidence file.
- Resume by rereading this project, repository status, the latest audit workbook,
  and live profile/queue/health state. Never infer success from an earlier turn.

## Milestones

### M0 — Diagnosis and bounded change approval

- [x] Reconcile the audit with live ARR item/profile/original-language metadata.
- [x] Inspect Sonarr/Radarr custom formats, profile scores, upgrade settings,
  Seerr defaults, Profilarr mappings, recovery coverage, and recycle-bin state.
- [x] Jason approves the exact M1 production profile update.

### M1 — Apply English-first acquisition policy to all profiles

- [x] Capture a fresh TrueNAS/configuration checkpoint and exact API payloads.
- [x] Ensure both Sonarr and Radarr have `Original Audio` (`Language: Original`)
  and `English Audio` (`Language: English`) custom formats.
- [x] On every quality profile in both applications, score `Original Audio` 100,
  score `English Audio` 50, and set minimum custom-format score to 100 while
  preserving unrelated custom-format scores and quality settings.
- [x] Confirm all profile assignments are unchanged, upgrades remain disabled,
  no search/grab/import command ran, queues did not grow, and Seerr still
  defaults to `HD-1080p`.
- [x] Validate representative English-original and foreign-original release
  evaluations, English-first ordering, and denied wrong-language examples.

### M2 — Report-first validator

- [ ] Implement a bounded source-local scanner using ARR original-language
  metadata plus direct `ffprobe` stream evidence.
- [ ] Classify confirmed mismatch, metadata conflict, legitimate foreign original,
  probe failure, and untagged/unknown audio separately.
- [ ] Add last-success/failure state, locking, runtime cap, sanitized output, and
  actionable Doctor/notification coverage without automatic media mutation.
- [ ] Validate against the 32-item baseline and synthetic fixtures.

### M3 — Reviewed correction queue

- [x] Reclassify all affected titles with human overrides for intentionally
  foreign, multilingual, dubbed, or incorrectly tagged works.
- [x] Produce a repair manifest for only accepted English-original mismatches.
- [x] With Jason's explicit no-snapshot direction, remove the 25 approved files
  through ARR and verify every parent remains monitored and becomes missing.
- [x] Register and retain `A Man Called Ove` as a monitored Radarr movie; retain
  the other six foreign originals.
- [ ] Acquire English subtitles for `Parasite` and `The Lunchbox`, then re-run
  the stream/subtitle audit after replacement media begins to arrive.

### M4 — Targeted reacquisition

- [x] Reconfirm the 18 Sonarr episodes and seven Radarr movies are monitored and
  missing immediately before search.
- [x] Obtain separate Stream M approval for searches that can enqueue downloads.
- [x] Dispatch only Sonarr `EpisodeSearch` command 274893 for the 18 approved
  episode IDs and Radarr `MoviesSearch` command 274798 for the seven approved
  movie IDs.
- [x] Record completed command status, accepted grabs and resulting queues.
- [ ] Directly verify English audio on every imported replacement; leave any
  unresolved item monitored and missing.

## Validation and evaluation

- Compare English-original and foreign-original titles before and after the
  profile change: original audio must meet the minimum, an English-containing
  release must rank higher, and foreign-only audio for an English original must
  remain below the minimum.
- Confirm all current-root profile assignments and every archive-root assignment.
- Confirm upgrade flags remain false, queues do not grow unexpectedly, service
  health remains normal, and no media file timestamp/path changes during M1.
- Test validator behavior for English, foreign original, multi-audio, untagged,
  malformed, unsupported ISO, and probe-error cases.
- For future automated replacement, verify direct streams, subtitles, duration,
  Jellyfin playback, Sonarr/Radarr file identity, and the separately approved
  recovery policy before releasing any newly acquired copy.

## Observability and maintenance

M1 uses existing ARR health and queue checks. M2 should add a single summarized
Doctor status with counts and last-success age; it must not duplicate per-title
notifications. Beszel needs no change because no host/container is added or moved.

## Backup, restore and rollback

- Before M1: fresh Sonarr/Radarr native configuration backup or equivalent exact
  API export plus a named TrueNAS configuration checkpoint.
- M1 rollback: restore the previous custom-format and quality-profile payloads;
  verify profile assignments, health, and queue state.
- M3 exception: Jason explicitly declined a new snapshot and accepted that the
  25 unusable files would be deleted and reacquired. No project snapshot was
  created. Root-private metadata evidence at
  `/root/arr-english-removal-20261023T175232Z` records targets and results but
  contains no media recovery copy.
- Any future automated replacement must receive its own approved recovery or
  fail-safe design; the M3 exception is not a reusable deletion authorization.

## Documentation and systems-of-record updates

- [ ] HomeLab Doctor — M2 last-success/count check; M1 existing ARR checks suffice.
- [ ] Monitoring/alerting — summarized validator alert only; Beszel unchanged.
- [x] Backup and recovery — M1 payload/checkpoint verified; M3 no-snapshot exception and reacquisition-only recovery recorded.
- [ ] NetBox — not applicable; no device, interface, IP, VLAN, or service endpoint changes.
- [ ] Human wiki — add profile intent and safe correction workflow after acceptance.
- [ ] Aster mirror/snapshot — update derived operational knowledge after documentation is authoritative.
- [x] Operational reference and runbooks — correct Profilarr authority drift and record the language guard.
- [ ] Environment and release lifecycle — production V1 in-place configuration change; no promotion or new endpoint.
- [x] Repository documentation — project, portfolio, operational reference, and sanitized evidence.
- [ ] Diagrams/rack records — not applicable; no topology or physical change.
- [ ] Homepage/service discovery — not applicable; no UI endpoint change.
- [ ] Authentication/authorization — existing source-local ARR credentials only; no new human login flow.
- [ ] DNS, certificates and firewall — not applicable; no network change.
- [ ] Automation and schedules — required only for M2 validator.
- [ ] Security inventory — no new secret; validator credential path must remain source-local and revocable.
- [ ] AI administration integration — no new AI administration. Repairs remain operator-approved ARR actions.

## Graduation criteria

- Every Sonarr and Radarr quality profile requires original-language audio,
  prefers English audio, and preserves legitimate foreign-original media.
- Profile assignments and global upgrade behavior remain unchanged.
- The post-import validator is report-only, observable, recoverable, and proven
  against real and synthetic cases.
- Every accepted English-original mismatch is either monitored and missing,
  downloading an eligible candidate, or directly verified after import; foreign
  originals are retained and subtitle gaps are explicit.
- Profilarr's real authority status and future sync procedure are documented.

## Evidence log

| Date | Action | Evidence and result |
|---|---|---|
| 2026-10-23 | Full media stream audit | 7,214 inventoried; 32 non-English-only by stream tags; 26 with embedded English subtitles; six without; zero English sidecars; 2,245 uncertain/unprobeable items retained separately |
| 2026-10-23 | ARR reconciliation | 31/32 matched to ARR files; 25 matched titles are marked English-original; archive roots use unguarded `Any`; one current movie is orphaned from Radarr |
| 2026-10-23 | Live configuration review | Sonarr has partially enforced English CF; Radarr has no CF; all profiles have upgrades disabled; Seerr defaults both apps to `HD-1080p`; Profilarr has zero live ARR instances/mappings |
| 2026-10-23 | Recovery review | Native scheduled config backups dated 2026-10-19 and `Media@auto-2026-10-23_00-00` exist; recycle-bin paths are empty; no mutation performed |
| 2026-10-23 | Policy clarification | Jason directed that all Sonarr and Radarr profiles receive an English-first rule; M1 was revised to use required original audio plus an English bonus across every profile |
| 2026-10-23 | M1 approval and checkpoint | Jason approved the exact 13-profile update. Fresh native backups completed as Sonarr command 274805 and Radarr command 274709; exact before/after API payloads and digests are root-private at `/root/arr-english-first-20261023T172319Z` on TrueNAS. |
| 2026-10-23 | English-first policy deployed | Added `Original Audio` to Sonarr; added `Original Audio` and `English Audio` to Radarr; applied Original +100, English +50 and minimum 100 to all seven Sonarr and six Radarr profiles. Profile assignments and disabled-upgrade flags are unchanged. |
| 2026-10-23 | M1 validation | Both containers remained healthy with no ARR health records. Sonarr queue remained 40 before/after (30 English score 100; 10 Japanese score 0 whose existing import block is the unrelated multi-season single-file safeguard); Radarr remained zero. No search, grab, import or media mutation was issued. |
| 2026-10-23 | M3 scope and approval | Jason clarified that genuine foreign originals with English subtitles are permissible, approved only the 25 English-original mismatches for deletion, requested no new snapshot, and authorized recording and pushing the result. |
| 2026-10-23 | Foreign-original retention | Retained seven foreign originals: `A Man Called Ove`, `Parasite`, `The Lunchbox`, `Sweet Bean`, `The Mysterious Gaze of the Flamingo`, `Tokyo Story`, and `Dark` S01E04. Five have embedded English subtitles; `Parasite` and `The Lunchbox` are recorded subtitle gaps. |
| 2026-10-23 | Approved media removal | Removed 18 Sonarr episode files and seven Radarr movie files through their file APIs: 25 files and 33,656,430,184 bytes (31.34 GiB). Every affected episode/movie validated as monitored and missing. No search or grab was started; queues remained Sonarr 40 and Radarr zero. |
| 2026-10-23 | Orphan registration and final validation | Added `A Man Called Ove` to Radarr as movie 993/file 2103, monitored and present, without search. Both containers remained running/healthy with zero health records; all seven retained foreign files still exist. Exact root-private manifest/result live at `/root/arr-english-removal-20261023T175232Z`. |
| 2026-10-23 | Targeted search approval and dispatch | Jason separately approved searches for all 25 monitored/missing records. Sonarr accepted `EpisodeSearch` command 274893 for 18 episode IDs and Radarr accepted `MoviesSearch` command 274798 for seven movie IDs. The seven retained foreign originals were excluded. |
| 2026-10-23 | Targeted search result | Both commands completed. Every target had a result: one Sonarr episode imported and 17 remained queued; all seven Radarr movies were queued. Every queued candidate scored 150 and parsed as English. Direct `ffprobe` of imported 12 Monkeys S04E11 confirmed French plus English E-AC-3 audio. The other 24 remain subject to direct post-import verification. |

## Close-out

Open. M1 and the approved M3 removal are complete. M2's recurring validator and
the two foreign-original subtitle gaps remain. Future files will be acquired
under the live English-first/original-audio policy.

## Documentation adequacy reflection

The operational reference now records Profilarr's real inactive sync state, the
English-first policy, retained foreign originals and the reviewed removal/search
result. The remaining documentation gap is the not-yet-implemented recurring
validator and its safe audio-mismatch workflow.
