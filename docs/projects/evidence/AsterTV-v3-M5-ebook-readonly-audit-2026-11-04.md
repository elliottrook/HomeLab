# AsterTV v3 M5 eBook narration read-only audit — 2026-11-04

## Result

The current narration backend is healthy but deliberately sentence-timed; it
does not yet implement the v3 single-word follow-along requirement. The earlier
Whisper experiment was correctly not promoted. A separate scheduling defect
was also found: the Proxmox EPUB scheduler checks for an empty Lab Hours window
but does not reserve a registered, hash-pinned workload or acquire the required
whole-host lease and shared operation lock. No narration, alignment, booking,
timer or live reader state was changed during this audit.

## Current reader and queue

- Aster Speech remains LXC 116. Its narration worker and worker timer are
  inactive/disabled; the read-only catalogue monitor timer is active.
- The queue contains 167 generations: 160 queued and seven ready. There are no
  currently failed rows; one queued row retains `suspended` as its last failure
  code. Historical failed-output directories remain as recovery evidence and
  were not removed.
- Every ready generation uses the canonical Aster voice: Kokoro ONNX,
  `bm_daniel`, `en-gb`, speed `0.95`, 24 kHz mono Opus.
- The pinned cleanup implementation is
  `/opt/epub-narration/vendor/digest_text.py`, SHA-256
  `0476a393afd237833835b8e5499f64250bfc5e382a1603b94803cb99e7a350b9`.
  It retains the accepted Markdown, URL, currency, dotted-abbreviation, number,
  Roman-numeral and Aster pronunciation corrections. The ready manifests pin
  that same cleanup contract.

## Why follow-along is sentence-sized

This is not merely a stale UI setting. Four independently enforced contracts
currently require `sentence-sample-index`:

1. the renderer emits sentence/clause units and sentence sample ranges;
2. the ready-generation publisher rejects any other timing level;
3. the Aster Books loader accepts only the sentence timing schema; and
4. the Kodi reader highlights each accepted source-character cue as one span.

Consequently, adding word records to a side file would not fix the reader; the
versioned generation schema, renderer, publication gate, loader, progress-safe
reader and their rollback tests must move together. Existing sentence
generations must remain valid as the fallback.

## Earlier word-alignment evidence

The retained harness at
`/var/lib/aster-speech/word-alignment-harness-20261026` used locally cached
`faster-whisper` 1.2.1 / CTranslate2 4.8.2 models and requested word
timestamps. Its 64.174-second synthetic canonical narration trial measured 161
words in 5.729 seconds but failed `alignment-time`: at least one word lacked a
finite measured interval. The adapter intentionally refuses to interpolate or
invent missing timing, then also requires exact source token count and text.
That is the correct fail-closed behavior for a feature described as accurate
single-word follow-along.

The cached Whisper models and benchmark virtual environment remain present,
but no forced-aligner stack such as WhisperX, wav2vec2 alignment or Montreal
Forced Aligner is installed. No model was loaded or executed in this audit.

## Scheduler compliance defect

The enabled Proxmox `epub-narration-scheduler.timer` invokes
`/usr/local/libexec/epub-narration/schedule_worker.py`, SHA-256
`f427305951ef7415f0eb907a73200afd4a858e19e6fe14327f018f59674f92f2`.
It takes its own scheduler flock and calls `aster-lab-hours check-window` for a
two-hour run plus fifteen-minute recovery period. If clear, it starts the LXC
worker directly.

It does **not**:

- name a workload registered in `lab_hours_workloads.py`;
- create or claim a Lab Hours booking for the complete window;
- acquire the whole-host local-AI lease; or
- acquire `/run/local-ai-lab-operation.lock`.

No EPUB workload is currently present in the registered workload catalogue.
The timer is therefore not an admissible way to resume narration under the
current Lab Hours rules. At audit time it was failing closed with exit status
75 because the authoritative ledger reported overlapping reservations; the
LXC worker stayed inactive. A clear ledger window would nevertheless allow the
noncompliant direct start, so this needs a bounded live correction before any
backlog processing resumes.

## Required next gate

The next implementation slice must be separately authorized because the
current `SA-M5N-JEN` envelope explicitly excluded eBook TTS/timing and live
scheduler changes. The safe sequence is:

1. checkpoint and stop/disable only the noncompliant Proxmox scheduler timer;
2. register an immutable EPUB narration/alignment workload with complete
   dependency hashes, fixed command, bounded runtime and recovery reserve;
3. route it through authoritative booking, whole-host lease and shared-lock
   acquisition, with a fail-closed immediate recheck;
4. benchmark at least one real canonical narration chapter using measured
   word timing, retaining sentence timing on any missing, mismatched or drifting
   word; and
5. version the generation/reader schema and test old sentence generations,
   resume state, interruption, rollback and listening quality before any
   catalogue promotion.

No execution window is proposed here. The authoritative ledger must be checked
for the complete execution plus recovery window only after the workload is
registered and immediately before a reservation is created.
