# M3 NLU staged-custody validator boundary — 2026-10-25

> Result: **PASS OFFLINE — NO STAGING EFFECT**

The existing packet validator proved source bytes but did not itself enforce
the final LXC directory owner, modes or exact absence of output files. The
inactive staging card listed those checks, but leaving them as shell-only
inspection would make the live result harder to reproduce.

`nlu_calibration_stage_manifest.py` now provides one exact staged-directory
validation path. It requires:

- a root-owned, non-symlink directory at mode `0700`;
- exactly the ten frozen input names and no `run.json`, journal or extra file;
- root-owned regular non-symlink inputs at mode `0600`; and
- every opened-file SHA-256 from the unchanged staging manifest.

The validator source SHA-256 is now
`8ea9daf47793aaeed0f2c475b4475cc1873173a9abc65089049e9c5bae86889e`.
Seven focused validator tests cover the passing directory plus bad directory
mode, bad input mode, extra output, missing/changed input and symlink cases.
The combined runner/staging suite passes 21/21 and the complete dependency-free
NLU suite passes 115/115.

The ten-file packet and its manifest are unchanged at 93,612 bytes and SHA-256
`357b4e3d5514fe32b1509ac27f9eac3940edb0635db3a5008b4f29fc4f124a00`.
Nothing was copied to LXC110 and no lease, key read, model request, score,
threshold or route followed.
