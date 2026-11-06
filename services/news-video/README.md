# Aster News video presenter

This directory holds the renderer-neutral identity and annual ageing contract
for the proposed Aster News video presenter.

The accepted identity anchor is immutable. The 2026 modern appearance and its
ten-look wardrobe are accepted baselines. Beginning on 2027-11-06, the annual check
advances Aster's apparent age by one year and prepares a tightly constrained
identity-preserving render request. The same request includes a mandatory review
of current British male news-presenter dress and UK tailoring before proposing
a replacement ten-look collection, plus an annual studio review bound to the
then-current accepted Aster and News Digest brand assets.

Daily wardrobe selection is deterministic and local: every date maps to one
look, every ten-day cycle uses all ten looks once, and adjacent dates never
repeat. This gives a random-looking rotation without a timer, mutable state or
an AI call. Select today's outfit with:

```sh
python3 wardrobe.py --date 2026-11-06
```

The numbered review boards are stored with the source looks as
`docs/assets/news-video/wardrobe/aster-wardrobe-board-01-05.png` and
`aster-wardrobe-board-06-10.png`. The selector always returns the individual
pinned source image, never the review-board derivative.

The accepted 2026 studio key frame is stored at
`docs/assets/news-video/studio/aster-studio-2026-candidate-v3.png`. It retains
the AsterTV set but uses a conventional horizontal rectangular story monitor;
that geometry is now an annual-review invariant. Its profile
pins the reconciled AsterTV r7 release and verifies the skin colour XML,
limestone background, jade focus surface and Aster Media material reference
inside that archive. The earlier blue/cyan app-icon interpretation is retained
only under `studio/rejected/` as negative evidence, while the curved-monitor v2
is retained under `studio/superseded/`. A changed AsterTV authority
fails verification until the studio manifest is deliberately reconciled;
annual reviews must derive the studio from the accepted AsterTV release current
at that time, not copy the 2026 palette blindly.

Prepare the non-rendering annual studio brief with:

```sh
python3 studio.py --date 2027-11-06 --prepare
```

Run the non-rendering status check with:

```sh
python3 presenter_age.py --date 2027-11-06 --prepare
```

The command verifies both pinned source images and prints the candidate request.
The wardrobe review requires evidence no more than 90 days old from at least
two official UK broadcaster sources and two current UK tailoring sources.
The studio review also requires current broadcast-set evidence no more than 90
days old. None of these commands calls an image model, schedules work or
activates an output. An actual
renderer must remain separately governed by its provider, Lab Hours admission
where applicable, and explicit visual acceptance.

## Synthetic motion pilot

The current renderer candidate is
`docs/assets/news-video/pilot/aster-lipsync-motion-pilot-v3.mp4`. It uses the
accepted Mac/Qwen Aster voice and the accepted studio image; its exact
inputs, model revisions, parameters, hashes, measured CPU time and limitations
are recorded in `pilot/pilot_manifest.json`. This SadTalker pass supplies lip,
eye and restrained head/upper-body micro-motion. It does not create independent
arm or hand gestures, does not establish an accepted random-motion policy and
is not production enabled. Jason accepted the v1 facial lip synchronization
but rejected its obsolete Kokoro audio; v1 remains only as superseded evidence.
The v2 voice and lip timing were otherwise accepted, but its name sounded like
“aRster” and its moving head separated visually from the static torso. V3 sends
the model-facing spelling “Asster” while preserving written “Aster”, and uses
SadTalker's recommended full-image `--still` mode to lock the original head
pose. Jason accepted the v3 “Asster” pronunciation; the head/torso correction
still awaits an explicit visual verdict.

Measured v3 throughput makes SadTalker a test renderer only: a 15-minute digest
is estimated at 42.93 video-render hours and a 20-minute digest at 57.25 hours,
plus 12.97–17.30 minutes for accepted Qwen speech. Reproduce the calculation
with `python3 capacity.py 15 20`. A twice-daily service therefore requires a
different lip-sync architecture and a measured production-shaped benchmark.
