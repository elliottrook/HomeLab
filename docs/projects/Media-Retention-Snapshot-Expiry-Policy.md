# Media retention snapshot expiry proposal

> Status: Review design only — no snapshot deletion authorized
>
> Parent project: [Media retention and recall](Media-Retention-and-Recall.md)

## Why a separate decision is necessary

On 2026-11-06, `Media/data` had 13 named manual snapshots, oldest 2026-10-17.
The fresh retention pilot snapshot contained every one of 1,068 indexed movie
files and 6,329 indexed episode files. A ZFS snapshot retains a file's blocks
after the live path is deleted. The isolated M2 probe proved that deleting a
snapshot-covered file did not reduce dataset use until its snapshot was
released. `Media/data` has no scheduled snapshot task and no TrueNAS replication
task; the two-week, nonrecursive parent `Media` task does not expire these
checkpoints. The separate proposed Synology media backup was declined. Current
snapshot expiry is therefore manual and effectively indefinite.

At the measured roughly 2 TB/month intake, seven days of unreclaimed deleted
media could add about 0.47 TB to pool allocation; fourteen days about 0.93 TB.
The 60–62% band on today's 39.98 TB raw pool is about 0.80 TB. These are
planning figures, not a guarantee: intake, snapshots, compression and pool
metadata vary. No snapshot policy alone guarantees the band.

## Proposed policy

1. **Inventory and owner review.** Keep the 13 existing `Media/data` snapshots
   until their owner projects identify which rollback they still require.
   Record each name, creation time, dependency, restore proof and proposed
   expiry. Do not let the retention controller destroy snapshots.
2. **New recovery checkpoints.** Every future project-created `Media/data`
   snapshot needs an owner and a review date. Seven days after its bounded
   change passes recovery and household checks is the suggested first review
   point, **not an automatic expiry**. A checkpoint still needed for rollback
   remains protected, with a renewed review date and explicit reason.
3. **Permanent retention removals.** Before considering a snapshot-covered
   title, verify exact ARR/Jellyfin identity, all-user watch evidence plus
   retained playback logs, the year safeguard, subtitle/sidecar manifest and
   requestability. Show the owner a list of snapshots retaining its blocks and
   the effect of releasing them. Existing snapshots may also protect unrelated
   media and projects, so review the entire snapshot, not only that title.
4. **Explicit risk decision.** Removing a snapshot that is the last recovery
   copy of any deleted media, or weakening an accepted backup window, requires
   a new explicit decision under the HomeLab Project Creation Standard. Record
   the exact snapshot names and recovery alternatives before that decision.
   A blanket approval to remove all old snapshots is not assumed.
5. **One-at-a-time execution and measurement.** After approval, release only
   the named reviewed snapshot, check ZFS pool allocation and affected
   restore paths, then continue to the next. Abort on unexpected space change,
   active restore need, new snapshot owner, or incomplete evidence. Never use
   snapshot deletion as a hidden step inside an ARR media-delete batch.

## Interim automatic-retention behavior

The controller may automatically consider only files absent from **every**
retained `Media/data` snapshot, with all other candidate gates passing. A file
still covered by a checkpoint gets zero immediate reclaim estimate and remains
playable. At 60% with no safe reclaimable candidates, stop and alert; at 62%,
escalate capacity pressure without weakening recovery rules. The daily
read-only audit reports snapshot coverage and pool pressure while this policy
is reviewed.

## Open review packet

The 2026-11-06 read-only inventory below is a review queue, not an expiry list.
`used` is ZFS's current *unique* space for one snapshot; the amount reclaimed
after deleting several snapshots is not the sum of these values. Recheck the
properties and dependencies immediately before any proposed release.

| Owner to confirm | Snapshot names | Created | Current unique use |
|---|---|---|---:|
| Music backfill | `pre-lrclib-backfill-20261017T071932Z` | Oct 17 | 92.4 GiB |
| Music genre consolidation | `music-genre-consolidation-20261020T225539PDT` | Oct 20 | 10.5 GiB |
| Media lifecycle | `pre-media-lifecycle-20261104` | Nov 4 | 21.7 GiB |
| Media reconciliation | `pre-media-reconcile-20261106` | Nov 6 | 695 KiB |
| Sonarr ownership pilots | `pre-sonarr-ownership-pilot-20261106`, `pre-sonarr-watched-pilot-20261106`, `pre-sonarr-resume-pilot-20261106`, `pre-sonarr-batch-a-20261106`, `pre-sonarr-batch-b-20261106`, `pre-sonarr-batch-c-20261106`, `pre-sonarr-series73-20261106`, `pre-sonarr-series2-20261106` | Nov 6 | 0–815 KiB each |
| Retention M3 pilot | `pre-retention-pilot-20261106` | Nov 6 | 583 KiB |

Each owner must confirm rollback closure and affected media before a named
expiry proposal. The proposal must include alternate recovery copies and a
bounded sequence. No off-pool `Media/data` replication was found in the live
TrueNAS task inventory on 2026-11-06.
