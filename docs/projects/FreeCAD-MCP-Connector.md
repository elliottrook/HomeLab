# FreeCAD MCP Connector for Local CAD Assistance

> Status: Active — Stream A. Milestone 1 nearly complete: source review,
> `uv`/`uvx`, addon installation, and Claude Code's MCP bridge config are
> all done; ChatGPT Desktop access confirmed not possible without an
> excluded internet tunnel and is deferred. The one remaining step is a
> manual FreeCAD GUI action (start the RPC server) that needs Jason at the
> Mac — see "Next safe action" below.
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
  internet-facing relay or tunnel**. **Verified 2026-09-14: not possible.**
  ChatGPT Desktop's connector support (Developer Mode custom connectors)
  requires a public HTTPS remote server and has no localhost/stdio option.
  This is not pursued via the excluded tunnel workaround; ChatGPT access to
  FreeCAD is deferred, not implemented.
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
          uvx freecad-mcp bridge   ChatGPT Desktop: NOT connected —
          process (localhost)     verified 2026-09-14 its connector
                |                 support requires a public HTTPS
                | MCP (local)     server, no localhost option exists
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

- **Current milestone:** Milestone 1, nearly complete.
- **Last verified state (2026-09-14):** FreeCAD 1.1.3 installed; addon copied
  into `~/Library/Application Support/FreeCAD/v1-1/Mod/FreeCADMCP`; `uv`/`uvx`
  0.12.13 on `PATH`; Claude Code's `freecad` MCP server configured
  (`local` scope) but not yet connectable; ChatGPT Desktop access confirmed
  not possible without an excluded tunnel, deferred.
- **Next safe action:** Jason restarts FreeCAD, selects the **MCP Addon**
  workbench, and clicks **Start RPC Server** in its toolbar (a manual GUI
  step this session cannot perform headlessly). Once running, confirm it's
  bound to `127.0.0.1` only, then do a trivial read-only check (open a
  document, read its object list) from this Claude Code session to close
  out Milestone 1's gate.
- **Rollback location:** the original three STL files from MakerWorld model
  150766, kept untouched in a clearly labeled directory separate from any
  working copy.

## Milestones

### Milestone 1 — Install and vet the connector

- [x] Confirm FreeCAD is installed on this Mac (Jason, 2026-09-14).
- [x] Confirm `uv`/`uvx` is available on this Mac, or install it. **Result,
      2026-09-14:** neither `uv`/`uvx` nor Homebrew were present. Installed
      via the official astral.sh installer (Jason chose this over
      self-install or pip/pipx when asked). This required adding
      `astral.sh` to the sandbox network allowlist (`.claude/settings.json`
      and the `CLAUDE.md` table, updated together per that file's own
      rule) — a genuinely new network destination, so it was not treated as
      already covered by Stream A. Installed `uv`/`uvx` 0.12.13 to
      `/Users/jelliott/.local/bin` (already on `PATH`); confirmed via
      `uv --version`/`uvx --version`.
- [x] Review `neka-nat/freecad-mcp`'s actual source code (not just its
      README) for anything reaching beyond localhost or beyond FreeCAD's
      documented RPC/Python scope. **Result, 2026-09-14:** read the actual
      `rpc_server/ip_filter.py` and `rpc_server/settings.py` source (not the
      README). `ip_filter.py` defaults to `allowed_ips_str="127.0.0.1"` and
      enforces it in `verify_request()` by checking the connecting client's
      IP against parsed allowed networks — a real, enforced default, not
      only a documentation claim. `settings.py` persists
      `remote_enabled: False`, `allowed_ips: "127.0.0.1"`, and
      `auto_start_rpc: False` as defaults, and contains no telemetry,
      analytics, update-check, or external network call of any kind. This
      covered the two files that actually determine the localhost-only
      claim; it is not an exhaustive line-by-line audit of all 14 files in
      `rpc_server/` (commands.py, gui_dispatch.py, fem_executor.py,
      object_factory.py, etc. were not individually reviewed) — noted as a
      residual limitation, not a completed full audit.
