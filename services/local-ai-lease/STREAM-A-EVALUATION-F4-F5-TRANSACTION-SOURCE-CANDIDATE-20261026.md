# Stream A F4/F5 transaction source candidate

Status: **SOURCE CANDIDATE / NO LIVE AUTHORITY**

The pure builder `stream_a_evaluation_f4_f5_transaction.py` closes the
cross-artifact construction gap identified after the October 27 F3 activation.
It accepts only already trusted content-free inputs and emits canonical F4, F5
and admission bytes that bind:

- one same-local-date F2 result and unchanged F3 receipt;
- one fixed `stream-a-evaluation-<date>-<nonce>` identity and generation `1`;
- the retained archive digest and verified LXC110 mirror identity;
- a fresh healthy production, schedule, accepted model/backend/unit and
  metadata-authentication observation; and
- the frozen candidate-H and final M3 identities already enforced by the
  admission library.

The Stream A F4 artifact records `heartbeat_alive=false` before F6. This is
permitted only through the distinctly named Stream evidence contract. Generic
pre-acquire/controller validation remains unchanged and requires the live
independent watchdog before any consumer effect.

The root entry point `stream_a_evaluation_f4_f5_root.py` now supplies that
separate collection and publication boundary. It:

- runs only as root and uses the fixed current local date;
- refuses to run before 03:05, before all three TrueNAS tasks have succeeded,
  or while either the whole-host or Stream A evaluation lease has state or a
  lock;
- opens the exact F2 and F3 files with no-follow, single-link, owner/mode and
  size checks, cross-binds their three rows, and verifies the retained archive
  receipt against the current Proxmox inventory and archive identities;
- uses the dedicated TrueNAS schedule observer to verify the fixed 01:00,
  02:00 and 03:00 jobs and the exact current-cycle LXC110 mirror;
- collects the fixed control-plane, production, GPU, schedule, model, binary,
  unit and metadata-authentication observation without stopping anything;
- rereads F2/F3 before publication and rejects any byte or receipt drift; and
- stages all three mode-`0600` artifacts, publishes F4 then F5 and admission
  last with no-replace hard links, and removes its own partial publications on
  a handled failure. Admission is the final acceptance boundary, so a process
  crash before it cannot expose a complete accepted set.

The wrapper `stream-a-evaluation-evidence` fixes both installed Python roots
and accepts no arguments. The entry point prints only content-free status,
lease/admission identity and artifact digests.

The writer still does **not** acquire a lease, create a lock, stop or restart a
service, enable a timer, call a model, change a schedule, or authorize F6. An
inactive hash-pinned installation and one live evidence-production invocation
remain distinct approval gates.
