# ARR English-audio reviewed removal evidence — 2026-10-23

The full-library stream audit found 32 files without an English audio stream.
Jason clarified that genuine foreign originals are acceptable when accompanied
by English subtitles. The reviewed action therefore removed only the 25 files
whose ARR metadata identifies the work's original language as English.

No new snapshot was created, by explicit direction. The files were deleted
through Sonarr/Radarr so their records became missing while remaining monitored.
No search or grab was started during removal. Exact source-local manifests and
results are root-private on TrueNAS at
`/root/arr-english-removal-20261023T175232Z`.

## Removed and monitored as missing

| ARR | File ID | Title / episode |
|---|---:|---|
| Radarr | 1795 | Blue Crush 2 |
| Radarr | 83 | Che: Part One |
| Radarr | 85 | Che: Part Two |
| Radarr | 1893 | Godzilla |
| Radarr | 1923 | I Can Only Imagine 2 |
| Radarr | 1695 | Underworld: Evolution |
| Radarr | 1233 | Wreck-It Ralph |
| Sonarr | 5395 | 12 Monkeys S04E11 |
| Sonarr | 6585 | Friends S05E24 |
| Sonarr | 6538 | Gentleman Jack S02E02 |
| Sonarr | 6590 | Gentleman Jack S02E03 |
| Sonarr | 6537 | Gentleman Jack S02E04 |
| Sonarr | 6535 | Gentleman Jack S02E05 |
| Sonarr | 6534 | Gentleman Jack S02E06 |
| Sonarr | 6589 | Gentleman Jack S02E07 |
| Sonarr | 6552 | Gentleman Jack S02E08 |
| Sonarr | 7961 | Sweet Tooth S02E08 |
| Sonarr | 6738 | The Expanse S01E10 |
| Sonarr | 7963 | The Great S03E10 |
| Sonarr | 8468 | Sense8 S01E02 |
| Sonarr | 8469 | Sense8 S01E03 |
| Sonarr | 8471 | Sense8 S01E05 |
| Sonarr | 8474 | Sense8 S01E08 |
| Sonarr | 8476 | Sense8 S01E10 |
| Sonarr | 8478 | Sense8 S01E12 |

Total removed: 25 files, 33,656,430,184 bytes (31.34 GiB). All 25 parent
records validated as monitored and missing. Sonarr's queue remained 40 and
Radarr's remained zero before and after the removal.

## Retained foreign originals

| Title | English subtitle status | Result |
|---|---|---|
| A Man Called Ove | Embedded English | Retained; added to Radarr as monitored movie 993/file 2103 |
| Sweet Bean | Embedded English | Retained |
| The Mysterious Gaze of the Flamingo | Embedded English | Retained |
| Tokyo Story | Embedded English | Retained |
| Dark S01E04 | Embedded English | Retained |
| Parasite | Not identified | Retained; subtitle correction pending |
| The Lunchbox | Not identified | Retained; subtitle correction pending |

Final checks found Sonarr and Radarr running healthy with zero application
health records. Every retained file still existed. The accepted profile policy
on all 13 profiles remains Original Audio +100, English Audio +50, minimum 100,
with upgrades disabled.

## Targeted reacquisition

After a separate approval, the 25 monitored-and-missing records were submitted
for bounded searches under the accepted profile policy. Sonarr accepted
`EpisodeSearch` command 274893 for the 18 episode IDs; Radarr accepted
`MoviesSearch` command 274798 for the seven movie IDs. The seven retained
foreign originals were not included. Imports must still be checked with direct
stream inspection because release parsing cannot prove the downloaded audio.

Both commands completed. All 25 targets received a result: 12 Monkeys S04E11
imported first, the other 17 Sonarr episodes remained queued, and all seven
Radarr movies remained queued. Every queued candidate had custom-format score
150 and parsed English audio. Direct `ffprobe` of the first imported replacement
confirmed French and English E-AC-3 tracks. The remaining imports still require
direct stream verification when they complete.
