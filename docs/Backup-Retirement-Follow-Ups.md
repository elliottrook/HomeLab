# Backup retirement follow-ups

Owner: Jason. Recorded 2026-09-22 while closing the backup redesign and DS220j
retirement. These items are not claims of completed disk reuse or future
retention-cycle validation.

## Removed DS220j disks and preserved data

Jason confirms the disks have been removed and have not been redeployed.
Their serials, current location, readability and current contents were not
verified during closeout. The existing preservation hold on the approximately
5.7 TB `GoWest_1.hbk` Media Backup continues. Do not erase either disk based on
the retirement project's completion status.

- [ ] Identify both disks by model, serial and capacity; record their location
  and read-only SMART results before deciding whether reuse is worthwhile.
- [ ] Reverify the legacy backup's presence/readability before any destructive
  step. Jason must separately choose preservation/migration or explicitly
  approve discarding it.
- [ ] If reuse is wanted, choose a supported topology under the
  [TrueNAS expansion project](projects/TrueNAS-DIY-SAS-Expansion.md), validate
  the disks and obtain exact per-action wipe/pool-change approval. Do not
  assume these disks are the six new 4 TB drives being tested separately.

## Capacity and retention

- [ ] Resolve the Media capacity alert through the separately active TrueNAS
  expansion work. On September 22 the pool was ONLINE, 92% allocated with
  approximately 978 GiB available to datasets. Jason is testing six new 4 TB
  disks; no new capacity is counted before pool membership and validation.
- [ ] After October 1, verify the first scheduled `backup-monthly` snapshot.
  Weekly and daily scheduled snapshots have already run; daily pruning is
  observed. Eight-week and six-month pruning need their real retention windows.
- [ ] Review the manual `backup-daily-2026-09-02_17-15` snapshot if cleanup is
  desired. It remains outside the normal 05:30 scheduled series, has no holds,
  and uses approximately 368 KiB uniquely. Closeout did not delete it.

## Optional later decisions

- Legacy IDrive `mini-atlas-backups` bucket disposal remains a separate explicit
  decision. No legacy objects or credentials were deleted during closeout.
  The prior accepted risk concerning its exposed credential is unchanged.
- Immich/family-cloud services remain on `gowest`; no migration is authorized
  or required by retirement. The September 22 spot-check showed load
  0.20/0.23/0.18, 5,166 MiB available RAM and 14% filesystem usage. This is not
  the proposed representative-week measurement. Collect that evidence before
  proposing a future move; no such measurement or move is claimed complete.

## Knowledge and synchronization

Aster's deployed operational snapshot was updated after explicit approval:
five corrected reference pages, 1,823 source records verified, all 1,796 derived
entries preserved. Retirement/retention/HA retrieval probes passed before and
after atomic activation. Human-wiki vendor manuals remain valid historical
hardware references; they were not deleted or regenerated.

The two local repository commits require normal Forgejo synchronization;
HomeLab's configured GitHub protection mirror is verified read-only afterward.
No direct GitHub push is part of this closeout.