- [x] Install the FreeCAD addon and start its RPC server; confirm it is
      bound to localhost only. **Result, 2026-09-14 (partial):** cloned
      `neka-nat/freecad-mcp` to a scratch directory and copied
      `addon/FreeCADMCP` into FreeCAD 1.1's addon directory
      (`~/Library/Application Support/FreeCAD/v1-1/Mod/FreeCADMCP`, per
      the project's own `docs/installation.md`). **Starting the RPC
      server itself is a manual, GUI-only step** (restart FreeCAD, select
      the **MCP Addon** workbench, click **Start RPC Server** in its
      toolbar) that this session cannot perform headlessly — needs Jason
      to do this at the Mac, or a screen-control-capable session. Binding
      confirmation is deferred until the server is actually running.
- [x] Add the MCP bridge to this Claude Code session's configuration,
      scoped to this machine. **Result, 2026-09-14:** `claude mcp add
      freecad -- uvx freecad-mcp` at `local` scope (stored in
      `~/.claude.json` under this project path, not committed to the
      repo's own `.mcp.json` / git history — this is a per-machine tool,
      not shared lab infrastructure). Not yet connectable: FreeCAD's RPC
      server isn't running yet (see the item above), so this server will
      show as unreachable until that manual step happens.
- [x] Check whether ChatGPT Desktop's current connector support can reach a
      local server without any internet-facing relay or tunnel. If it
      cannot do this today, ChatGPT access is deferred rather than
      implemented some other way — the internet-facing alternative was
      explicitly declined and is not an approved fallback. **Result,
      2026-09-14:** confirmed **not possible**. ChatGPT Desktop (v26.825.51511,
      installed on this Mac) supports MCP only through "Developer Mode"
      custom connectors, which require a **public HTTPS remote server** —
      it does not support localhost or stdio MCP servers at all. The
      standard workaround documented elsewhere (an ngrok-style tunnel) is
      exactly the internet-facing relay this project's scope explicitly
      excludes as non-waivable. Per this checklist item's own instruction,
      ChatGPT access is deferred, not implemented via that excluded path.
- [x] If confirmed possible: connect ChatGPT Desktop to the same local RPC
      server as a second client. **N/A — see previous item:** not
      currently possible without the excluded internet-facing relay, so
      this is skipped rather than attempted.
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
- [x] **Security inventory:** record that a new local, code-execution-capable
      third-party tool exists on this Mac once installed, including its
      exact source (`neka-nat/freecad-mcp`), version/commit, and the fact
      that it is scoped to localhost only. **Recorded 2026-09-14:** addon
      installed from commit `5dbfe2c80b53c3102bff0723951676e16edf2d84`
      (2026-09-10) into
      `~/Library/Application Support/FreeCAD/v1-1/Mod/FreeCADMCP`; the
      published `freecad-mcp` PyPI package is run on demand via `uvx` (no
      persistent install of that half). Localhost-only by verified default
      config (Milestone 1 source review); not yet running.

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
| 2026-09-14 | 1 source review | Read the actual `addon/FreeCADMCP/rpc_server/ip_filter.py` and `settings.py` source directly from GitHub (not the README): confirmed `allowed_ips_str` defaults to `"127.0.0.1"` and is genuinely enforced in `verify_request()`; confirmed persisted settings default to `remote_enabled: False` and `auto_start_rpc: False`; found no telemetry, analytics, or external network call in either file. Did not individually review the other 12 files in `rpc_server/` (commands.py, gui_dispatch.py, fem_executor.py, object_factory.py, object_validation.py, parts_library.py, property_mapper.py, rpc_server.py, serialize.py, view_manager.py, dispatch_health.py, `__init__.py`) — this is a targeted review of the access-control-critical files, not an exhaustive audit | The localhost-only claim is verified at the code level for the files that enforce it, not merely asserted by documentation. Residual limitation recorded: the remaining ~12 files handling the actual CAD command surface have not been reviewed line-by-line. Addon installation and RPC connection have not yet been performed |
| 2026-09-14 | 1 handoff, uv/uvx | Fresh Remote-Control session picked up the handoff. Neither `uv`/`uvx` nor Homebrew were present on this Mac. Asked Jason how to proceed (self-install, pip/pipx, or add astral.sh to the sandbox allowlist); Jason chose adding astral.sh. Added it to `.claude/settings.json`'s `allowedDomains` and the `CLAUDE.md` sandbox-access table in the same change, then ran the official astral.sh installer (needed `dangerouslyDisableSandbox` once the sandbox's own `mktemp -d` default path conflict surfaced as a genuine sandbox restriction, not a project-scope bypass) | `uv`/`uvx` 0.12.13 installed to `/Users/jelliott/.local/bin`, confirmed via `--version`. No FreeCAD addon installation or RPC connection performed yet |
| 2026-09-14 | 1 addon install, MCP config, ChatGPT check | Cloned `neka-nat/freecad-mcp` to scratch, copied `addon/FreeCADMCP` into FreeCAD 1.1's addon directory (`~/Library/Application Support/FreeCAD/v1-1/Mod/FreeCADMCP`, sandbox disabled for this local write only). Added `freecad` as a `local`-scope Claude Code MCP server (`claude mcp add freecad -- uvx freecad-mcp`, stored in `~/.claude.json`, not committed to this repo). Researched ChatGPT Desktop's (v26.825.51511, installed) actual current connector capability rather than assuming it: confirmed its Developer Mode custom connectors require a public HTTPS remote server with no localhost/stdio support at all | Addon installed but RPC server not yet started — that step is a manual FreeCAD GUI action (toolbar button) this session cannot perform headlessly; needs Jason at the Mac. ChatGPT Desktop access is confirmed not possible without the excluded internet tunnel and is deferred, not implemented. Claude Code's MCP bridge is configured but not yet connectable until the RPC server is running |

