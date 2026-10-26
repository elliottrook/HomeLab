# Stream A F4/F5 transaction source candidate

Status: **SOURCE-ONLY / NO LIVE AUTHORITY**

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

This candidate has no CLI, filesystem write, command runner, network access,
systemd action, lease operation or model request. A later reviewed root entry
point must collect the fixed sources, revalidate exact current-cycle bytes and
write all three files as one bounded fail-closed transaction. Installation,
live evidence production and F6 remain separately gated.
