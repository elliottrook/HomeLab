# Local Subtitle Generation/Translation Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen by
> Jason before implementation begins

## Purpose and desired outcome

Use a locally-run Whisper speech-to-text model to generate `.srt` subtitle
files for video-library titles that are missing an English subtitle track, and
optionally to generate non-English subtitle tracks for titles whose original
non-English subtitle/audio streams were deliberately stripped during archival.
The desired outcome is a working title's real accessibility gap closed (TV
subtitles) without ever mutating an existing video file, existing subtitle
file, or Radarr/Sonarr/Jellyfin state that the ARR stack already owns.

This is **not** a general "add subtitles to everything" project. The two
concrete, evidence-grounded motivations are:

1. **TV subtitles are essentially absent in this library.** The
   Plex-to-Jellyfin migration measured this directly: only 1 of 5,678 TV
   episodes carried an embedded subtitle stream at all
   ([Plex-to-Jellyfin-Media-Migration.md](<completed projects/Plex-to-Jellyfin-Media-Migration.md>),
   "Test external subtitles..." section). That is a real, measured gap in the
   Shows/Archive TV libraries, not a hypothetical one.
2. **Video-Library-Archiving deliberately drops non-English audio and
   subtitle tracks during archival to stay inside its size budget** — only
   the flagged-default (or first English, or first) audio track and
   English-tagged subtitle tracks survive the transcode
   ([Video-Library-Archiving.md](<completed projects/Video-Library-Archiving.md>)
   Architecture decisions, "Only one audio track and English-only subtitles
   are kept"; also recorded in
   [04-Operations.md](../04-Operations.md)). If a non-English subtitle track
   is ever wanted back for an archived title, generating it locally from the
   kept audio (for foreign-language audio still present pre-archival) or via
   translation is the only way to get it without re-acquiring the source.

## Current state and evidence

- No subtitle-generation tooling exists anywhere in this lab today. This
  document is the initial proposal; no implementation work has occurred.
- Movie/TV libraries and their exact host paths (confirmed via
  `docs/04-Operations.md`):

  | Library | Path |
  |---|---|
  | Movies (current, Radarr-managed) | `/mnt/Media/data/media/movies` |
  | Shows (current, Sonarr-managed) | `/mnt/Media/data/media/tv` |
  | Archive Movies (former Plex library) | `/mnt/Media/data/archive-movies` |
  | Archive TV (former Plex library) | `/mnt/Media/data/archive-tv` |

- Media stack (Jellyfin, Plex, Sonarr, Radarr, Lidarr, Prowlarr, Seerr, plus
  SABnzbd) runs as Docker containers on TrueNAS at `192.168.20.40`
  ([ARR-Stack-Operational-Reference.md](../ARR-Stack-Operational-Reference.md)).
  Radarr owns `/mnt/Media/data/media/movies`, Sonarr owns
  `/mnt/Media/data/media/tv`; Jellyfin only observes files after ARR import —
  it has no downloader/file authority. Archive Movies/Archive TV are outside
  ARR's canonical roots entirely (they hold the former Plex library, not
  ARR-managed files).
- Shared local LLM inference already exists as `aster-llama.service` on LXC
  110 (`192.168.70.12:11435`, OpenAI-compatible `/v1` API, model
  `aster-qwen3.8-27b` / `unsloth/Qwen3.8-27B-GGUF:UD-IQ4_XS`, Vulkan on the
  Intel Arc Pro B60 24GB, bearer-auth, Lab VLAN 70 —
  [Aster-Operations.md](../Aster-Operations.md),
  [02-IP-Addressing.md](../02-IP-Addressing.md)). This is a text LLM
  endpoint, not a speech-to-text model — it cannot itself run Whisper, though
  it could plausibly be reused later for a translation pass over
  Whisper-produced English text (see Open decisions).
- Video-Library-Archiving's GPU-accelerated transcode job runs against
  `/dev/dri` on the **TrueNAS host**, exposed through the Jellyfin Docker
  container, using an **Intel Arc A380** (confirmed via
  `docs/projects/completed projects/Video-Library-Archiving.md` Architecture
  decisions and Evidence log: "an Intel Arc A380 had landed on this host...
  `lspci`/`/dev/dri/renderD128`"). This is a **different physical GPU on a
  different physical host** from `aster-llama`'s Arc Pro B60 (which lives in
  Proxmox-hosted LXC 110 on Lab VLAN 70). Any claim that Whisper could "just
  use the same GPU as one of these" needs to specify which one and why —
  they are not interchangeable or co-located.
