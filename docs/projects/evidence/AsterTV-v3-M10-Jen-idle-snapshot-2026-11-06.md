# AsterTV v3 M10 — Jen low-spec idle snapshot

Date: 2026-11-06

State: read-only initial evidence; performance gate remains open

## Scope and safety

The deployed low-spec client at `192.168.1.180` identified itself as
`AsterTV-Jen`. Direct read-only SSH gathered host counters and a local Kodi
JSON-RPC `Player.GetActivePlayers` query returned an empty list. No page was
opened, no input was sent, no playback started, no file or service changed and
the display was not moved.

## Point-in-time result

- uptime: 13 hours 46 minutes;
- load average: `0.19 / 0.18 / 0.17` at the opening sample;
- CPU at the bounded `top` sample: 97.6% idle, 1.2% user, 1.2% system;
- temperature: 27.8°C;
- memory: 7,657 MiB total, 1,099 MiB used and 6,558 MiB available;
- swap: absent, with no observed swapping;
- Kodi resident memory: 754,288 KiB (about 737 MiB), 54 threads;
- Kodi service: active, zero systemd restarts;
- storage: 115.8 GiB total, 975.8 MiB used, 114.9 GiB available (1%);
- active Kodi players: none; and
- Intel GPU frequency counters: 1,100 MHz current/actual, 1,150 MHz RP0 and
  200 MHz RPn at the instant sampled.

The one-process `top` row reported Kodi at 9.8% CPU while the whole-host sample
remained 97.6% idle. These clocks use different sampling semantics, so neither
is promoted to a sustained budget result.

## Interpretation and remaining gate

The sample shows ample idle host memory, storage and thermal headroom, an active
non-restarting Kodi service and no playback conflict. It does not measure page
latency, artwork latency, sustained network traffic, camera cost, speech
latency, playback decoding or repeatability. It therefore narrows the M10
performance work but does not close it. Any connected playback or UI movement
still requires the named idle/display gate already recorded in the project.

The repository now includes `low-spec/measure_idle.py`, a target-bound sampler
that checks for no active player before and after its bounded 2–30 second
window. It emits only aggregate CPU, memory, Kodi RSS, temperature, GPU clock,
storage and network-rate data. Three focused tests prove the parsers, target/
duration gates and absence of item/title/path/playback-control calls. The full
M10 gate passes 63 test files with zero page or operations-readiness failures.

The sampler was then streamed over the existing SSH session without installing
or retaining a file on Jen. Its 10-second run passed both idle checks and
reported 3.93% aggregate CPU used, 6,726,496 KiB available memory, 754,292 KiB
Kodi RSS, 27.8°C, 200 MHz actual GPU clock, zero swap, 3,253.8 B/s received and
71.9 B/s transmitted. No active player appeared during the interval. This is a
repeatable idle datum, but sustained and interactive workloads remain open.
