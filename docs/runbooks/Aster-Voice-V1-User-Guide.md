# Aster Voice V1 user guide

> Status: graduation candidate; Home Assistant and browser voice accepted, native Mac streaming and final News/web listening passes remain
>
> Voice identity: Kokoro `bm_daniel`, British English, speed 0.95, policy v1
>
> Reviewed: 2026-10-12

## Where to use Aster

- **Web and phone:** open `https://aster.elliottrook.com/` and use the existing
  passkey sign-in. `/companion` is the same application through a compatibility
  address. Tap the orb once to listen and again to finish.
- **Home Assistant:** select the existing Aster Pilot/voice workflow. Device and
  entity permissions are still Home Assistant's; changing the voice does not
  grant Aster additional control.
- **News briefing:** the scheduled briefing uses the same approved voice and
  pronunciation policy through its isolated batch renderer.
- **Mac app:** the application is usable for chat, but its installed build still
  uses the retained v1 speech route. Use the web application when canonical V1
  voice identity is required until the native streaming build is accepted.

The approved voice should sound like the accepted `bm_daniel` samples: British,
measured, and consistent across short replies and longer narration. Pronunciation
rules cover household terms including Home Assistant, Lutron Caseta, BC/British
Columbia, Canadian dollars, David Eby and Jason's room.

## During a voice turn

The interface distinguishes listening, transcribing/thinking and speaking. A
typed turn stays silent. If the browser blocks automatic sound, use the visible
Play control. **Stop speech** cancels the remaining spoken units. Keep the phone
page in the foreground during a turn.

Home Assistant's browser Assist may continue listening after its reply and can
mistake clear television or radio dialogue for a new turn. Close the dialog when
finished; future satellite/wake-word rollout must bound that follow-up window.

## If something fails

- Voice unavailable but text works: continue by typing and report which surface
  failed. Do not repeatedly submit the same device command.
- `Error playing audio`: retry once after confirming browser autoplay is allowed
  for the exact site. Home Assistant Safari requires **Allow All Auto-Play**.
- Wrong or old voice: stop the turn and report the surface. For web Aster this is
  evidence of a legacy `/voice/v1/tts` path, not merely a subjective voice change.
- No network or service: normal physical controls and Home Assistant's direct
  recovery path remain available. Aster is not a dependency for emergency access.

Routine microphone audio and transcripts are processed for the current request
and are not retained for diagnostics. Operational telemetry contains bounded
timing, size, queue and error categories, not spoken text or recordings.

## Final acceptance walkthrough

Before V1 production graduation, complete and confirm:

1. A second web/phone spoken turn with the approved voice, responsive playback
   and working Stop speech.
2. One regenerated full News briefing, checking the opening, BC/British Columbia,
   Canadian-dollar wording, David Eby and overall long-form cadence.
3. After the native app is rebuilt from the AVS1 source, two Mac spoken turns,
   including interruption/cancellation.
4. Confirm typed web/Mac chat still works and stays silent.

The operator health, rollback, backup and recovery procedures are in
[Aster Companion operator guide](Aster-Companion.md) and
[Aster operations](../reference/Aster-Operations.md).
