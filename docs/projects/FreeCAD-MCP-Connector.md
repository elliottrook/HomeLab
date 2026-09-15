# FreeCAD MCP Connector for Local CAD Assistance

> Status: Active — Stream A
>
> Owner: Jason
>
> Proposed: 2026-09-14
>
> Started: 2026-09-14
>
> Completed: —
>
> Authorization stream: **Stream A — Autonomous**, granted by Jason
> 2026-09-14 in this project's own conversation, per the per-project
> authorization mechanism in `CLAUDE.md` and the `Project-Creation-Standard`.
> The enumerated scope: install and use `neka-nat/freecad-mcp` as a
> localhost-only bridge between FreeCAD (this Mac) and both this Claude Code
> session and the ChatGPT Desktop app (also this Mac, added 2026-09-14 —
> confirmed with Jason that this means a second **local** client on the same
> machine, not a cloud-hosted ChatGPT reaching in over the internet); design
> and print an ATX-compatible variant of the TrueNAS enclosure. This
> authorization does not extend past that scope. Per the Standard's
> non-waivable stop conditions, **any change that would expose the FreeCAD
> RPC server or the MCP bridge beyond localhost — including any form of
> ChatGPT cloud/mobile access — requires a fresh, explicit decision
> regardless of this Stream A grant**, and is not pre-authorized here.

## Purpose and desired outcome

Let Claude help design and edit 3D-printable CAD models — starting with
adapting the TrueNAS DIY SAS Expansion project's drive enclosure (currently
sized around an SFX power supply) to fit a standard ATX PSU instead — by
giving Claude a way to actually drive FreeCAD, rather than only reasoning
about dimensions from static measurements. The user-visible outcome is a
working, printable, ATX-compatible enclosure variant; the MCP connector is
the means, not the goal, and should not become a standing, unmonitored
capability without a deliberate decision to widen it.

## Current state and evidence

- FreeCAD is already installed on a separate "3D printer PC," not on this
  Mac. Jason intends to install FreeCAD on this Mac specifically so the MCP
  bridge can talk to it over localhost, rather than opening any new network
  path between machines.
- This Claude Code session has no CAD or mesh-editing tool today (confirmed
  2026-09-14: no OpenSCAD/FreeCAD/Blender/MeshLab binary on this Mac's PATH
  or in `/Applications`; no CAD-related connector in the MCP registry
  available to this account, checked both broadly and for "freecad"
  specifically).