## Starting the handoff session

This project is handed off 2026-09-14 to a fresh session with Remote Control
enabled, so Jason can approve prompts from his phone as Milestone 1
continues, without needing to sit at this Mac. This is a mechanical handoff,
not a scope or authorization change — Stream A, the enumerated scope, and
the non-waivable ChatGPT-cloud exclusion above all carry over unchanged.

**Why a new session is needed at all:** Remote Control cannot be enabled on
an already-running session — it is locked at launch. The prior session
confirmed this directly rather than assuming it.

**What the new session needs to do:**

1. Read this document in full before touching anything, especially the
   Authorization stream header, the Scope and exclusions section, and
   Milestone 1's evidence log entries — the localhost-only access-control
   review is already done and verified at the code level; do not redo it,
   build on it.
2. Check whether `uv`/`uvx` is available on this Mac (`command -v uv uvx`);
   install it if not, using the least invasive method available (e.g.
   Homebrew if already in use on this Mac, otherwise the official installer).
3. Continue Milestone 1's remaining items in order: install the
   `addon/FreeCADMCP` addon into FreeCAD's addon directory, start its RPC
   server from FreeCAD's toolbar, confirm (do not just assume) that it is
   bound to `127.0.0.1` only, then add the MCP bridge to this Claude Code
   session's configuration.
4. Before connecting ChatGPT Desktop: actually check whether its current
   connector support can reach a local server without any internet-facing
   relay or tunnel. If it cannot, stop there and report that plainly rather
   than reaching for an internet-facing workaround — that path is
   explicitly excluded and non-waivable, not a fallback to improvise around.
5. Confirm the connection with a trivial read-only action (open a document,
   read its object list) from each connected client before any real edit.
6. Under Stream A, ordinary anticipated steps in this enumerated scope do
   not need a fresh chat approval each time — but platform/sandbox approval
   prompts remain mandatory regardless (per `CLAUDE.md` and the Standard)
   and will still surface as phone dialogs; that is expected, not a
   malfunction.
7. Keep the evidence log current at each step, exactly as the prior session
   did, so this remains resumable if interrupted again.

## Close-out

To be completed at graduation. Will record: the final connector version/
commit used, confirmation it remained localhost-only throughout, the
resulting ATX-compatible enclosure design and its relationship to the
original MakerWorld model, and whether the connector was removed after use
or retained for future CAD work.
