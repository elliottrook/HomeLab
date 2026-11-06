# AsterTV v3 M7 physical equipment-control candidate — 2026-11-06

## Outcome

The repository side of physical AsterTV Remote equipment control is complete
without installing a keymap or sending an equipment command.

- An enrolled room client can submit only `volume_up`, `volume_down`,
  `mute_toggle` or `power_toggle` through its existing outbound identity.
- The gateway authenticates that exact client/room, applies the existing rate
  and replay boundaries, requires a live capability-scoped equipment bridge
  and converts toggles into explicit `mute_on/off` or `power_on/off` from fresh
  state. It never emits a blind toggle.
- The Kodi helper reads only the existing mode-`0600` room identity/key and
  can reach only the new semantic endpoint. It contains no shell, Kodi
  JSON-RPC, arbitrary Home Assistant service or volume-set path.
- The keymap renderer refuses Guest/unknown hosts, missing controls, duplicate
  inputs and Select/Back/navigation keys. It produces no keymap until an exact
  per-hardware capture record is supplied.
- Home Assistant now supports independently keyed Family and Bedroom room
  rows while preserving the accepted Family-only configuration during rolling
  upgrade. Content state is held separately per room in volatile memory.

The Bedroom contract uses the accepted LG webOS entity for power and for
volume/mute expected to traverse ARC/eARC SIMPLINK/CEC. Family retains direct
Onkyo volume/mute and state-aware TCL power.

## Validation and custody

Twelve gateway tests passed in LXC 104's pinned Aster Agent environment without
loading production secrets or restarting the service. Thirty-seven focused
Remote, keymap, Home Assistant contract and fleet materialization tests passed;
the complete V3 gate passes 72 local test files, the connected HEVC test and
all operations/page checks. All three active fleet compositions compile.

No physical key code has been guessed, no keymap has been installed, Bedroom
equipment authority remains disabled, and no Family/Bedroom equipment command
was sent. The remaining work is deliberately owner-assisted: capture the four
keys and observe one bounded command/recovery sequence in each room.
