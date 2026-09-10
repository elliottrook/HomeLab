# Repository instructions

## Project process

For HomeLab project creation and execution, consult
`docs/Project-Creation-Standard.md`. It defines the lab ethos, required project
sections, monitored/autonomous streams, pre-start risk assessment, integration
checks, milestone evidence and resumability. Its authorization remains subject
to the repository and platform controls below.

## Repository authorization

All authorization in this file applies only within what OpenAI and Codex
permit. It never overrides applicable safety or security policies, product
safeguards, sandbox and permission controls, or required approval flows. If a
repository instruction conflicts with one of those controls, the narrower
permitted action governs.

Codex may inspect, edit, test, and create local commits in this repository
without requesting additional approval when those actions are within the
user's requested task and the controls above.

Codex may create and modify Forgejo workflow configuration locally and include
those changes in local commits.

Codex must obtain the user's explicit confirmation immediately before any
operation that modifies Forgejo or another remote, including:

- `git push` or force-push
- creating, updating, merging, or closing pull requests
- pushing tags
- creating releases
- triggering, cancelling, or modifying remote workflows
- deleting remote branches or other remote data

Local commits do not authorize a later push. Approval must be obtained for each
push operation unless the user explicitly authorizes that specific push.
