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

## Local AI Lab Hours scheduling

Tasks must never be scheduled in a way that interferes with a protected Aster
Lab Hours window. Before creating, updating, enabling or proposing any
scheduled task, Codex automation, systemd timer or cron job that could use or
compete for the local AI stack, query the authoritative Proxmox reservation
ledger for the complete proposed execution and recovery window:

`/usr/local/sbin/aster-lab-hours check-window --start <offset-qualified-ISO-8601> --end <offset-qualified-ISO-8601>`

A conflict, unavailable ledger or uncertain result is a fail-closed scheduling
decision: do not create or activate the task. Move it outside the protected
window or create an approved booking first. Calendar time alone is never proof
that the window is clear.

Every local AI lab workload that needs exclusive use of the local AI stack must
have its own Lab Hours booking before it is scheduled or started. Bookings may
name only registered, hash-pinned workloads and may not contain arbitrary
commands. The booking is additional to the live whole-host lease and shared
operation lock; all three controls must pass. A task created before a later
booking must recheck immediately before effects and fail closed if the booking,
lease or lock boundary is no longer clear.

The operating contract and recovery procedure are in
`services/local-ai-lease/ASTER-LAB-HOURS-RESERVATION-RUNBOOK.md` and
`docs/projects/AI Projects/Aster-Lab-Hours.md`.

Forgejo `origin` is the single authoritative push target. Forgejo automatically
mirrors accepted commits to the GitHub protection remote; Codex must verify the
GitHub ref read-only after the mirror runs and must not push the same commit
directly to the `github` remote. A direct GitHub push is permitted only when the
user explicitly requests it for mirror recovery or another exceptional case.

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

## Confirmed Paperless IP correction — 2026-09-23

Jason directed that confirmation for the proposed Paperless IP-collision fix
be recorded here. This is approval for this one bounded operation:

- Move only Paperless LXC 115 from `192.168.70.14/24` to
  `192.168.70.15/24`, after rechecking that the new address is available.
  Preserve its existing MAC, VLAN, gateway and other guest settings.
- Update only the Paperless UI firewall rule
  `fdc0bfb3-9dd4-4bca-869c-a571f8d64f02` and its Homepage tile to the new
  address; reload the firewall and restart only Homepage as needed.
- Register Paperless and its new address in NetBox without changing the
  existing Aster Speech address record.
- Capture recovery checkpoints, validate UI access and network isolation,
  and record the result in the project and operational documentation.

Leave Aster Speech LXC 116 and its existing network rules unchanged. Do not
restore an active conflicting `.14` assignment as a rollback. This approval
does not authorize unrelated changes, backup deletion, Git pushes or a general
waiver of the remote-change confirmation rule. Once completed, this section
is an authorization record, not permission to repeat the operation blindly.

Completion record: the IP correction, UI rule/tile update and NetBox registration
were completed and validated on 2026-09-23. Jason subsequently approved completing
the remaining deployment, closing, committing, pushing and archiving this project.
That task-specific close-out authorization does not waive approval for unrelated
projects or future remote operations.