- Frigate (surveillance) separately uses a Coral Edge TPU on the Frigate VM
  (`192.168.20.10`), a third distinct accelerator not usable for Whisper
  (it is an object-detection ASIC, not a general compute device).

## Scope

- Generate new, additive `.srt` sidecar subtitle files for video titles in
  the Movies/Shows/Archive Movies/Archive TV libraries that currently have no
  English subtitle track, using a locally-run Whisper model (or a
  faster-whisper/whisper.cpp implementation — see Open decisions) transcribing
  the existing audio track.
- Optionally, for a title whose original non-English audio/subtitle track was
  dropped during Video-Library-Archiving's transcode but is still recoverable
  from a pre-archival source, transcribe/translate that track to produce a
  non-English or translated-English subtitle. This is explicitly scoped as
  **optional and secondary** — it depends on whether a usable source track
  still exists per title, which has not been inventoried.
- Validate output against a small, human-reviewed spot-check sample before
  any unattended or library-wide run, mirroring
  Video-Library-Archiving's and Jellyfin-Library-Integrity-Automation's
  dry-run-then-apply precedent.
- Integrate with HomeLab Doctor, backup and the other systems-of-record per
  the integration impact checklist below.

## Out of scope

- Re-encoding, transcoding, or otherwise modifying any existing video file.
  This project only ever writes a new sidecar subtitle file next to an
  existing video; it never touches video/audio streams.
- Overwriting or deleting any existing subtitle file, embedded or sidecar.
  If a title already has an English subtitle track (embedded or `.srt`), it
  is skipped, not "improved."
- Any interaction with Radarr's/Sonarr's file-tracking state. Adding a
  sidecar subtitle file does not change a monitored/`hasFile` file record and
  this project must not call any ARR write endpoint.
- Competing with Video-Library-Archiving for the same TrueNAS I/O/GPU window
  (Mon–Sat 01:30) or for the same GPU resource without a measured, agreed
  scheduling plan (see Pre-start risk assessment).
- Building a general-purpose translation/dubbing product, or transcribing
  audio for anything outside the Movies/Shows/Archive Movies/Archive TV
  roots (e.g., music, audiobooks, surveillance footage are explicitly not in
  scope).
- Any cloud/third-party transcription or translation API. Local processing
  only, per the lab-ethos privacy principle — audio content stays inside the
  lab network.

## Authority model

- Radarr/Sonarr remain authoritative for movie/episode file records; this
  project never writes to their APIs.
- Jellyfin remains authoritative for what subtitle tracks a client sees; a
  sidecar `.srt` file next to a video file is picked up by Jellyfin's own
  library scan, not pushed by this tool.
- This project's own state (which titles have been processed, which are
  skipped/failed, and why) is authoritative only for its own run history — a
  dated JSON-lines log plus a human-readable report, matching the
  Video-Library-Archiving/Jellyfin-Library-Integrity-Automation pattern.

## Architecture and data flows (proposed)

1. **Inventory pass (read-only).** Walk the four library roots via SSH
   read-only discovery (or the Jellyfin API, which already exposes
   `MediaStreams` per item) to build a list of titles with no English
   subtitle stream (embedded or sidecar). This reuses the same
   `MediaStreams` check already validated during the Plex-to-Jellyfin
   migration's own subtitle audit.
2. **Transcription.** For each candidate title, extract/read the existing
   audio track (via `ffprobe`/`ffmpeg`, already present and trusted in this
   lab per Video-Library-Archiving and Jellyfin-Library-Integrity-Automation)
   and run it through a local Whisper-family model to produce timestamped
   English (or source-language) text.
3. **Optional translation pass.** If a non-English subtitle output is wanted,
   either use Whisper's own translate-to-English mode, or a dedicated
   translation pass. Reusing the existing `aster-llama` text-LLM endpoint for
   a translation step is plausible in principle (it is already a
   bearer-authed, Lab-VLAN-only OpenAI-compatible endpoint) but is **not
   assumed here** — it competes for the same shared B60 GPU that Aster's
   sysadmin-advisor workload already uses, and that contention has not been
   measured. Recorded as an open decision below, not a design commitment.
4. **Sidecar write.** Write the result as `<video-basename>.<lang>.srt` next
   to the source video file — additive only, never overwriting an existing
   subtitle file of the same name (the tool must check for and refuse to
   overwrite any existing `.srt`/embedded subtitle before writing).
5. **Validation.** A spot-checked sample (a handful of titles, human-reviewed
   for actual transcription accuracy, not just "a file was created") is
   required before any unattended, library-wide run — see Milestones and
   Validation plan.
