---
name: home-assistant-manager
description: "Diagnose Home Assistant issues and propose safe next steps."
version: 0.1.0
author: Jason Elliott, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [HomeAssistant, Hue, Lutron, Aqara, HomeKit]
    related_skills: [hermes-agent-skill-authoring]
---

# Home Assistant Manager Skill

Use Aster as the source-aware advisor for Home Assistant questions covering
the Philips Hue, Lutron Caséta and Aqara M3 (Matter) integrations, the
HomeKit Bridge presentation layer, and household automations. This skill
guides diagnosis and a reviewable proposal; it does not hold a Home
Assistant token, call the Home Assistant API, control a device, run a
scene or script, or trigger an automation.

## When to Use

- Questions about how Home Assistant, its integrations (Hue, Lutron, Aqara)
  and HomeKit Bridge relate.
- Diagnosing a reported device, automation or integration problem from
  operator-provided, sanitized evidence.
- Preparing a change proposal for an automation, script, scene or
  integration setting.

Do not use it to retrieve a long-lived access token, control a device
directly, or make an unapproved Home Assistant change.

## Procedure

1. Classify the request as a knowledge question, a bounded diagnosis, or a
   requested change. Completion: state which class applies before advising.
2. For knowledge questions, ask Aster and retain its cited source, authority
   and review date. Completion: distinguish current operational evidence
   from project history or derived memory.
3. For diagnosis, use only a sanitized report or facts the operator
   supplied. Completion: name missing or stale evidence; do not request a
   token, entity_id, room/area name, or arbitrary API call.
4. For a requested change, produce a proposal with scope, expected outcome,
   validation, rollback and exact approval needed. Completion: no action is
   executed or implied.
5. Stop on conflicts, missing evidence, private-household details (who is
   home, room-level occupancy, individual device names), credentials, or
   any control/arm/disarm/setpoint/automation mutation. Completion: explain
   the boundary and ask for the appropriate reviewed procedure or explicit
   approval.

## Known operating rules

- Home Assistant is the sole automation authority; vendor apps (Hue,
  Lutron, Aqara) remain responsible for firmware, recovery and unsupported
  features. Do not propose rebuilding a vendor-owned safety automation.
- Aqara's six water sensors, shutoff valve and lock are visible through
  Matter but Aqara itself still owns their safety behavior. Any proposal
  touching water/shutoff/lock entities needs explicit heightened review;
  never propose auto-approving one.
- HomeKit Bridge publishes only `light`, `switch`, `lock`, `climate`,
  `cover`, `fan`, `vacuum`, `scene`, `script` and `binary_sensor`; media
  players, cameras, general sensors, automations, buttons and helpers are
  deliberately excluded there to prevent duplication and clutter. Do not
  assume an entity is HomeKit-controllable outside that list.
- A successful integration pairing is not proof an automation behaves
  correctly. Diagnose the complete path: trigger, condition, action,
  script/scene, and the entity's resulting state.
- Aster's current live capability is read-only, aggregate-only. A
  per-domain entity count is not proof a specific device is on or off, and
  never carries an entity_id, friendly name or room/area.
- Broad Home Assistant long-lived access tokens are not a suitable
  shortcut for a future read-only integration; least-privilege is the
  goal, not convenience.

## Verification

- Every answer cites an approved source or labels the state unknown.
- Every proposal identifies its approval boundary and does not invoke a
  tool.
- No response reveals a token, a room/area name, an individual's presence,
  or a live service configuration location.
