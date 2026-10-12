# M1 Green-only connected-role admission assessment — 2026-10-11

**Status: analysis only; no grant, account, tool connection or gate amendment.**
The existing Stage2 and connected-Codex holds remain in force.

## Question

Could the first fixed read-only Codex diagnostic use a Green AI-PAM capability
without waiting for an independent Companion approval ingress? This tests
whether the proposed separate approval service is a real dependency or an
unnecessary addition for a narrower role.

## Evidence classes

**Verified repository behavior:** `BrokerStore.create_request` marks Green
requests approved when an already registered agent has the exact enabled
capability, is in an eligible state and global policy permits it. The main
broker derives agent identity from Unix peer credentials; it does not accept a
caller-supplied agent ID. `consume_request` rechecks caller and policy. The
separate human approval socket is used for Yellow/Red decisions, not the Green
creation path. A Green grant is still an authority change and requires its
own reviewed enrolment, bounded tool and audit evidence.

**Verified live metadata:** a read-only `capabilities.list` query as the
existing `hlabagent` on LXC 104 showed `lab.doctor.latest` as Green, but also
listed Yellow and Red capabilities for that same identity. No request was
created or consumed. This does **not** make `hlabagent` a safe general Codex
worker. The current approval socket still accepts the Aster UID and Aster is
still in its approver group; the separate-ingress candidate is uninstalled.

**Architectural inference:** a *new*, distinct Unix worker with one exact
Green, fixed-target, read-only capability and no approval-socket access could
theoretically perform a bounded diagnostic without using Companion's Yellow/
Red approval route. That does not repair the existing Aster-as-approver trust
flaw, prove prompt-injection resistance, or imply that any current agent's
capabilities are appropriately scoped for Codex. `lab.doctor.latest` itself
must be reviewed for its actual output projection and model-visible privacy
before being delegated.

## Decision and possible gate amendment

Do **not** reuse `hlabagent`, grant a generic shell, or promote connected
Codex tools from this source-level observation. The current Stream A delivery
map makes M1 Stage2 an explicit prerequisite. If a future owner review wants a
Green-only exception, amend that gate deliberately and only for one named
diagnostic capability. Before activation, require:

1. a dedicated worker UID with no inherited groups, credentials or other
   capability grants; prove kernel peer binding and approval-socket denial;
2. an exact fixed-target read-only adapter whose output is bounded, fresh,
   source-labelled and sanitized before any model context or cloud egress;
3. live policy snapshot showing only the named Green grant, with revocation,
   global disable, wrong-caller, changed-policy and replay tests;
4. an explicit decision about the residual Aster approval-socket flaw and a
   rule that no Yellow/Red request can be initiated or approved through the
   Codex path; and
5. a finite observation window, independent postchecks, audit and a tested
   revoke/stop path.

No source or live evidence yet establishes all five. Until a reviewed
amendment exists, Stage2 and connected Codex tools remain HOLD. The separate
approval ingress may be deferred on value grounds without declaring the
authority problem solved.