6. **Reporting.** Dated JSON-lines run log plus human-readable summary,
   matching the `video-archiver`/`jellyfin-integrity` `reports/`/`logs/`
   convention, retained outside Git (contains full local paths and titles).

### Open decision: which hardware runs Whisper

Whisper transcription is itself GPU/CPU-intensive (a 27B-parameter LLM's
worth of contention is not the comparison — Whisper models range from tiny
to large-v3, but even a mid-size model transcribing hours of TV audio is a
real, sustained compute job, not a trivial background task). This lab has
three distinct existing accelerators, none of which is presumptively "free":

- **TrueNAS's Intel Arc A380** (via the Jellyfin container) — already
  scheduled Mon–Sat 01:30 for Video-Library-Archiving's own transcode job.
  Running Whisper here means either sharing that same window (contention
  risk, unmeasured) or picking a separate window and confirming the A380
  isn't mid-job when Whisper starts.
- **LXC 110's Intel Arc Pro B60** (Proxmox host, Lab VLAN 70) — already
  serving `aster-llama.service`'s Qwen3.8-27B inference. Adding a
  Whisper workload here means either a new LXC on the same physical B60 (VF
  sharing already constrained per `Local-AI.md`'s BAR/passthrough findings)
  or accepting contention with Aster's own inference latency.
  `Local-AI.md` also documents that full-device VFIO passthrough of the B60
  is currently blocked by firmware BAR limits, which further limits how
  cleanly a second workload could be isolated on this card.
- **CPU-only, on a new unprivileged LXC on Lab VLAN 70** (the lab's
  conventional placement for new AI-touching services) — no GPU contention
  at all, but meaningfully slower per title; needs a real throughput
  measurement against the actual candidate-title count before assuming it's
  practical at library scale.

**This charter does not resolve this decision.** It is the single largest
open question blocking Milestone 1, and needs Jason's input: either accept
GPU contention with a named existing workload (and on which host), or accept
CPU-only throughput, before implementation starts. A capacity measurement
(one real title transcribed on each candidate path, wall-clock timed) belongs
in Milestone 1's discovery step regardless of which path is chosen.

### Open decision: translation path

Whether non-English/translated subtitle generation is wanted at all (Jason's
priority per the Purpose section is English-subtitle-for-TV first), and if
so, whether it reuses `aster-llama` (with the GPU-contention caveat above) or
runs entirely inside Whisper's own translate mode (lower quality for
non-English *output*, since Whisper natively translates *to* English, not
*from* it — translating *into* a non-English language needs a separate
model/step regardless).

## Privacy and security design

- All audio processing happens locally; no cloud speech-to-text or
  translation API is used, in keeping with the lab-ethos preference for local
  processing of private material (this is home video/TV audio, not
  public data).
- The tool needs read access to video files under the four library roots and
  write access only to create new sidecar `.srt` files in the same
  directories — no delete permission on any existing file, and no access to
  Radarr/Sonarr/Jellyfin write APIs.
- Any new service component (if placed on a new Lab VLAN 70 LXC) follows the
  established pattern: bearer-auth API if it exposes one at all, Lab-VLAN-only
  exposure, least-privilege filesystem access (read on media roots, write
  only to a scoped subtitle-output path).
- Run logs are retained outside Git (contain full local paths and titles),
  matching existing `video-archiver`/`jellyfin-integrity` practice.
- No credential, API key or secret is written to any subtitle file, log
  filename, or report content.

## Pre-start risk assessment

- **Objective, scope, exclusions, stream:** as above. Stream not yet chosen —
  recommend Stream M given the GPU-placement decision is unresolved and the
  first library-wide run's actual transcription quality is unproven.
- **Affected systems:** TrueNAS media roots (read + additive write only),
  whichever host/LXC ultimately runs Whisper, potentially `aster-llama` (LXC
  110) if the translation path is chosen.
- **Users/data:** Jason's video library audio content, processed locally only.
- **Current versions/dependencies/consumers:** none yet — no Whisper
  installation exists anywhere in this lab today; this would be a wholly new
  dependency, needing an explicit choice of implementation (see Milestones).
- **Confidentiality/secret-handling risk:** low — no credentials are
  generated by this workload beyond a possible new API key if the tool
  exposes its own API; existing key-handling conventions apply.
- **Availability/integrity/privacy/recovery risk:** the only mutation this
  project performs is creating new files. The worst-case integrity failure is
  a low-quality or garbled subtitle file being written and shown to a viewer
  — annoying, not destructive, and trivially reversible (delete the sidecar
  file). No existing file is ever at risk given the additive-only,
  never-overwrite design constraint.
