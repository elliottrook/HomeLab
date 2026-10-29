# SA2 breadth v1 race NO-GO and v2 correction — 2026-10-28

## V1 result

**NO-GO; FULL BOUNDED ROLLBACK COMPLETE.** The approved v1 installation
reached healthy LXC source, a working sanitized log publisher, an active timer
and one healthy Aster restart. Two fresh Doctor collectors then overlapped.
Both remote writers used the same `latest.json.new`,
`aster-inference.json.new` and `diagnostic-catalogue.json.new` paths.

One writer moved the other's aggregate staging file before its `chmod`, causing
that writer to fail with `FileNotFoundError`. The surviving final state mixed:

- aggregate SHA-256 `eb724c4c…92fc`, generated at
  `2026-10-29T03:25:44.875188Z`;
- sidecars from run `15cf3fd531ae432ba1c0b532a13f9473`, generated at
  `2026-10-29T03:25:44.875076Z`;
- both sidecar `source_report_digest` values differed from the installed
  aggregate digest.

The fixed consumers rejected that pair, so no incorrect typed evidence became
usable. The release card required rollback on publisher failure. The new timer
was disabled and removed, the seven LXC additions were removed, both LXC
replacements and all three Mac replacements were restored, the Mac catalogue
module addition was removed, and Aster restarted healthy on its exact
predecessor. Llama remained PID `61089` with zero restarts. The root-only Mac
and LXC checkpoints and the failed mixed evidence were preserved.

## V2 correction

The corrected remote publisher:

1. fully decodes and validates the aggregate and both optional sidecars before
   touching installed evidence;
2. opens a root-owned, single-link `.publisher.lock` without following links;
3. holds an exclusive `flock` across the complete three-file transaction;
4. creates a unique same-directory temporary file for each target, flushes and
   fsyncs it, applies exact custody, then atomically replaces the target; and
5. commits the aggregate last, so a racing reader safely rejects any interim
   digest mismatch and the final generation is coherent.

A regression launches two writers concurrently for four successive pairs and
requires the final aggregate, schema-2 sidecar and schema-3 catalogue to share
one digest, run ID and generation time after every pair. It passes locally and
under LXC104 Linux. The corrected manifest is
`sa2-breadth-evidence-v2-20261028`, SHA-256
`2d744a01fc965ee826ac88a636711c758f03c399295e0cc05faafda97b269713`.

V2 is source-only. It needs a new exact deployment approval because the Mac
builder digest changed; it retains the same four-Mac/nine-LXC target boundary,
one Aster restart, one log timer and no model/routing/repair change.
