# F2 archive timing — admission gap after disabled installation

**October 16, 2026, Vancouver.** The corrected seven-path common-exclusion
candidate is [installed but disabled](Common-host-exclusion-disabled-install-v2-2026-10-16.md).
That proves target-Linux imports, hashes and synthetic lock behavior. It does
not make the 01:10 archive scan safe to start unattended or mark F2 complete.

The next-cycle read-only run needs the platform owner to release a separate,
reviewed observer path with all of these checks before its first archive:

1. **Competing control paths.** The old manual `local-ai-lease acquire
   --light` bypasses the new advisory directory lock. An unattended scan
   requires a verified, bounded way to exclude that route for the scan window
   or a compatible updated controller. A statement that no one plans to use it
   is not an enforced admission gate. No stateful lease may already exist.
2. **Backup and load.** The exact 00:30 Proxmox job and 01:00 TrueNAS task 1
   must have completed successfully for the current cycle. Resolve the exact
   current 104/110/116 volids and identities; reject stale or replaced
   archives. Refuse a competing backup, pull, maintenance operation or
   unsuitable host load, and recheck these conditions immediately before the
   first `zstd` process. The advisory lease lock does not cover backup jobs.
3. **Hard deadline.** Start only in the 01:10–01:19 Vancouver window. Enforce
   one external wall deadline at the earlier of 20 minutes after actual start
   and 01:40. Kill the scanner and any child `zstd` if it reaches the limit.
   Keep per-file limits 120/900/120 seconds for 104/110/116, sequentially;
   do not start a file unless the remaining budget accommodates it and all
   remaining bounds. Preserve at least 20 minutes before the 02:00 pull.
4. **Read-only output.** The observer must suppress the producer's receipt
   writer, emit only archive identity/size/ctime, test times and exit status,
   and produce no trusted F3/F4 admission claim. A partial, timed-out or
   otherwise uncertain run is NO-GO, never a success inferred from scheduler
   state. Keep candidate effect flags and timers off until separately reviewed.

These controls require an offline fake-runner test, target-Linux bounded
termination test and fresh source/hash review. Only then should Jason receive
one exact approval request for the read-only F2 run. If that gate misses its
start window, skip the cycle; do not shorten checks to make the clock.
The platform owner owns the host release. Stream A owns the resulting timing
evidence and will not start the scan from this disabled-install approval.