- **Irreversible/destructive operations:** none by design. This is the
  primary reason this project is a comparatively low-risk proposal relative
  to, say, the duplicate-file-finder sibling project.
- **Expected auth/firewall/DNS/storage/external-service changes:** none
  expected beyond a possible new Lab VLAN 70 LXC (firewall rule scoped to
  that LXC reaching the media share read/write path) — no new external
  service, no public exposure.
- **Recovery checkpoint/rollback/abort:** rollback is deleting any sidecar
  file this tool created (tracked in its own run log, so exactly which files
  were written by this tool is always known). No checkpoint needed on the
  video files themselves since they are never touched.
- **Test strategy:** synthetic/disposable test clips first (known-transcript
  audio, to validate the Whisper pipeline's actual accuracy before touching
  real production titles), then a small spot-checked real-title sample,
  before any unattended run — same pattern as
  Jellyfin-Library-Integrity-Automation's synthetic-fixture-then-real-dry-run
  gate.
- **Likely service interruption:** none expected for Jellyfin/ARR services.
  A GPU-contention risk exists for whichever accelerator is chosen (see Open
  decision above) — potential latency impact on `aster-llama` or on
  Video-Library-Archiving's transcode job if scheduled carelessly.
- **Backup/Doctor/monitoring/NetBox/wiki/documentation impacts:** see
  integration checklist below.
- **Unresolved decisions requiring Jason's acceptance before Milestone 1:**
  1. Which hardware/host runs Whisper (TrueNAS A380 shared window, B60/LXC
     110 shared with Aster, or new CPU-only Lab VLAN 70 LXC) — see Open
     decision above.
  2. Whether the translation/non-English path is wanted at all for this
     project's first milestone, or deferred entirely.
  3. Which Whisper implementation (see Milestones — OpenAI's reference
     `whisper`, `faster-whisper`, or `whisper.cpp`) given none has been
     evaluated yet for this lab's actual hardware.

## Persistence plan

- Candidate-title inventory and per-title processed/skipped/failed status are
  recorded in a durable state file (JSON, schema-versioned) so a resumed run
  never reprocesses an already-completed title and never silently infers
  success from process absence, per the standard's persistence requirements.
- Runs are idempotent: a title with an existing English subtitle (sidecar or
  embedded) is always skipped, regardless of whether this tool wrote it.

## Milestones

All unchecked — nothing has been built.

### Milestone 1 — Discovery, implementation choice, and dry-run inventory

- [ ] Inventory the actual scope: query the Jellyfin API for `MediaStreams`
  across Movies/Shows/Archive Movies/Archive TV to get a real count of
  titles missing an English subtitle (embedded or sidecar) — replacing the
  single historical 5,678-episode TV measurement with a current number.
- [ ] Evaluate and choose a Whisper implementation (reference `whisper`,
  `faster-whisper`, or `whisper.cpp`) against the hardware-placement decision
  above, with a real measured wall-clock transcription time per title on the
  chosen path.
- [ ] Resolve the open hardware-placement decision with Jason (see Pre-start
  risk assessment) before writing any file.
- [ ] Dry-run only: produce a candidate list (no subtitle files written) with
  projected processing time for the full backlog at the chosen throughput.

### Gate

A real hardware/implementation choice is made and accepted by Jason, and a
dry-run candidate list plus realistic time estimate exists, before any file
is written.

### Milestone 2 — Supervised sample run and quality validation

- [ ] Transcribe a small, human-reviewed sample (a handful of titles across
  both Movies and Shows) and have Jason (or a documented equivalent) actually
  check transcription accuracy against the real audio — not just confirm a
  file was created.
- [ ] Confirm the never-overwrite behavior against a title that already has
  an English subtitle (should be skipped, not touched).
- [ ] Confirm Jellyfin picks up the new sidecar file correctly via a live
  library scan.

### Gate

Sample transcriptions are judged accurate enough to be useful by a human
reviewer, and the never-overwrite/Jellyfin-pickup behaviors are confirmed —
both before any unattended run is considered.

### Milestone 3 — Bounded unattended run (if approved)

- [ ] Define and get sign-off on a scheduling window that does not compete
  with Video-Library-Archiving's Mon–Sat 01:30 transcode job or with
  Jellyfin-Library-Integrity-Automation's Wednesday 03:00 job, on whichever
  host/GPU was chosen in Milestone 1.
- [ ] Add a per-run processing cap, matching the
  Jellyfin-Library-Integrity-Automation precedent, so a bug can't process the
  entire backlog unsupervised in one pass.
- [ ] Run unattended for a bounded initial period and review every generated
  subtitle log before extending the cap or the library scope.

