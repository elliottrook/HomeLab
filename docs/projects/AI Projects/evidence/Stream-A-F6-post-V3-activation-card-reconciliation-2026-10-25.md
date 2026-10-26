# Stream A F6 post-V3 activation-card reconciliation — 2026-10-25

Result: **NO-GO FOR ACTIVATION CARD; INACTIVE INSTALL REMAINS VALID**

After the V3 composition installation passed, Stream A compared the two
existing effectful F6 cards with the installed target. No service or timer was
enabled or started and no receipt, lease, lock, consumer stop or model request
was produced.

The older `STREAM-A-EVALUATION-LEASE-EFFECTFUL-F6-POST-F2-ACTIVATION-CARD-20261025.md`
is superseded: its lease, adapter, entrypoint and restore-observer hashes refer
to earlier installed revisions, and it names candidate-G rather than the
current candidate-H workload.

The later candidate-H card matches 15 of its 16 listed installed file hashes.
Its restore-observer pin is stale:

- card: `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3`;
- installed V3: `20d977681452eb89cbda7b0417de02b4caed279f234e7b568a072638bb736fb2`.

The card also predates the installed V3 composition and therefore does not pin
the other eight new host composition files or the four guest paths. It still
says a later source revision must provide the orchestrator, although that
composition is now installed inactive.

Before any F6 activation approval, the platform owner must issue one revised
card that:

1. supersedes both earlier effectful cards;
2. pins the exact current installed packet, including all 13 V3 paths and the
   unchanged lease/watchdog/owner/wrapper/unit dependencies;
3. names candidate-H and the staged M3 calibration as the only serial
   workloads;
4. binds the fresh F3, F4 and F5 artifacts for one cycle; and
5. retains the existing 90-minute deadline, 15-minute recovery reserve,
   no-retry rule and independent recovery/postcheck contract.

The V3 installation itself remains accepted and inert. This reconciliation
prevents a stale card from being used as live authority.
