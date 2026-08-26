# Repository instructions

## Repository authorization

Codex may inspect, edit, test, and create local commits in this repository
without requesting additional approval when those actions are within the
user's requested task.

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
