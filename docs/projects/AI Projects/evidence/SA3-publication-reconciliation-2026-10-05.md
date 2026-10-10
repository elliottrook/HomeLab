# Publication reconciliation checkpoint

Status: local merge reviewed; remote write not yet approved.

Fetched Forgejo main at `ec6ebd29c572f61aade8a91c1bff863645fd3acc` and merged
locally with the completed trial at `d18b666`. Both histories are preserved;
no rebase, force-push, deployment or remote mutation. Other projects' changes are
inherited unchanged from Forgejo, not new work performed by this task.

Two conflicts were resolved: preserve both dated project evidence logs; reconcile
the intake test with the twelve previously reviewed development records while
retaining the newer contract's repair-scope, postcheck and timing requirements.
Those twelve records lack the three newer fields. Their original contents, source
references and human-review attribution are preserved without inventing extra
reviewed facts. The intake status is now `reviewed_development_requires_extension`.
Validation intentionally blocks using that incomplete intake as evaluation input.
The custody template now also requires source provenance. Tests explicitly verify
this incomplete state, and use synthetic additions only to test a complete fixture.

All 50 local evaluation tests passed after reconciliation. No conflict markers or
whitespace errors remain. This does not revalidate live service deployments or
turn the intake into a complete independent test corpus. Existing whole-file
adaptive source pins were not silently refreshed; newer inherited source changes
may require a separate equivalence review before those older experiments rerun.

The proposed push is the reviewed merge HEAD to Forgejo `origin` main, normal
fast-forward only, with a fresh remote-ref check first. If main advances again,
reconcile before pushing. Verify Forgejo and its automatic GitHub mirror afterward;
do not push directly to GitHub. Repository AGENTS.md requires explicit approval
for this remote write. Publishing evaluation source/evidence is not deployment.