### Gate

At least one clean unattended run reviewed, with no contention observed
against existing scheduled jobs.

### Milestone 4 — Documentation and closeout

- [ ] Record final tool location, config, schedule and report location in
  `docs/04-Operations.md`.
- [ ] Close out the integration impact checklist items below with actual
  evidence.

## Validation plan

- Functional: sample transcriptions reviewed for actual accuracy by a human,
  not just file existence.
- Security: confirm no write capability beyond new sidecar subtitle files;
  confirm no ARR API write calls are made.
- Failure/regression: confirm a bad audio track, corrupt file, or
  unsupported codec fails loudly and skips that title rather than crashing
  the run or writing a garbage file.
- Never-overwrite test: run twice against the same title and confirm the
  second run is a no-op.
- Performance/capacity: confirm the chosen hardware path's measured
  throughput makes the full backlog achievable in a reasonable number of
  scheduled windows, not an open-ended job.

## Observability and maintenance (integration impact checklist)

- **HomeLab Doctor** — add a check (e.g. `check_subtitle_generator`) reading
  the latest run log, matching the `check_video_archiver`/
  `check_jellyfin_integrity` pattern: warns on stale last-run age, fails
  loudly on a run with errors.
- **Monitoring/alerting** — covered via HomeLab Doctor; no separate
  Prometheus/Grafana metric proposed unless GPU contention with `aster-llama`
  turns out to need its own alert (open question, deferred to Milestone 1's
  measurement).
- **Backup and recovery** — the tool's own config/state (not the generated
  subtitles themselves, which are trivially regenerable) should be added to
  the existing backup pipeline (`scripts/backup/`) if the tool has any
  non-regenerable config; the generated `.srt` files are additive derived
  data, not backed up separately given they can be regenerated from source.
- **NetBox** — not applicable with reason: no new physical device; a new LXC,
  if chosen, is recorded the same way any other Lab VLAN 70 LXC is
  (NetBox is already the adopted inventory authority for Proxmox guests).
- **Human wiki** — add an operator page describing what the tool does, its
  sidecar-file convention, and how to spot-check/delete a generated subtitle.
- **Aster mirror/snapshot** — mirror this project document once accepted,
  same as other project docs, non-authoritative.
- **Operational reference and runbooks** — add to
  `docs/04-Operations.md` alongside the Video-Library-Archiving entry once
  implemented.
- **Repository documentation** — update this document's status and the
  portfolio table once accepted/implemented (portfolio table itself is
  maintained by someone else per this task's instructions).
- **Diagrams/rack records** — not applicable with reason: no physical
  hardware change; only a possible new LXC on existing Lab VLAN 70.
- **Homepage/service discovery** — not applicable with reason: this is a
  scheduled backend job with a report, not an interactive service, matching
  Jellyfin-Library-Integrity-Automation's own "not a dashboard" scoping —
  unless a decision is later made to expose a small status page, which is
  not proposed here.
- **Authentication/authorization** — a new dedicated API key (if the tool
  calls Jellyfin's API for `MediaStreams` inventory) follows the existing
  least-privilege, mode-600, not-committed-to-Git pattern used by
  `jellyfin-integrity`.
- **DNS, certificates and firewall** — not applicable with reason: no new
  external-facing endpoint; any new LXC stays Lab-VLAN-only per existing
  firewall policy for that VLAN.
- **Automation and schedules** — TrueNAS-native Cron Job or systemd timer
  (matching existing precedent), with the per-run cap and non-overlap lock
  required by Milestone 3.
- **Security inventory** — any new API key is recorded in the security
  inventory the same way `jellyfin-integrity`'s key is; no credential is
  ever placed in a subtitle file, log filename or report body.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## References

- [Plex-to-Jellyfin media migration — TV subtitle absence measurement](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
- [Video Library Archiving — subtitle/audio track-dropping design and A380 GPU evidence](<completed projects/Video-Library-Archiving.md>)
- [Jellyfin Library Integrity Automation — sibling project's dry-run/report/apply precedent](Jellyfin-Library-Integrity-Automation.md)
- [Local AI — B60 GPU capacity, BAR/passthrough constraints, aster-llama service](<completed projects/Local-AI.md>)
- [Aster Operations — aster-llama.service endpoint and model details](../Aster-Operations.md)
- [ARR Stack Operational Reference — canonical library roots and service authority](../ARR-Stack-Operational-Reference.md)
- [04-Operations.md — video-archiver operational details this project must not collide with](../04-Operations.md)
- [HomeLab Project Creation Standard](../Project-Creation-Standard.md)