- The source model for the enclosure (MakerWorld model 150766, "NAS Hard
  Drive Bay / Enclosure V1" by plucbernier) ships only as baked STL mesh
  files, not parametric CAD source — editing it means real mesh manipulation
  (resizing a compartment, re-checking that mating faces between the three
  printed sections still align), not just changing a few parameters.
- Researched available FreeCAD MCP server projects on GitHub (2026-09-14).
  `neka-nat/freecad-mcp` is the clear standout by maturity signals: 2.3k
  stars, 289 forks, 173 commits, MIT licensed. Architecture: a FreeCAD
  workbench addon runs an RPC server inside FreeCAD itself (started manually
  from FreeCAD's toolbar), and a separate `uvx freecad-mcp` process bridges
  that RPC server to Claude over MCP, by default over localhost only. Its own
  documentation confirms it supports running Python scripts inside FreeCAD
  (both GUI and headless), and separately documents a "remote connections"
  configuration option — meaning wider network exposure is possible but not
  the default. Several smaller, far-less-established alternatives exist
  (`Coben-3d/freecad-mcp`, `lucygoodchild/freecad-mcp-server`,
  `bonninr/freecad_mcp`, `contextform/freecad-mcp`, `puran-water/freecad-mcp`,
  `spkane/freecad-addon-robust-mcp-server`, `yuri-schmaltz/mcp_freecad`,
  `proximile/FreeCAD-MCP`) with no comparable adoption signal; none were
  reviewed further given `neka-nat/freecad-mcp`'s clear lead, but this is
  itself worth naming as a limitation — "most stars" is a popularity signal,
  not a security audit.
- No source-code review of `neka-nat/freecad-mcp` itself has been performed
  yet — only its README/documentation. This is a real gap before installing
  it: a starred, MIT-licensed project is still an unaudited third party with
  the ability to execute code locally.

## Scope and exclusions

### Included

- Installing FreeCAD on this Mac (Jason's own action — done 2026-09-14).
- Installing the `neka-nat/freecad-mcp` addon inside FreeCAD and running its
  bridge process locally, connected to this Claude Code session over
  localhost only.
- Connecting the ChatGPT Desktop app, also running on this same Mac, to the
  same local FreeCAD RPC server as a second local client — **only if ChatGPT
  Desktop's own connector support can reach a local server without any
  internet-facing relay or tunnel**. This has not yet been verified; Milestone
  1 includes checking ChatGPT Desktop's actual current connector capability
  before assuming it can be wired up this way, rather than building toward
  it as a foregone conclusion.
- Using the connector to inspect and edit the enclosure model: widening the
  PSU compartment (and any dependent joint/mating geometry) to fit a
  standard ATX PSU footprint, re-exporting printable STL files, and checking
  fit against the drive-bay sections' shared cross-section.
- Reviewing the connector's own source (not just its README) for anything
  that reaches beyond localhost, phones home, or executes beyond what
  FreeCAD's own Python environment implies, before the first real use.

### Excluded

- Any network exposure of the FreeCAD RPC server or the MCP bridge beyond
  localhost on this Mac. The connector's own "remote connections" option is
  explicitly not used in this project.
- ChatGPT's cloud/web/mobile app reaching this Mac's FreeCAD instance over
  the internet, via a tunnel, port-forward, or hosted relay. This was asked
  about and explicitly declined 2026-09-14 in favor of the local-only
  interpretation above; it remains a non-waivable stop condition under the
  Standard regardless of this project's Stream A grant, and would need its
  own fresh, separately justified decision if reconsidered later.
- Any use of this connector against files outside a dedicated scratch/CAD
  working directory until Jason decides otherwise — it should not be pointed
  at this repository's other files, credentials, or unrelated parts of the
  filesystem.
- Extending this capability to the separate 3D printer PC, or to any other
  machine, in this project. That would be a new, separate decision.
- Treating GitHub star count as a substitute for actually reading the code
  before granting it local execution ability.
- Any change to production HomeLab systems. This project touches only local
  CAD files on this Mac; it has no relationship to any lab VLAN, service, or
  credential.

## Authority model

Not applicable in the usual HomeLab sense — this project has no live system
of record. The MakerWorld model page is the authoritative source for the
original design; any modified STL becomes a new, locally-owned artifact with
no upstream authority relationship to the original designer's file.

## Architecture and data flows

```text
This Mac
  FreeCAD (GUI, installed by Jason)
    +-- neka-nat/freecad-mcp addon (workbench)
          +-- RPC server, localhost only
                |
                | (loopback, no network exposure)
                +----------------------+
                v                      v
          uvx freecad-mcp bridge   ChatGPT Desktop's own local
          process (localhost)     connector (localhost), IF its
                |                 current capability supports this —
                | MCP (local)     unverified, see Milestone 1
                v
     This Claude Code session
```

No new inbound or outbound network path is created — both AI clients reach
the same FreeCAD RPC server over loopback only, from processes running on
this same machine. No credential is involved. The trust boundary this
project introduces is: any local client able to reach that RPC server
(today: this Claude Code session; potentially: ChatGPT Desktop) gains the
ability to execute Python inside FreeCAD's environment on this Mac, which in
turn has normal user-level filesystem access — meaning the practical blast
radius of a bug or a malicious dependency in the connector is "arbitrary
local code as the logged-in user," not merely "bad CAD geometry." Adding a
second local client does not change that blast radius in kind, only in how
many local processes could reach it — the RPC server itself has no described
per-client access control, so this remains a single shared local capability
surface rather than two independently-scoped ones. That should be named
plainly rather than undersold, even though the intended use is narrow.

## Privacy and security design

- **Least privilege:** the RPC server and bridge run locally, bound to
  localhost, with no remote-connection option enabled.
- **Scope containment:** the connector is used only against a dedicated CAD
  working directory for this task, not this repository or the wider
  filesystem, until a deliberate decision says otherwise.
- **Supply-chain awareness:** before first real use, review
  `neka-nat/freecad-mcp`'s actual source (not just its README) for anything
  that phones home, reaches beyond localhost, or does more than the
  documented FreeCAD RPC bridge. This is a manual step, not automated by
  this project.
- **No credential exposure:** this project involves no lab credentials,
  tokens, or production access of any kind.
- **Public exposure:** none. Entirely local to this Mac.

## Pre-start risk assessment

- **Objective, scope, exclusions, stream:** as stated above. Stream M
  requested because this introduces a new local code-execution surface on
  the machine that also holds this repository's SSH access — the kind of
  "unusually sensitive" case the Standard reserves for Monitored approval,
  at least until its real-world behavior is well understood.
- **Affected systems, users, data, network paths, systems of record:** this
  Mac only. No lab VLAN, service, or credential is touched. Jason is the
  only user. No system of record is affected.
- **Current versions, dependencies, known consumers:** FreeCAD not yet
  installed on this Mac (Jason's action); `neka-nat/freecad-mcp` at whatever
  its current release is when installed (record the exact commit/release
  once installed); `uv`/`uvx` required as a dependency (not yet confirmed
  present on this Mac).
- **Confidentiality and secret-handling risks:** none directly — but see the
  architecture note above: local code execution capability, if the
  connector or a future update to it were malicious or compromised, could in
  principle reach this Mac's other files, including this repository's SSH
  keys. This is the project's real risk, not a formality, and is the reason
  a source review is required before first real use rather than treated as
  optional polish.
- **Availability, integrity, privacy, recovery risks:** low for the lab
  itself (nothing here touches production); the main risk is local to this
  Mac and this hobby project (a bad edit could corrupt a CAD working file,
  recoverable by keeping the original STLs untouched and working only on
  copies).
- **Irreversible or destructive operations:** none anticipated. All CAD edits
  should work on copies of the original STL files, never overwriting the
  MakerWorld-sourced originals in place.
- **Authentication, firewall, DNS, storage, external-service changes:** none.
- **Recovery checkpoint, rollback path, abort conditions:** keep the original
  three STL files (as downloaded from MakerWorld) untouched in a separate,
  clearly labeled location before any edit begins. Abort and reassess if the
  connector's source review surfaces anything reaching beyond localhost or
  executing outside FreeCAD's own document/Python scope.
- **Test strategy:** print a single test coupon (matching the existing
  project's own "one-bay/rear-depth test coupon" practice) before committing
  to a full print, exactly as the original project document already
  requires for the unmodified design.
- **Likely interruption and detection:** none beyond normal desktop-session
  interruption; nothing here runs unattended or persists across restarts
  unless Jason chooses to keep the FreeCAD RPC server running continuously,
  which is not required for this task.
- **Backup, Doctor, monitoring, NetBox, wiki/mirror, documentation impacts:**
  not applicable — see the integration checklist below.
- **Unresolved decisions requiring acceptance before work starts:** whether
  Jason wants the connector's source reviewed by Claude before first use
  (recommended), and whether the FreeCAD RPC server should be started only
  for active sessions versus left running (recommended: only when actively
  working on this, not as a standing background service).

## Persistence plan

- **Current milestone:** none started — proposed, awaiting authorization.
- **Last verified state:** not applicable; FreeCAD is not yet installed on
  this Mac.
- **Next safe action:** once Jason installs FreeCAD and confirms the Stream
  M authorization, review `neka-nat/freecad-mcp`'s source, then install the
  addon and configure the local MCP connection.
- **Rollback location:** the original three STL files from MakerWorld model
  150766, kept untouched in a clearly labeled directory separate from any
  working copy.

## Milestones

### Milestone 1 — Install and vet the connector

- [x] Confirm FreeCAD is installed on this Mac (Jason, 2026-09-14).
- [ ] Confirm `uv`/`uvx` is available on this Mac, or install it.
- [ ] Review `neka-nat/freecad-mcp`'s actual source code (not just its
      README) for anything reaching beyond localhost or beyond FreeCAD's
      documented RPC/Python scope.
- [ ] Install the FreeCAD addon and start its RPC server; confirm it is
      bound to localhost only.
- [ ] Add the MCP bridge to this Claude Code session's configuration,
      scoped to this machine.
- [ ] Check whether ChatGPT Desktop's current connector support can reach a
      local server without any internet-facing relay or tunnel. If it
      cannot do this today, ChatGPT access is deferred rather than
      implemented some other way — the internet-facing alternative was
      explicitly declined and is not an approved fallback.
- [ ] If confirmed possible: connect ChatGPT Desktop to the same local RPC
      server as a second client.
- [ ] Confirm the connection with a trivial, read-only action (e.g. opening
      a document and reading its object list) before any edit, from each
      connected client.

Gate: the connector is installed, reviewed, and proven to work read-only,
with no network exposure beyond localhost.

### Milestone 2 — Baseline the existing model

- [ ] Download and preserve the original three MakerWorld STL files
      untouched, in a clearly labeled rollback location.
- [ ] Open working copies in FreeCAD via the connector and confirm the
      measured envelopes match the original project document's table
      (Main body 1: 132 x 218.6 x 185mm; Main body 2: 132 x 82 x 185mm;
      Main body 3: 132 x 40 x 185mm).
- [ ] Confirm standard ATX PSU dimensions to design against (record the
      exact target unit, e.g. the used EVGA SuperNOVA 650 GA under
      consideration, or a generic ATX envelope if the exact unit is not yet
      decided).

Gate: the working environment reproduces the original design's known
measurements before any modification begins, so later changes are
measured against a verified baseline, not assumption.

### Milestone 3 — Adapt the PSU compartment

- [ ] Widen the shared cross-section (currently 132mm width x 185mm height)
      as needed to fit the target ATX PSU, or scope a narrower fix if a
      width-only change to the PSU compartment section can avoid touching
      the drive-bay sections' shared profile.
- [ ] Extend the PSU compartment's length along the stacking axis to fit the
      ATX unit's depth, re-checking the joint with the adjacent end/base
      section.
- [ ] Adjust the PSU mounting screw pattern for a standard ATX rear-panel
      bracket.
- [ ] Re-verify the drive-bay sections' geometry is unaffected by any
      cross-section change.
- [ ] Export updated STL files for a test print.

Gate: a modified model exists, dimensionally verified against the target
ATX PSU's real envelope, with the drive-bay sections' geometry unchanged.

### Milestone 4 — Print and fit validation

- [ ] Print a rear-depth/PSU-bay test coupon before a full print, matching
      the original project's own practice.
- [ ] Verify the target ATX PSU fits without force, its mounting screws
      align, and its rear panel connectors and airflow are unobstructed.
- [ ] Confirm the modified PSU compartment still joins cleanly with the
      unmodified drive-bay sections.

Gate: the physical test print confirms fit before committing to a full
print of the modified enclosure.

## Validation and evaluation

- Functional: the connector performs read-only inspection correctly before
  any edit is attempted.
- Least-privilege / denied-action: confirm the RPC server refuses
  connections from anything other than localhost.
- Malformed, missing, stale, adversarial inputs: not applicable at this
  scale — this is a local hobby CAD task, not a production service.
- Restart/interrupted-run behavior: FreeCAD documents are saved incrementally
  as working copies; an interrupted session should not corrupt the
  preserved original STL files.
- Rollback to prior accepted state: the original STL files remain untouched
  and are the rollback target at every stage.
- Secret-pattern review: not applicable — no secrets are involved anywhere
  in this project.
- Performance/capacity: not applicable.

## Observability and maintenance

Not applicable in the HomeLab Doctor/monitoring sense — this is a local,
on-demand hobby tool, not a running service. If Jason later decides to keep
the FreeCAD RPC server running persistently, that would be a new, separate
decision revisiting this project's "only when actively working on this"
scope.

## Backup, restore and rollback

- **Protected components:** the original three MakerWorld STL files.
- **Retention:** kept indefinitely, untouched, separate from any working
  copy.
- **Isolated restore proof:** not applicable beyond keeping the originals
  untouched — there is no production system to restore.
- **Last-known-good path:** the original, unmodified STL files always serve
  this role.

## Documentation and systems-of-record updates

- [ ] **HomeLab Doctor:** not applicable — no lab service is created.
- [ ] **Monitoring/alerting:** not applicable.
- [ ] **Backup and recovery:** not applicable — no production data.
- [ ] **NetBox:** not applicable — no new device, VM, or service.
- [ ] **Human wiki:** not applicable.
- [ ] **Aster mirror/snapshot:** not applicable.
- [ ] **Operational reference/runbooks:** not applicable.
- [ ] **Repository documentation:** update
      `docs/projects/TrueNAS-DIY-SAS-Expansion.md` with the resulting
      ATX-compatible enclosure variant once it exists, and cross-reference
      this project from it.
- [ ] **Diagrams/rack records:** not applicable.
- [ ] **Homepage/service discovery:** not applicable.
- [ ] **Authentication/authorization:** not applicable — no lab identity or
      credential is touched.
- [ ] **DNS, certificates and firewall:** not applicable.
- [ ] **Automation and schedules:** not applicable — no unattended or
      scheduled execution.
- [ ] **Security inventory:** record that a new local, code-execution-capable
      third-party tool exists on this Mac once installed, including its
      exact source (`neka-nat/freecad-mcp`), version/commit, and the fact
      that it is scoped to localhost only.

## Graduation criteria

This project graduates when a printable, dimensionally-verified,
ATX-compatible variant of the enclosure exists; the connector has been
reviewed and proven localhost-only; the original design files remain
untouched and recoverable; and the outcome is recorded back into the
TrueNAS DIY SAS Expansion project document.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-14 | Proposal | Confirmed no CAD tool or connector exists in this session today; researched available FreeCAD MCP server projects and identified `neka-nat/freecad-mcp` (2.3k stars, 289 forks, 173 commits, MIT) as the clear adoption leader among several much smaller alternatives; confirmed its architecture is localhost-only by default with an optional, unused "remote connections" mode, and that it supports running Python scripts inside FreeCAD | Proposed as Stream M given the new local code-execution trust boundary this introduces on the same machine holding this repository's SSH access; no software installed, no MCP connection configured yet |
| 2026-09-14 | Authorization and scope revision | Jason installed FreeCAD on this Mac; granted Stream A for this project's enumerated scope; asked to add ChatGPT access to the same FreeCAD instance. Asked Jason to clarify since a cloud-reachable ChatGPT would be a materially different, internet-facing architecture — a non-waivable stop condition regardless of Stream A. Jason confirmed the local-only interpretation: ChatGPT Desktop, on this same Mac, as a second local client of the same localhost-only RPC server, not cloud/mobile ChatGPT reaching in over the internet | Scope and architecture revised accordingly; the cloud/mobile interpretation is explicitly recorded as excluded and non-waivable. No software installed yet beyond FreeCAD itself; Milestone 1's source review and addon installation have not started |

## Close-out

To be completed at graduation. Will record: the final connector version/
commit used, confirmation it remained localhost-only throughout, the
resulting ATX-compatible enclosure design and its relationship to the
original MakerWorld model, and whether the connector was removed after use
or retained for future CAD work.
