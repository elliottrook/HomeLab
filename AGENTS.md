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

For an approved Stream A project, routine read-only LAN discovery and
validation must run without conversational confirmation. Invoke read-only SSH,
HTTP and Git queries as standalone commands so their scope remains recognizable
to the sandbox; do not bundle them with mutations or unrelated shell segments.
The workspace Codex configuration enables sandboxed network access for this
purpose and grants write access only to the named sibling knowledge
repositories. A platform-enforced prompt that cannot be removed by repository
configuration remains mandatory and must not be represented as a project
approval request.

On this macOS sandbox, direct `ssh -o BatchMode=yes` is the approved read-only
LAN transport. Git-over-SSH may still be denied because Git launches SSH as an
indirect child process. For read-only remote verification, query repository
metadata or refs through a direct SSH command on the appropriate HomeLab host;
reserve elevated `git push`/fetch operations for actual synchronization and
the remote-write approval rule below.

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
