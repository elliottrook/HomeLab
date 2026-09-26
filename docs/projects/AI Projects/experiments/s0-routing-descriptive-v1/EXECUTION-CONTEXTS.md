# Existing execution-context comparison — read-only inventory

Status: **no existing context is yet verified suitable for a corpus run**.
Inspection2026-09-26. This is a comparison for technical review, not execution
approval. No guest, container, transient unit or isolated worker was created,
started, stopped or reconfigured. No accepted corpus was accessed.

## Evidence provenance

Standalone direct SSH `BatchMode=yes` queries to the established Proxmox host
returned `pct list`, `qm list`, and bounded `pct exec` metadata reads on100/104.
Queries inspected Python/tool availability, systemd version, Docker version/cgroup/
security-option fields, running names/images and available image names only.
No environments, credentials, application configs, private data or secret stores
were read. These are administrative observation commands, not workload deployment.
`execution-context-inventory.json` records the selected non-secret results.

Repo references: `docs/01-Architecture.md` identifies100 as shared Docker host,
104 as Aster API/UI,105 as stopped legacy inference rollback guest. Current lists
corroborate running100/104 and stopped105. The existing broker project documents
104 as credential/access integration. No unused dedicated test guest appeared in
the queried node's inventory; other nodes/devices remain UNKNOWN, not absent.

## Comparison

| Existing context | VERIFIED | UNKNOWN/BLOCKED | Disposition |
|---|---|---|---|
| Current Mac Codex sandbox | Existing Python3.12.14; supervisor primitives tested | Nested sandbox_apply denied; OS read/network/process restrictions unavailable here | NO-GO for corpus run; retain design/test work here |
| Same Mac, another execution context | Physical/runtime already exists | No separately permitted launcher context established or tested | Possible first fixture-only feasibility option if explicitly authorized; no sandbox bypass implied |
| LXC100, native Python/systemd | Python3.13.5, systemd257, unshare/timeout present; running shared application guest | Namespace/seccomp/cgroup delegation enforcement under LXC untested; no restricted worker identity/root; production blast radius | Most plausible existing-runtime fixture candidate; conditional only, not approved or preferred over isolation safety |
| LXC100, Docker | Docker29.8.1, cgroupv2; daemon reports builtin seccomp and cgroupns; application images available | No purpose-built minimal Python test image observed; controls untested; daemon privileged path and shared kernel/services | Do not repurpose application containers or mount daemon socket into worker; not the minimal first choice |
| LXC104 | Python3.13.5, systemd257, unshare/timeout; no bwrap/Docker on PATH | Hosts Aster/broker; shares authority/credential integration surface | Reject placement for this experiment despite convenient Python |
| VM105 | Stopped; repository calls it inference rollback guest | Starting changes recovery posture/resources; no isolation/runtime inspection inside it | Reject reuse as a disposable lab; do not start |
| Other running guests | Inventory includes identity, proxy, Forgejo, observability, inference, NetBox, backup, wiki, news, Paperless, speech, OpenBao; VMs102/103 running | No dedicated test role verified; dependencies potentially critical | Do not choose by spare-looking name; no workload mutation |

A Docker binary, systemd feature string or unshare path is capability inventory,
not proof that nested confinement works. LXC100 currently runs Pi-hole and other
household/admin applications; it is not an empty sandbox. No cache image was
executed to discover Python. No image pull or new package is proposed now.

## Primary documentation versus host proof

Upstream systemd257 documents namespace/filesystem restrictions, syscall filtering
and address-family controls. Their availability depends on execution context and
kernel support; documentation does not prove enforcement in these guests. Private
networking is not by itself a complete deny of local IPC or reads. Candidate worker
policy must test each prohibited network/process/file operation explicitly.
Source: [systemd257 execution manual source](https://raw.githubusercontent.com/systemd/systemd/v257/man/systemd.exec.xml).

The version-matched resource-control manual describes cgroup memory/task limits.
A cgroup memory ceiling is not the same metric as process RSS; if adopted, request
an explicit budget definition/change rather than claiming an exact RSS bound. Task
limits also do not replace syscall/process-creation restrictions.
Source: [systemd257 resource manual source](https://raw.githubusercontent.com/systemd/systemd/v257/man/systemd.resource-control.xml).

The rendered versioned freedesktop pages returned403; official tagged repository
manual sources were retrieved instead. No vendor performance claim is used.

## Recommendation and smallest next scope

**Do not run the corpus anywhere yet. Do not add hardware or dependencies.**
Recommend designing a fixture-only LXC100 feasibility probe as the least additional
runtime path, conditional on explicit shared-host risk acceptance and technical
review. This recommendation is an architectural inference, not authorization.
It needs a concrete temporary identity/filesystem/network/syscall/cgroup scope,
parent wall supervision, bounded output, exact cleanup, service-health baselines
and stop conditions. No Docker access in the worker. If any boundary needs weaker
LXC settings, extra nesting privilege, firewall changes, shared-service disruption
or persistent installation, reject this option and report the new scope.

Before such a probe: determine read-only whether existing cgroup delegation and
namespace support can satisfy the design, then prepare exact commands/configuration
for review. Capability probes that start transient units or namespaces are state
changes and have not been authorized by this read-only inventory. Do not sneak
those into a version check. Confirm Pi-hole and other100 workloads are not affected
by any proposed limits; apply limits only to the exact new disposable scope.

Alternative: a separately permitted local Mac fixture execution context, if one
can be established without bypassing platform controls. Do not assume that moving
commands to a Terminal window makes a denied action authorized. A dedicated existing
non-production Linux environment could be superior, but none is verified in this
inventory; ask about one only if the above bounded alternatives cannot be made safe.

Neither option authorizes actual evaluation. Full launch readiness still requires
externally frozen pins, immutable inputs, proven denied operations, hard timeout,
memory containment, exclusive run IDs, bounded atomic output and recovery evidence,
then one exact human-approved corpus run. Current live gate stays disabled.

## Rollback and publication

Read-only queries need no infrastructure rollback; no live modifications occurred.
This draft is local documentation only and awaits technical review. No commit or
push of this inventory before that review. Previous readiness milestone is c85511e.
