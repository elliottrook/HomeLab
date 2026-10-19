# D4 development-corpus extension draft — 2026-10-19

Status: **offline draft; requires Jason review; not evaluable**

The existing 12 historical development incidents preserve Jason's reviewed
symptoms, evidence limits, permitted advisory outcomes and forbidden effects.
They intentionally lacked three fields required by the current evaluation
contract: bounded repair scope, expected postcheck and latency protocol.

`sysadmin-incident-development-extension-draft-v1.json` adds proposals for
those three fields without changing any reviewed field. It labels Codex as the
draft author and expressly prohibits treating the extension as Jason-reviewed,
a holdout, a qualification result or a promotion gate. The common timing rule
measures frozen-evidence handoff to terminal advisory output, separates
completion, abstention, invalid output and timeout, and excludes evidence
collection time.

The draft and provenance tests pass locally. No incident was sent to a model;
no live evidence, tool, credential or permission was used. The canonical
intake remains unchanged. Jason's eventual review can accept, edit or reject
each proposed field before the development corpus becomes evaluable.
